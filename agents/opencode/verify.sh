#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
config_home="${XDG_CONFIG_HOME:-$HOME/.config}"
opencode_config="$config_home/opencode"
failed=0

check() {
  local name="$1"
  shift
  if "$@"; then
    printf 'ok: %s\n' "$name"
  else
    printf 'fail: %s\n' "$name" >&2
    failed=1
  fi
}

check "opencode binary" command -v opencode
check "rtk binary" command -v rtk
check "codebase-memory-mcp binary" command -v codebase-memory-mcp
check "rtk plugin symlink" test -L "$opencode_config/plugins/rtk.ts"
check "caveman plugin symlink" test -L "$opencode_config/plugins/caveman"
check "caveman plugin file" test -f "$opencode_config/plugins/caveman/plugin.js"
check "caveman skill symlink" test -L "$opencode_config/skills/caveman"
check "caveman skill file" test -f "$opencode_config/skills/caveman/SKILL.md"
check "ponytail plugin symlink" test -L "$opencode_config/plugins/ponytail"
check "ponytail plugin file" test -f "$opencode_config/plugins/ponytail/.opencode/plugins/ponytail.mjs"
check "stack rules symlink" test -L "$opencode_config/AGENTS.stack.md"

if command -v opencode >/dev/null 2>&1; then
  check "context-mode plugin" bash -c "opencode debug config | grep -q 'context-mode'"
  check "caveman plugin config" bash -c "opencode debug config | grep -q 'plugins/caveman/plugin.js'"
  check "ponytail plugin config" bash -c "opencode debug config | grep -q 'plugins/ponytail/.opencode/plugins/ponytail.mjs'"
  check "stack rules imported" bash -c "opencode debug config | grep -q 'AGENTS.stack.md'"
  check "caveman plugin loaded" bash -c "opencode debug info | grep -q 'plugins/caveman/plugin.js'"
  check "ponytail plugin loaded" bash -c "opencode debug info | grep -q 'plugins/ponytail/.opencode/plugins/ponytail.mjs'"
  check "CBM not global" bash -c "! grep -q 'codebase-memory-mcp' '$opencode_config/opencode.json'"
fi

check "node binary" command -v node
check "caveman plugin module" node --input-type=module -e "import('$opencode_config/plugins/caveman/plugin.js').then((m) => { if (typeof m.CavemanPlugin !== 'function') process.exit(1) })"
check "caveman ruleset" node -e "const c = require('$opencode_config/plugins/caveman/caveman-config.cjs'); const r = c.loadFilteredRuleset('full', '$opencode_config/plugins/caveman'); if (!r || !r.includes('Respond terse like smart caveman')) process.exit(1)"
check "ponytail plugin module" node --input-type=module -e "import('$opencode_config/plugins/ponytail/.opencode/plugins/ponytail.mjs').then((m) => { if (typeof m.default.server !== 'function') process.exit(1) })"
check "ponytail ruleset" node -e "const { getPonytailInstructions } = require('$opencode_config/plugins/ponytail/hooks/ponytail-instructions.js'); if (!getPonytailInstructions('full').includes('PONYTAIL MODE ACTIVE')) process.exit(1)"

check "no U+2014 or U+2192 in documents" bash -c "! grep -RInP '\x{2014}|\x{2192}' '$repo_dir/README.md' '$repo_dir/AGENTS.stack.md' '$repo_dir/docs' >/dev/null 2>&1"

local_verify="$repo_dir/../../local/opencode/verify.local.sh"
if [ -x "$local_verify" ]; then
  if ! "$local_verify" "$opencode_config"; then
    failed=1
  fi
fi

if [ "$failed" -ne 0 ]; then
  printf 'verification failed\n' >&2
  exit 1
fi
printf 'verification passed\n'
