#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
config_home="${XDG_CONFIG_HOME:-$HOME/.config}"
opencode_config="$config_home/opencode"
backup_suffix=".pre-agent-token-stack"

backup_target() {
  local target="$1"
  if { [ -e "$target" ] || [ -L "$target" ]; } && [ ! -e "$target$backup_suffix" ] && [ ! -L "$target$backup_suffix" ]; then
    cp -a --no-dereference "$target" "$target$backup_suffix"
    printf 'backup: %s -> %s%s\n' "$target" "$target" "$backup_suffix"
  fi
}

link_file() {
  local source="$1"
  local target="$2"
  mkdir -p "$(dirname "$target")"
  if [ -L "$target" ] && [ "$(readlink -f "$target")" = "$(readlink -f "$source")" ]; then
    printf 'ok: %s\n' "$target"
    return
  fi
  if [ -e "$target" ] || [ -L "$target" ]; then
    backup_target "$target"
    if [ -d "$target" ] && [ ! -L "$target" ]; then
      rm -rf "$target"
    else
      rm -f "$target"
    fi
  fi
  ln -s "$source" "$target"
  printf 'linked: %s -> %s\n' "$target" "$source"
}

mkdir -p "$opencode_config/plugins" "$opencode_config/skills"

link_file "$repo_dir/plugins/rtk.ts" "$opencode_config/plugins/rtk.ts"
link_file "$repo_dir/plugins/caveman" "$opencode_config/plugins/caveman"
link_file "$repo_dir/plugins/ponytail" "$opencode_config/plugins/ponytail"
link_file "$repo_dir/skills/caveman" "$opencode_config/skills/caveman"
link_file "$repo_dir/AGENTS.stack.md" "$opencode_config/AGENTS.stack.md"

for tool in rtk codebase-memory-mcp; do
  if command -v "$tool" >/dev/null 2>&1; then
    printf 'ok: %s (%s)\n' "$tool" "$("$tool" --version 2>/dev/null | head -n 1)"
  else
    printf 'warning: %s not found in PATH\n' "$tool" >&2
  fi
done

printf 'OpenCode stack configuration installed. Restart OpenCode sessions to apply.\n'
