#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
# Copyright 2025 Robert F. Brost
# --------------------------------------------------------------------------------------
# Utility to convert a Mac alias file to a URL
# --------------------------------------------------------------------------------------

# Last: Modified 10/27/26  07:19:19 RFB iMac5K - report a broken alias to a missing file or folder
# Last: Modified 10/27/26  05:58:46 RFB iMac5K - version 1.3.0
# Last: Modified 10/27/26  05:57:18 RFB iMac5K - normal output is the path alone
# Last: Modified 10/27/26  05:55:15 RFB iMac5K - -t sets TestMode so color codes are removed
# Last: Modified 10/27/26  05:19:30 RFB iMac5K - test mode prints without color codes
# Last: Created  08/17/25  04:21:51 RFB - Created
# --------------------------------------------------------------------------------------

"""
This Utility to convert a Mac alias file to a URL.  It is borrowed from
Larry Yaeger, 20 Feb 2018.
"""


from __future__ import annotations
import time
import os
import sys
import grp
import string
import argparse
#from argparse import ArgumentParser
import struct
import re
from Foundation import NSURL
from typing import NamedTuple
from colors import c
from mac_alias import Alias
from mac_alias import Bookmark
from mac_alias import ALIAS_KIND_FOLDER
from mac_alias import kBookmarkPath, kBookmarkVolumePath, kBookmarkFileProperties
from mac_alias.bookmark import kCFURLResourceIsDirectory
from elevate import elevate

#----------------------------------------------------------------------------------------
#   Class Args
#----------------------------------------------------------------------------------------

class Args(NamedTuple):
    verbose: int
    quiet: bool
    testMode: bool
    user: str
    group: str
    superuser: bool
    aliasName: str

#----------------------------------------------------------------------------------------
#   Constants
#----------------------------------------------------------------------------------------

#----------------------------------------------------------------------------------------
#   Globals
#----------------------------------------------------------------------------------------

lastUpdate: str = c.MAG+"10/27/26  07:19:19"+c.EDC
myVersion: str = c.CYN+"1.4.0"+c.EDC
progName: str = c.BBLK+"alias2file.py"+c.BOFF

# localtime looks like "Sat May  2 20:08:04 2020"
localtime1: str = time.asctime( time.localtime(time.time()) )
localtime: str = c.BLU+'('+localtime1+')'+c.EDC

# the argparse() parser strips off the leading and trailing linefeeds!
versionDesc: str ="\n"+progName+" "+lastUpdate+" "+myVersion+" "+localtime+"\n"

verbosity: int = 0   # Anything greater than zero outputs debug messages
TestMode: bool = False
# CSI color sequences, including ESC [ m and ESC [ 1;31 m.
_colorCode = re.compile(r"\x1b\[[0-9;]*m")
bootVolume: str = os.environ["BOOTVOL"]
homeVolume: str = os.environ["HOMEVOL"]
uName: str = os.getlogin()
gName: str = grp.getgrgid(os.getegid()).gr_name
aliasName: str = ""

#----------------------------------------------------------------------------------------
#   bookmarkTarget() - POSIX path stored in a bookmark
#----------------------------------------------------------------------------------------

def bookmarkTarget(bookmark: Bookmark) -> str:
    """
    POSIX path stored in a bookmark.

    Bookmark.for_file() stores path components relative to the volume.
    A Finder alias stores them from the filesystem root, and also stores
    the volume mount in kBookmarkVolumePath. Prepending that mount then
    repeats the volume. That is what a folder on the home disk produced.
    """
    names = bookmark[kBookmarkPath]
    volume = bookmark[kBookmarkVolumePath]

    if isinstance(volume, (list, tuple)):
        parts = [part for part in volume if part not in ("", os.sep)]
        volume = os.path.join(os.sep, *parts) if parts else os.sep
    if not isinstance(volume, str) or volume == "":
        volume = os.sep

    if isinstance(names, str):
        names = [names]
    elif not isinstance(names, (list, tuple)):
        names = []
    names = [part for part in names if part not in ("", os.sep)]

    on_volume: str = os.path.join(volume, *names) if names else volume
    from_root: str = os.path.join(os.sep, *names) if names else os.sep
    if os.path.exists(on_volume):
        return on_volume
    if os.path.exists(from_root):
        return from_root

    vol_parts = [part for part in volume.split(os.sep) if part]
    if names[:len(vol_parts)] == vol_parts:
        return from_root
    return on_volume

#----------------------------------------------------------------------------------------
#   isClassicAlias() - true when the bytes are an older Alias record
#----------------------------------------------------------------------------------------

def isClassicAlias(data: bytes) -> bool:
    """
    A classic Alias record is big-endian, at least 150 bytes, version 2 or 3.
    """
    if len(data) < 150:
        return False
    _appinfo, recsize, version = struct.unpack_from(">4shh", data, 0)
    return recsize >= 150 and version in (2, 3) and len(data) >= recsize

