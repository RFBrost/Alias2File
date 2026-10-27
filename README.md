# Alias to File

**Local Path:**     [~/SOFTWARE/PYTHON/Alias2File/alias2file.py](~/SOFTWARE/PYTHON/Alias2File/alias2file.py)

**Description:**    print the path a Finder alias points to

**usage:**

```
alias2file [-h|-H] [-V]

alias2file [-v] [-t|-T] [-q|-Q] [-s|-S] [-u user name] [-g group name] <alias file name>
```

look up the target of an **alias** [^1]

`<alias file name>` is a Finder alias or an older Alias record. A relative path is accepted. A plain file prints `<file> is a file, not an alias.` A plain folder prints `<folder> is a folder, not an alias.`

`-t` leaves the color codes out.

**positional arguments:**
```
  alias file name       alias file name
```
**options:**
```
  -h, -H, --help        show this help message and exit
  -V, --version         show program's version number and exit
  -v, --verbose         verbose invocation. Also prints the bookmark, or a classic Alias record
  -t, -T, --test        test mode. Color codes are left out of the messages
  -q, -Q, --quiet       quiet invocation
  -u, --user USER       user name (rfbrost)
  -g, --group GROUP     group name (Family)
  -s, -S, --superuser   super user mode!


```
---

The companion program is **file2alias**, which writes an alias in the current directory.

A Finder alias made since Mac OS X 10.6 is a bookmark in a `book`/`mark` file. An older Alias record has no `book`/`mark` header. `-v` says which one was read.

**tests:**

```
cd ~/SOFTWARE/PYTHON/Alias2File
./test/test.sh
```

`test/test.sh` runs `alias2file -t` on the files in `test/` and compares each result to a known string. A match prints `Success.` A mismatch prints `FAILED!` The script exits `$SHELL_GOOD` when every comparison matches and `$SHELL_BAD` when one does not.

The checks are `AFile alias`, `AFolder alias`, the plain file `AFile`, the plain folder `AFolder`, `AMissingFile alias`, and `AMissingFolder alias`.

---
[^1]: A link in ~/SOFTWARE/bin exists which points alias2file -> ~/SOFTWARE/PYTHON/Alias2File/alias2file.py
