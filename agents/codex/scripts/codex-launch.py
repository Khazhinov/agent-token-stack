#!/usr/bin/env python3
"""Opt-in launcher: trust the selected directory, keeping normal action review."""

import json
import os
import sys
from pathlib import Path


def main():
    args = sys.argv[1:]
    cwd = Path.cwd()
    index = 0
    while index < len(args):
        arg = args[index]
        if arg == "--":
            break
        if arg in ("-C", "--cd") and index + 1 < len(args):
            index += 1
            cwd = Path(args[index]).expanduser().absolute()
        elif arg.startswith("--cd="):
            cwd = Path(arg.split("=", 1)[1]).expanduser().absolute()
        elif arg.startswith("-C") and len(arg) > 2:
            cwd = Path(arg[2:]).expanduser().absolute()
        index += 1

    # CLI trust matching uses exact paths, not a trusted ancestor or wildcard.
    # Include the resolved spelling for symlinked working directories.
    overrides = []
    for path in dict.fromkeys((str(cwd), str(cwd.resolve()))):
        overrides += ["-c", f'projects.{json.dumps(path, ensure_ascii=False)}.trust_level="trusted"']
    binary = Path.home() / ".codex/packages/standalone/current/bin/codex"
    os.execv(binary, [str(binary), "--no-daemon", *overrides, *args])


if __name__ == "__main__":
    main()