def pointsAtFolder(bookmark: Bookmark = None, classic: Alias = None) -> bool:
    """
    The alias record says whether the target was a folder.
    kBookmarkFileProperties begins with the CFURL resource flags.
    """
    if bookmark is not None:
        props = bookmark.get(kBookmarkFileProperties)
        raw = getattr(props, "bytes", None)
        if isinstance(raw, (bytes, bytearray)) and len(raw) >= 8:
            flags: int = struct.unpack_from("<Q", raw, 0)[0]
            return (flags & kCFURLResourceIsDirectory) != 0
    if classic is not None:
        return classic.target.kind == ALIAS_KIND_FOLDER
    return False

#----------------------------------------------------------------------------------------
#   getAlias() - GET file path from an ALIAS
#----------------------------------------------------------------------------------------

def getAlias(aliasPathName: str, debug: bool = False) -> tuple[bool,str]:
    """
    GET file path from an ALIAS.

    A Finder alias is a book/mark file. An older Alias record has no book/mark
    header. A plain file or folder is not an alias.

    debug=True asks mac_alias to print the decoded bookmark or alias record.
    The default is False, so a normal call stays quiet.
    """
    success: bool = False
    target_path: str = ""
    try:
        if os.path.isdir(aliasPathName):
            logError("getAlias()-> ", c.RED,
                     "%s is a folder, not an alias." % aliasPathName)
            return (success, target_path)

        with open(aliasPathName, "rb") as aliasFile:
            data = aliasFile.read()

        bookmark = None
        classic = None
        # Finder writes "book" / "mark" and leaves the size fields zero.
        # Bookmark.from_bytes() requires those fields.
        if data[:4] == b"book" and data[8:12] == b"mark":
            hdrsize = struct.unpack_from("<I", data, 16)[0]
            data = struct.pack("<4sIII", b"book", len(data), 0x10040000, hdrsize) + data[16:]
            bookmark = Bookmark.from_bytes(data, debug=debug)
            target_path = bookmarkTarget(bookmark)
        elif isClassicAlias(data):
            classic = Alias.from_bytes(data, debug=debug)
            posix = classic.target.posix_path
            mount = classic.volume.posix_path if classic.volume is not None else None
            if isinstance(posix, bytes):
                posix = posix.decode()
            if isinstance(mount, bytes):
                mount = mount.decode()
            # The classic record stores the path relative to its volume.
            if mount and posix:
                relative = posix[1:] if posix.startswith(os.sep) else posix
                on_volume = os.path.join(mount, relative)
                target_path = on_volume if os.path.exists(on_volume) else posix
            else:
                target_path = posix or ""
        else:
            logError("getAlias()-> ", c.RED,
                     "%s is a file, not an alias." % aliasPathName)
            return (success, target_path)

        if target_path == "" or not os.path.exists(target_path):
            kind: str = "folder" if pointsAtFolder(bookmark, classic) else "file"
            logError("getAlias()-> ", c.RED,
                     "%s is a broken alias to a %s." % (aliasPathName, kind))
            return (success, "")

        success = True
        if verbosity > 1:
            logError("getAlias()-> ", c.GRN, "Alias at ", c.BLK, aliasPathName, c.GRN,
                     "Points to ", c.BLU, target_path, "\n", suppress=True)
    except FileNotFoundError:
        logError("getAlias()-> ", c.RED, "Alias file not found.")
    except Exception as e:
        logError("getAlias()-> ", c.RED, f"An error occurred: {e}")
    return (success, target_path)


#----------------------------------------------------------------------------------------
#   logError() - LOG ERROR (Eliminate duplicates)
#----------------------------------------------------------------------------------------

def logError(msg1: str, *msg2:str, suppress:bool=False)-> None:
    """
    The logError() function takes a series of strings and outputs them to stderr.
    The suppress boolean suppresses the following actions:
        - the addition of the color RED and the string "***" at the start of message
    """

    global lineCount, lastErrorLine, errorCount

    # Combine all optional arguments into one string
    myString:str =""
    for s in msg2:
        myString+=s

    if suppress:    # For run message, suppress counting and additions to message
        message = ("%s%s"+c.EDC) % (msg1.strip(), myString.strip())
    else:
        # Eliminate Bright Red and "***" for informational messages
        message = (c.BRED+"\n*** %s"+c.EDC+"%s"+c.EDC) % (msg1.strip(), myString.strip())
    if TestMode:
        message = _colorCode.sub("", message)
    print(message, file=sys.stderr, sep='', end='\n')
    return

#----------------------------------------------------------------------------------------
#   main() - MAIN entry point when run
#----------------------------------------------------------------------------------------
# Entry point when run

