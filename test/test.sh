#!/bin/bash
# --------------------------------------------------------------------------------------
# Compare alias2file -t output with the known results for the files in this directory.
# The result stays in a shell variable. No capture file is written.
# --------------------------------------------------------------------------------------

# Last: Modified 10/27/26  05:31:57 RFB iMac5K - use shell constants for status and color
# --------------------------------------------------------------------------------------
# GLOBAL CONSTANTS: $SHELL_GOOD, $SHELL_BAD -- from ~/.bash_const
# GLOBAL CONSTANTS: $BRED, $BGREEN -- from ~/.bash_colors
# GLOBAL CONSTANTS: $NC -- from ~/.bash_colors
# --------------------------------------------------------------------------------------

root="$(cd "$(dirname "$0")/.." && pwd)"
prog="$root/alias2file.py"
cd "$root" || exit $SHELL_BAD

failures=0

check() {
    local target="$1"
    local expected="$2"
    local result
    # printf x keeps the program's trailing newline, which $(...) would drop.
    result=$("$prog" -t "$target" 2>&1; printf x)
    result="${result%x}"
    if [ "$result" = "$expected" ]; then
        printf '%s-%bSuccess.%b\n' "$target" "$BGREEN" "$NC"
    else
        printf '%s-%bFAILED!%b\n' "$target" "$BRED" "$NC"
        printf '  expected: %q\n' "$expected"
        printf '  actual:   %q\n' "$result"
        failures=$((failures + 1))
    fi
}

check "test/AFile alias" \
    $'main()->fileName = /Volumes/8TB-Mojave3/Users/rfbrost/SOFTWARE/PYTHON/Alias2File/test/AFile\n'

check "test/AFolder alias" \
    $'main()->fileName = /Volumes/8TB-Mojave3/Users/rfbrost/SOFTWARE/PYTHON/Alias2File/test/AFolder\n'

check "test/AFile" \
    $'\n*** getAlias()->test/AFile is a file, not an alias.\nmain()->fileName = \n'

check "test/AFolder" \
    $'\n*** getAlias()->test/AFolder is a folder, not an alias.\nmain()->fileName = \n'

if [ "$failures" -ne 0 ]; then
    exit $SHELL_BAD
fi
exit $SHELL_GOOD
