#!/usr/bin/env python3
"""Install and toggle the global Codex token-saving stack."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import urllib.request
from dataclasses import dataclass
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]
# Machine-specific rules (git-ignored) appended to the public AGENTS.md when present.
LOCAL_GUIDANCE = Path(os.environ.get("TOKEN_STACK_LOCAL", REPO.parents[1] / "local")) / "codex/AGENTS.md"
COMPONENTS = ("rtk", "cbm", "native", "te")
ROOT_START = "# >>> codex-token-stack root >>>"
ROOT_END = "# <<< codex-token-stack root <<<"
CBM_START = "# >>> codex-token-stack cbm >>>"
CBM_END = "# <<< codex-token-stack cbm <<<"
PERMISSIONS_START = "# >>> codex-token-stack permissions >>>"
PERMISSIONS_END = "# <<< codex-token-stack permissions <<<"
CBM_UPDATER_START = "# >>> codebase-memory-mcp SessionStart >>>"
CBM_UPDATER_END = "# <<< codebase-memory-mcp SessionStart <<<"
BINARY_SPECS = {
    "rtk": {
        "version": (0, 49, 0),
        "url": "https://github.com/rtk-ai/rtk/releases/download/v0.49.0/rtk-x86_64-unknown-linux-musl.tar.gz",
        "sha256": "a051b22361c7cfa36022bc3f06bb41cdc88e58a07263dc340d8bd3468c41befe",
    },
    "codebase-memory-mcp": {
        "version": (0, 12, 1),
        "url": "https://github.com/DeusData/codebase-memory-mcp/releases/download/v0.12.1/codebase-memory-mcp-linux-amd64-portable.tar.gz",
        "sha256": "77745491f0a9c346d6da23eed4d92b5feaa31a27a883c9faa4fa9f47c8183705",
    },
}


@dataclass(frozen=True)
class Layout:
    home: Path

    @property
    def codex(self) -> Path:
        return self.home / ".codex"

    @property
    def agents(self) -> Path:
        return self.home / ".agents"

    @property
    def config(self) -> Path:
        return self.codex / "config.toml"

    @property
    def hooks(self) -> Path:
        return self.codex / "hooks.json"

    @property
    def guidance(self) -> Path:
        return self.codex / "AGENTS.md"

    @property
    def skill(self) -> Path:
        return self.agents / "skills" / "token-stack"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def backup_once(path: Path) -> None:
    if not path.exists() or path.is_symlink():
        return
    backup = path.with_name(path.name + ".pre-token-stack")
    if not backup.exists():
        shutil.copy2(path, backup)


def strip_block(text: str, start: str, end: str) -> str:
    pattern = re.compile(
        rf"(?ms)^\s*{re.escape(start)}\s*$.*?^\s*{re.escape(end)}\s*$\n?"
    )
    return pattern.sub("", text)


def strip_marker_lines(text: str, start: str, end: str) -> str:
    return "".join(line for line in text.splitlines(keepends=True) if line.strip() not in {start, end})


def strip_cbm_tables(text: str) -> str:
    targets = ("mcp_servers.codebase-memory", "mcp_servers.codebase-memory-mcp")
    kept: list[str] = []
    skipping = False
    for line in text.splitlines(keepends=True):
        match = re.match(r"^\s*\[([^]]+)]\s*(?:#.*)?$", line)
        if match:
            name = match.group(1)
            skipping = any(name == target or name.startswith(target + ".") for target in targets)
        if not skipping:
            kept.append(line)
    return "".join(kept)


def strip_root_keys(text: str) -> str:
    kept: list[str] = []
    in_root = True
    for line in text.splitlines(keepends=True):
        if re.match(r"^\s*\[", line):
            in_root = False
        if in_root and re.match(
            r"^\s*(tool_output_token_limit|project_doc_max_bytes|sandbox_mode|default_permissions|approval_policy|approvals_reviewer|auto_review\.extra_policy)\s*=", line
        ):
            continue
        kept.append(line)
    return "".join(kept)


def ensure_hooks_feature(text: str) -> str:
    lines = text.splitlines(keepends=True)
    feature_at = None
    next_table = len(lines)
    for index, line in enumerate(lines):
        match = re.match(r"^\s*\[([^]]+)]\s*(?:#.*)?$", line)
        if not match:
            continue
        if feature_at is not None:
            next_table = index
            break
        if match.group(1) == "features":
            feature_at = index
    if feature_at is None:
        suffix = "" if not text or text.endswith("\n") else "\n"
        return text + suffix + "\n[features]\nhooks = true\n"

    for index in range(feature_at + 1, next_table):
        if re.match(r"^\s*hooks\s*=", lines[index]):
            lines[index] = "hooks = true\n"
            return "".join(lines)
    lines.insert(feature_at + 1, "hooks = true\n")
    return "".join(lines)


def cbm_binary() -> str:
    return shutil.which("codebase-memory-mcp") or str(
        Path.home() / ".local/bin/codebase-memory-mcp"
    )


def root_block(native: bool) -> str:
    native_lines = "tool_output_token_limit = 10000\nproject_doc_max_bytes = 16384\n" if native else ""
    return f"{ROOT_START}\n{native_lines}" + (
        'default_permissions = "workspace-only"\n'
        'approval_policy = "on-request"\n'
        'approvals_reviewer = "auto_review"\n'
        "auto_review.extra_policy = '''\n"
        "For filesystem actions outside the current workspace, approve only when the user explicitly requested work in that directory or path. Do not infer authorization from convenience or proximity to the workspace. Keep any approval limited to the requested path and action. Deny ambiguous or unrelated access and ask the user to specify the target. Apply the default reviewer safety policy as well.\n"
        "'''\n"
        f"{ROOT_END}\n\n"
    )


def cbm_block() -> str:
    tools = (
        '"index_status", "index_repository", "detect_changes", "search_graph", '
        '"get_architecture", "trace_path", "get_code_snippet", "search_code"'
    )
    return (
        f"{CBM_START}\n"
        "[mcp_servers.codebase-memory]\n"
        f'command = "{cbm_binary()}"\n'
        "enabled = true\n"
        "startup_timeout_sec = 20\n"
        "tool_timeout_sec = 120\n"
        f"enabled_tools = [{tools}]\n"
        f"{CBM_END}\n"
    )


def claude_read_denies(home: Path) -> list[str]:
    """Paths Claude Code may not read, from ~/.claude/settings.json, so Codex sees the same files.
    The two lists anchor paths differently (Claude docs):
    - permissions.deny Read(...): //x absolute, ~/x home, /x relative to ~/.claude, x relative to cwd;
    - sandbox.filesystem.denyRead: /x and //x absolute, ~/x home, ./x or x relative to ~/.claude.
    Cwd-relative rules and globs inside a path have no Codex equivalent and are skipped."""
    try:
        settings = json.loads((home / ".claude/settings.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    def strip(path: str) -> str:
        return re.sub(r"/\*\*$", "", path)

    paths: list[str] = []
    for rule in settings.get("permissions", {}).get("deny", []):
        m = re.fullmatch(r"Read\((.+)\)", rule)
        if not m:
            continue
        p = strip(m.group(1))
        if p.startswith("//"):
            paths.append(p[1:])
        elif p.startswith("~/"):
            paths.append(p)
        elif p.startswith("/"):
            paths.append("~/.claude" + p)
    for p in settings.get("sandbox", {}).get("filesystem", {}).get("denyRead", []):
        p = strip(p)
        if p.startswith("//"):
            p = p[1:]
        elif not p.startswith(("/", "~/")):
            p = "~/.claude/" + p.removeprefix("./")
        paths.append(p)
    return list(dict.fromkeys(p for p in paths if "*" not in p))


def permissions_block(home: Path) -> str:
    """Same as Claude Code: the whole file system is readable except Claude's
    denied paths, writes stay in the workspace, auto_review judges the rest.
    No ":root" deny: Codex runs its own binary from ~/.codex/packages inside bwrap."""
    denies = "".join(f'{json.dumps(path)} = "deny"\n' for path in claude_read_denies(home))
    return (
        f"{PERMISSIONS_START}\n"
        "[permissions.workspace-only]\n"
        'extends = ":workspace"\n'
        + (f"\n[permissions.workspace-only.filesystem]\n{denies}" if denies else "")
        + f"{PERMISSIONS_END}\n"
    )


def update_config(layout: Layout, *, native: bool | None, cbm: bool | None) -> None:
    backup_once(layout.config)
    current = read_text(layout.config)
    try:
        parsed = tomllib.loads(current) if current.strip() else {}
    except tomllib.TOMLDecodeError as error:
        raise SystemExit(f"Invalid {layout.config}: {error}") from error

    current_native = (
        parsed.get("tool_output_token_limit") == 10000
        and parsed.get("project_doc_max_bytes") == 16384
    )
    servers = parsed.get("mcp_servers", {})
    current_cbm = bool(servers.get("codebase-memory", {}).get("enabled", True))
    if "codebase-memory" not in servers:
        current_cbm = False

    native = current_native if native is None else native
    cbm = current_cbm if cbm is None else cbm

    text = strip_block(current, ROOT_START, ROOT_END)
    text = strip_marker_lines(text, CBM_START, CBM_END)
    text = strip_block(text, PERMISSIONS_START, PERMISSIONS_END)
    text = strip_block(text, CBM_UPDATER_START, CBM_UPDATER_END)
    text = strip_root_keys(strip_cbm_tables(text)).lstrip("\n")
    text = ensure_hooks_feature(text).rstrip() + "\n"
    text = root_block(native) + text
    text = text.rstrip() + "\n\n" + permissions_block(layout.home)
    if cbm:
        text = text.rstrip() + "\n\n" + cbm_block()
    tomllib.loads(text)
    write_text(layout.config, text)


def rtk_entry() -> dict:
    return {
        "matcher": "^Bash$",
        "hooks": [
            {
                "type": "command",
                "command": f"python3 {REPO}/skills/token-stack/scripts/rtk-codex-hook.py",
                "timeout": 10,
                "statusMessage": "Optimizing command output with RTK",
            }
        ],
    }


def has_rtk(entry: object) -> bool:
    return isinstance(entry, dict) and "rtk-codex-hook.py" in json.dumps(entry)


def update_hooks(layout: Layout, enabled: bool) -> None:
    backup_once(layout.hooks)
    try:
        data = json.loads(read_text(layout.hooks) or "{}")
    except json.JSONDecodeError as error:
        raise SystemExit(f"Invalid {layout.hooks}: {error}") from error
    hooks = data.setdefault("hooks", {})
    pre = hooks.setdefault("PreToolUse", [])
    hooks["PreToolUse"] = [entry for entry in pre if not has_rtk(entry)]
    if enabled:
        hooks["PreToolUse"].append(rtk_entry())
    if not hooks["PreToolUse"]:
        hooks.pop("PreToolUse")
    write_text(layout.hooks, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def ensure_symlink(target: Path, source: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_symlink() and target.resolve() == source.resolve():
        return
    if target.exists() or target.is_symlink():
        if target.is_dir() and not target.is_symlink():
            raise SystemExit(f"Cannot replace a directory: {target}")
        backup_once(target)
        target.unlink()
    target.symlink_to(source)


def version_tuple(text: str) -> tuple[int, ...]:
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", text)
    return tuple(map(int, match.groups())) if match else ()


def install_binary(name: str, spec: dict, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(spec["url"], headers={"User-Agent": "codex-token-stack/1"})
    with tempfile.TemporaryDirectory(prefix="codex-token-stack-") as tmp:
        archive = Path(tmp) / "release.tar.gz"
        with urllib.request.urlopen(request, timeout=120) as response, archive.open("wb") as output:
            shutil.copyfileobj(response, output)
        with tarfile.open(archive, "r:gz") as bundle:
            bundle.extractall(tmp, filter="data")
        candidates = [path for path in Path(tmp).rglob(name) if path.is_file()]
        if len(candidates) != 1:
            raise SystemExit(f"Archive has {len(candidates)} files named {name}")
        binary = candidates[0]
        digest = hashlib.sha256(binary.read_bytes()).hexdigest()
        if digest != spec["sha256"]:
            raise SystemExit(f"SHA-256 of {name} does not match: {digest}")
        staged = target.with_name(target.name + ".new")
        shutil.copy2(binary, staged)
        staged.chmod(0o755)
        staged.replace(target)


def bootstrap(layout: Layout) -> None:
    if platform.system() != "Linux" or platform.machine() not in {"x86_64", "amd64"}:
        raise SystemExit("Bootstrap supports Linux x86_64 only; see README for a manual installation.")
    for name, spec in BINARY_SPECS.items():
        current = version_tuple(command_version(name))
        if current >= spec["version"]:
            continue
        target = layout.home / ".local/bin" / name
        print(f"Installing {name} {'.'.join(map(str, spec['version']))} to {target}")
        install_binary(name, spec, target)


def guidance_text() -> str | None:
    """Public rules + local rules, or None when there are no local rules (then a symlink)."""
    if not LOCAL_GUIDANCE.exists():
        return None
    return read_text(REPO / "AGENTS.md").rstrip() + "\n\n" + read_text(LOCAL_GUIDANCE)


def install_guidance(layout: Layout) -> None:
    text = guidance_text()
    if text is None:
        ensure_symlink(layout.guidance, REPO / "AGENTS.md")
        return
    if layout.guidance.is_symlink():
        layout.guidance.unlink()
    else:
        backup_once(layout.guidance)
    write_text(layout.guidance, text)


def install(layout: Layout) -> None:
    bootstrap(layout)
    install_guidance(layout)
    ensure_symlink(layout.skill, REPO / "skills/token-stack")
    update_config(layout, native=True, cbm=True)
    update_hooks(layout, True)


def command_version(command: str) -> str:
    binary = shutil.which(command)
    if not binary:
        return "not installed"
    result = subprocess.run(
        [binary, "--version"], text=True, capture_output=True, timeout=10, check=False
    )
    return (result.stdout or result.stderr).strip().splitlines()[0]


def symlink_to(path: Path, source: Path) -> bool:
    return path.is_symlink() and path.exists() and source.exists() and path.samefile(source)


def toggle_te(layout: Layout, enabled: bool, *, explicit: bool) -> None:
    current = read_text(layout.config)
    parsed = tomllib.loads(current)
    key = "tokeneconomizer@tokeneconomizer"
    if key not in parsed.get("plugins", {}):
        if explicit:
            raise SystemExit("TokenEconomizer is not installed in Codex")
        return
    header = re.search(r'(?m)^\[plugins\."tokeneconomizer@tokeneconomizer"\]\s*$', current)
    if not header:
        raise SystemExit("Unknown TokenEconomizer configuration format")
    next_table = re.search(r"(?m)^\[", current[header.end():])
    end = header.end() + next_table.start() if next_table else len(current)
    section = current[header.end():end]
    value = "true" if enabled else "false"
    field = re.search(r"(?m)^enabled\s*=\s*(?:true|false)\s*$", section)
    if field:
        section = section[:field.start()] + f"enabled = {value}" + section[field.end():]
    else:
        section = f"\nenabled = {value}" + section
    updated = current[:header.end()] + section + current[end:]
    tomllib.loads(updated)
    write_text(layout.config, updated)


def states(layout: Layout) -> dict[str, tuple[bool, str]]:
    try:
        config = tomllib.loads(read_text(layout.config))
    except tomllib.TOMLDecodeError:
        config = {}
    try:
        hooks = json.loads(read_text(layout.hooks) or "{}")
    except json.JSONDecodeError:
        hooks = {}

    pre = hooks.get("hooks", {}).get("PreToolUse", [])
    rtk_version = command_version("rtk")
    cbm_version = command_version("codebase-memory-mcp")
    rtk_on = rtk_version != "not installed" and any(has_rtk(entry) for entry in pre)
    server = config.get("mcp_servers", {}).get("codebase-memory", {})
    cbm_on = cbm_version != "not installed" and bool(server.get("enabled", False))
    native_on = (
        config.get("tool_output_token_limit") == 10000
        and config.get("project_doc_max_bytes") == 16384
    )
    text = guidance_text()
    guidance_on = (
        symlink_to(layout.guidance, REPO / "AGENTS.md") if text is None
        else not layout.guidance.is_symlink() and read_text(layout.guidance) == text
    )
    skill_on = symlink_to(layout.skill, REPO / "skills/token-stack")
    te = config.get("plugins", {}).get("tokeneconomizer@tokeneconomizer", {})
    te_installed = (layout.codex / "plugins/cache/tokeneconomizer/tokeneconomizer").exists()
    te_on = te_installed and bool(te.get("enabled", False))
    return {
        "RTK": (rtk_on, rtk_version),
        "Codebase Memory": (cbm_on, cbm_version),
        "Native limits": (native_on, "10000 tokens / 16384 bytes"),
        "TokenEconomizer": (te_on, "experimental Codex plugin" if te_installed else "not installed"),
        "Global guidance": (guidance_on, str(REPO / "AGENTS.md")),
        "Token Stack skill": (skill_on, str(REPO / "skills/token-stack")),
    }


def print_status(layout: Layout, as_json: bool = False) -> None:
    current = states(layout)
    if as_json:
        print(
            json.dumps(
                {name: {"enabled": enabled, "details": details} for name, (enabled, details) in current.items()},
                ensure_ascii=False,
                indent=2,
            )
        )
        return
    print("Component          State      Details")
    for name, (enabled, details) in current.items():
        print(f"{name:<18} {'ON' if enabled else 'OFF':<10} {details}")


def toggle(layout: Layout, action: str, target: str) -> None:
    enabled = action == "on"
    targets = COMPONENTS if target == "all" else (target,)
    if "native" in targets or "cbm" in targets:
        update_config(
            layout,
            native=enabled if "native" in targets else None,
            cbm=enabled if "cbm" in targets else None,
        )
    if "rtk" in targets:
        update_hooks(layout, enabled)
    if "te" in targets:
        toggle_te(layout, enabled, explicit=target == "te")


def doctor(layout: Layout) -> int:
    failures: list[str] = []
    current = states(layout)
    for name, (enabled, details) in current.items():
        if not enabled and name != "TokenEconomizer":
            failures.append(f"{name}: off or unavailable ({details})")

    config_text = read_text(layout.config)
    try:
        config = tomllib.loads(config_text)
        servers = config.get("mcp_servers", {})
        cbm_names = [name for name in servers if name.startswith("codebase-memory")]
        if cbm_names != ["codebase-memory"]:
            failures.append(f"CBM registrations: {cbm_names}")
    except tomllib.TOMLDecodeError as error:
        failures.append(f"config.toml: {error}")

    codex = shutil.which("codex")
    if codex:
        sandbox = subprocess.run(
            [codex, "sandbox", "--", "/bin/true"],
            text=True, capture_output=True, timeout=30, check=False,
            env={**os.environ, "CODEX_HOME": str(layout.codex)},
        )
        if sandbox.returncode or "bwrap" in sandbox.stderr:
            failures.append(
                "the Codex sandbox cannot run commands: "
                + (sandbox.stderr.strip().splitlines() or ["?"])[-1]
            )

    payload = json.dumps(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "rg --files"},
        }
    )
    try:
        result = subprocess.run(
            [sys.executable, str(REPO / "skills/token-stack/scripts/rtk-codex-hook.py")],
            input=payload,
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
        )
        output = json.loads(result.stdout)
        specific = output["hookSpecificOutput"]
        rewritten = specific["updatedInput"]["command"]
        if result.returncode or specific.get("permissionDecision") != "allow":
            failures.append("RTK hook did not allow updatedInput")
        if rewritten != "rtk rg --files":
            failures.append(f"RTK hook rewrote rg --files as: {rewritten}")
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError, KeyError) as error:
        failures.append(f"RTK hook smoke test: {error}")

    if failures:
        print("DOCTOR: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("DOCTOR: OK")
    print("- TOML is valid; one CBM registration")
    print("- RTK rewrites rg --files to rtk rg --files")
    print("- the global AGENTS.md and the skill point to this repository")
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument(
        "--home",
        type=Path,
        default=Path(os.environ.get("TOKEN_STACK_HOME", str(Path.home()))),
        help=argparse.SUPPRESS,
    )
    sub = result.add_subparsers(dest="command", required=True)
    sub.add_parser("bootstrap")
    sub.add_parser("install")
    status = sub.add_parser("status")
    status.add_argument("--json", action="store_true")
    sub.add_parser("doctor")
    for action in ("on", "off"):
        command = sub.add_parser(action)
        command.add_argument("component", choices=(*COMPONENTS, "all"))
    return result


def main() -> int:
    args = parser().parse_args()
    layout = Layout(args.home.expanduser().resolve())
    if args.command == "bootstrap":
        bootstrap(layout)
        print_status(layout)
        return 0
    if args.command == "install":
        install(layout)
        print_status(layout)
        return 0
    if args.command == "status":
        print_status(layout, args.json)
        return 0
    if args.command == "doctor":
        return doctor(layout)
    toggle(layout, args.command, args.component)
    print_status(layout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