def main() -> None:
    
    global verbosity, bootVolume, homeVolume, uName, gName, TestMode
    
    if verbosity > 0:
        logError("\nmain()-> ", c.GRN+"bootVolume: "+c.BLU+bootVolume, suppress=True)
        logError("\nmain()-> ", c.GRN+"homeVolume: "+c.BLU+homeVolume, suppress=True)
        logError("\nmain()-> ", c.GRN+"uName: ", c.BLU+uName, suppress=True)
        logError("\nmain()-> ", c.GRN+"gName: ", c.BLU+gName, suppress=True)
        
    # class argparse.ArgumentParser(
    #   prog=None, usage=None, description=None, epilog=None, parents=[],
    #   formatter_class=argparse.HelpFormatter, prefix_chars='-',
    #   fromfile_prefix_chars=None, argument_default=None, conflict_handler='error',
    #   add_help=True, allow_abbrev=True)
    parser: argparse.ArgumentParser = argparse.ArgumentParser(prog=progName, argument_default=0, \
        usage=c.BBLK+'\n     %(prog)s '+c.BYEL+'[-h|-H] '+c.BCYN+'[-V] \n'+\
        c.BBLK+'     %(prog)s '+c.BMAG+'[-vv] '+c.BWHT+'[-t|-T] '+c.BRED+'[-s|-S] '+\
        c.BBLU+'[-u '+c.RBLU+'user name'+c.ROFF+'] '+\
        c.BGRN+'[-g '+c.RGRN+'group name'+c.ROFF+'] '+\
        c.BMAG+'<'+c.RMAG+'alias file name'+c.ROFF+'>'+c.EDC, \
        epilog='.',
        description=c.BBLK+'look up target file name from alias'+c.EDC, \
        add_help=False)
        
    # class argparse.ArgumentParser.add_argument
    #   (name or flags...[, action][, nargs][, const][, default]
    #   [, type][, choices][, required][, help][, metavar][, dest])
    
    parser.add_argument('-h', '-H', '--help', action='help', \
        help=c.BYEL+'show this help message and exit'+c.EDC)
    
    parser.add_argument('-V', '--version', action='version', version=versionDesc, \
        help=c.BCYN+'show program\'s version number and exit'+c.EDC)
    
    parser.add_argument('-v', '--verbose', action='count', default=0, \
        help=c.BMAG+'verbose invocation'+c.EDC)
     
    parser.add_argument('-t', '-T', '--test', dest='testMode', action='store_true', default=False, \
        help=c.BWHT+'test mode'+c.EDC)

    parser.add_argument('-q', '-Q', '--quiet', action='store_true', default=False, \
        help=c.BCYN+'quiet invocation'+c.EDC)
   
    parser.add_argument('-u', '--user',  action='store',  type=str, default=uName, \
        help=c.BBLU+'user name'+c.BOFF+c.EDC)
    
    parser.add_argument('-g', '--group',  action='store', type=str, default=gName, \
        help=c.BGRN+'group name'+c.BOFF+c.EDC)
    
    parser.add_argument('-s', '-S', '--superuser',  action='store_true', default=False, \
        help=c.BRED+'super user mode! '+c.BOFF+c.EDC)
        
    parser.add_argument('aliasName',  action='store', default=False, \
        help=c.BMAG+'alias file name '+c.BOFF+c.EDC)
        
    #args: Args = Args(**parser.parse_args().__dict__)
    args: Args = Args(**{k: v for k, v in parser.parse_args().__dict__.items() if k in Args._fields})
    verbosity = verbosity + args.verbose
    TestMode = args.testMode
    superUser: bool = args.superuser
    userName: str = args.user
    groupName: str = args.group
    aliasName: str = args.aliasName
    quiet: bool = args.quiet
    
    success: bool = False
    
    if verbosity > 0:
        logError("\nmain()-> ", c.GRN, "args.verbose = ", c.BLU, str(args.verbose), \
            suppress=True)
        logError("main()-> ", c.GRN+"verbosity is ", c.BLU, "non-zero", c.GRN, \
            "!", suppress=True)
        logError("main()-> ", c.GRN+"superUser = ", c.BLU, "%s" % superUser, suppress=True)
        logError("main()-> ", c.GRN+"userName = ", c.BLU, "%s" % userName, suppress=True)
        logError("main()-> ", c.GRN+"groupName = ", c.BLU, "%s" % groupName, suppress=True)
        logError("main()-> ", c.GRN+"aliasName = ", c.BLU, "%s" % aliasName, suppress=True)
        
    fileName: str = ""
    success,fileName = getAlias(aliasName, debug=(verbosity > 0))
    if fileName != "":
        logError("", c.BLU, "%s" % fileName, suppress=True)
    os.sync()
    sys.exit(0)
    
#----------------------------------------------------------------------------------------
# Standard boilerplate to call the main() function to begin
# the program.
#----------------------------------------------------------------------------------------

if __name__ == '__main__':
    main()
