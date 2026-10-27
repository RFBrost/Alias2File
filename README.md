# Alias to File

**Local Path:**     [~/SOFTWARE/PYTHON/Alias2File/alias2file.py](~/SOFTWARE/PYTHON/Alias2File/alias2file.py)

**Description:**    print the path a Finder alias points to

**usage:**

```
alias2file [-h|-H] [-V]

alias2file [-v] [-q|-Q] [-s|-S] [-u user name] [-g group name] <alias file name>
```

look up the target of an **alias** [^1]

`<alias file name>` may be a Finder alias or a real directory. A directory has no alias bytes, so the program reports that directory's own path. A relative path is accepted.

**positional arguments:**
```
  alias file name       alias file name
```
**options:**
```
  -h, -H, --help        show this help message and exit
  -V, --version         show program's version number and exit
  -v, --verbose         verbose invocation. Also prints the bookmark, or a classic Alias record
  -q, -Q, --quiet       quiet invocation
  -u, --user USER       user name (rfbrost)
  -g, --group GROUP     group name (Family)
  -s, -S, --superuser   super user mode!


```
---

The companion program is **file2alias**, which writes an alias in the current directory.

A Finder alias made since Mac OS X 10.6 is a bookmark in a `book`/`mark` file. An older Alias record has no `book`/`mark` header. `-v` says which one was read.

---
[^1]: A link in ~/SOFTWARE/bin exists which points alias2file -> ~/SOFTWARE/PYTHON/Alias2File/alias2file.py
