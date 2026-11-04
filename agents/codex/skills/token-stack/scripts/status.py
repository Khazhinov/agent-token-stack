#!/usr/bin/env python3
"""Backward-compatible status entrypoint."""
import sys

from manage import main

if __name__ == "__main__":
    sys.argv[1:] = ["status"]
    raise SystemExit(main())
