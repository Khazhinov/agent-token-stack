#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$repo_dir/skills/token-stack/scripts/manage.py" install
python3 "$repo_dir/skills/token-stack/scripts/manage.py" doctor
