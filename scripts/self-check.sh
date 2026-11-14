#!/usr/bin/env bash
# Checks before a commit: installer tests, nothing machine-specific in public files, typography.
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT"
fail=0

echo "== Codex installer tests =="
(cd agents/codex && python3 -B -m unittest discover -s tests) >/dev/null 2>&1 && echo OK || { echo FAILED; fail=1; }

echo "== Claude switcher tests =="
(cd agents/claude-code/skills/stack && python3 -B -m unittest test_toggle) >/dev/null 2>&1 && echo OK || { echo FAILED; fail=1; }

# Public files: everything git tracks or would add, except local/.
mapfile -t files < <(git ls-files --cached --others --exclude-standard | grep -v '^local/')

echo "== privacy =="
# Real home folders and drive mounts; documentation uses ~ and neutral examples instead.
patterns=('/home/[a-z][a-z0-9_-]*/' '/Users/[A-Za-z][A-Za-z0-9_-]*/' '/mnt/[a-z]/' 'C:\\Users\\')
if [[ -f local/private-patterns.txt ]]; then
  while IFS= read -r p; do [[ -n $p && $p != \#* ]] && patterns+=("$p"); done < local/private-patterns.txt
fi
for p in "${patterns[@]}"; do
  if hits=$(grep -nIE -- "$p" "${files[@]}" 2>/dev/null | grep -v '^scripts/self-check.sh:'); then
    echo "private pattern '$p':"; echo "$hits"; fail=1
  fi
done

echo "== typography =="
# No em dash or arrow characters in documents: use "-" and "->". Code may match such text verbatim.
mapfile -t docs < <(printf '%s\n' "${files[@]}" | grep '\.md$')
if hits=$(grep -nP '\x{2014}|\x{2192}' "${docs[@]}" 2>/dev/null); then
  echo "$hits"; fail=1
fi

echo "== ru copies =="
for f in $(printf '%s\n' "${files[@]}" | grep -E '(^README|^docs/.*|/README)\.md$' | grep -v -e '\.ru\.md$' -e '^local.example/'); do
  [[ -f ${f%.md}.ru.md ]] || { echo "missing ${f%.md}.ru.md"; fail=1; }
done

((fail)) && { echo "self-check: FAIL"; exit 1; }
echo "self-check: PASS"
