#!/usr/bin/env python3
"""Adapt RTK's Claude PreToolUse hook output to Codex hooks."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

def main() -> int:
    proc = subprocess.run([shutil.which("rtk") or str(Path.home() / ".local/bin/rtk"), "hook", "claude"], input=sys.stdin.read(), text=True, capture_output=True, check=False)
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        return proc.returncode
    if not proc.stdout.strip():
        return 0
    try:
        output = json.loads(proc.stdout)
        specific = output.get("hookSpecificOutput", {})
        if specific.get("updatedInput") is not None:
            specific["permissionDecision"] = "allow"
        print(json.dumps(output, separators=(",", ":")))
    except (json.JSONDecodeError, TypeError):
        sys.stdout.write(proc.stdout)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
