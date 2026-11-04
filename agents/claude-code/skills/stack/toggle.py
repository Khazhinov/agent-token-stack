#!/usr/bin/env python3
"""
Claude Code token optimization stack control.
Usage: toggle.py [status | on TOOL | off TOOL | mode MODE | update [apply [TOOL|all]]]
Tools: rtk  headroom  cbm  context-mode  caveman  ponytail  te  all
After third-party installers (CBM updater): toggle.py normalize
"""
import json, sys, subprocess, re, urllib.request, tempfile, tarfile, os, shutil
from pathlib import Path

HOME        = Path.home()
SETTINGS    = HOME / ".claude/settings.json"
CLAUDE_JSON = HOME / ".claude.json"
STASH       = HOME / ".claude/skills/stack/stash.json"
INSTALLED_PLUGINS = HOME / ".claude/plugins/installed_plugins.json"

TOOLS = ["rtk", "headroom", "cbm", "context-mode", "caveman", "ponytail", "te"]

# Plugin tools: the plugin declares its hooks and MCP; only enabledPlugins in
# ~/.claude/settings.json is switched. For te this is Claude's only switch: the shared
# ~/.tokeneconomizer/config.json (Codex reads it too) and ~/.codex stay untouched.
PLUGINS = {
    "context-mode": "context-mode@context-mode",
    "caveman":      "caveman@caveman",
    "ponytail":     "ponytail@ponytail",
    "te":           "tokeneconomizer@tokeneconomizer",
}

# No savings percentages on purpose: they were not measured here; vendor claims
# are collected in docs/STACK.md
LABELS = {
    "rtk":            "RTK           (experimental; shell output)",
    "headroom":       "Headroom      (API proxy)",
    "cbm":            "CBM hooks     (code graph)",
    "context-mode":   "context-mode  (large outputs)",
    "caveman":        "Caveman       (answer style)",
    "ponytail":       "Ponytail      (minimal code)",
    "te":             "TokenEconomizer (experimental; Claude plugin)",
}

NEEDS_RESTART = {"rtk", "cbm", "context-mode", "caveman", "ponytail", "te"}

MODES = {
    "doc": {"off": ["caveman", "context-mode", "ponytail"], "on": []},
    "dev": {"off": [], "on": ["rtk", "cbm", "caveman", "context-mode", "ponytail"]},
}
MODE_LABEL = {
    "doc": "doc  - Documents   (caveman + context-mode + ponytail off)",
    "dev": "dev  - Development (full stack except headroom)",
}

CLAUDE_MCP_JSON = HOME / ".claude/.mcp.json"
# The Codex part owns the shared CBM version: pin and SHA-256 in BINARY_SPECS of manage.py
CODEX_MANAGE    = Path(__file__).resolve().parents[3] / "codex/skills/token-stack/scripts/manage.py"
# Shared TokenEconomizer config (Claude and Codex); toggle.py only reads it
TE_CONFIG       = HOME / ".tokeneconomizer/config.json"
# Global MCP entries forbidden by policy: CBM is attached per project,
# context-mode is declared by its plugin
FORBIDDEN_GLOBAL_MCP = ("codebase-memory-mcp", "context-mode")
# Hooks of the standalone Caveman installer; they duplicate the plugin's hooks
LEGACY_CAVEMAN_HOOKS = ("/.claude/hooks/caveman-activate.js", "/.claude/hooks/caveman-mode-tracker.js")

# Headroom traces outside settings.env: ~/.bashrc lines and autoMode.environment mentions
BASHRC = HOME / ".bashrc"
HEADROOM_BASHRC = [
    "# Headroom API compression proxy — routes Claude Code requests through localhost:8787",
    "# Service: systemctl --user status headroom-proxy",
    "export ANTHROPIC_BASE_URL=http://127.0.0.1:8787",
]
HEADROOM_AUTOMODE_CUTS = (
    r"Session traffic is proxied — ANTHROPIC_BASE_URL routes through a local HeadRoom proxy at [^;]+; ",
    r"local HeadRoom proxy \([^)]*\), ",
)

# --- Repositories and update methods ---
REPOS = {
    "rtk": {
        "api":    "https://api.github.com/repos/rtk-ai/rtk/releases/latest",
        "binary": "~/.local/bin/rtk",
        "asset":  "rtk-x86_64-unknown-linux-musl.tar.gz",
        "method": "github_binary",
    },
    "headroom": {
        "api":    "https://pypi.org/pypi/headroom-ai/json",
        "binary": "~/.local/bin/headroom",
        "pkg":    "headroom-ai",
        "method": "uv_tool",
        "post":   "systemctl --user restart headroom-proxy",
    },
    "cbm": {
        "api":    "https://api.github.com/repos/DeusData/codebase-memory-mcp/releases/latest",
        "binary": "~/.local/bin/codebase-memory-mcp",
        "method": "codex_pin",
    },
    "context-mode": {
        "api":    "https://api.github.com/repos/mksglu/context-mode/releases/latest",
        "method": "claude_plugin",
    },
    "caveman": {
        "api":    "https://api.github.com/repos/JuliusBrussee/caveman/commits/main",
        "method": "claude_plugin",
    },
    "ponytail": {
        "api":    "https://api.github.com/repos/DietrichGebert/ponytail/releases/latest",
        "method": "claude_plugin",
    },
    "te": {
        # No GitHub releases; the version comes from plugin.json on main
        "api":    "https://raw.githubusercontent.com/microsoft/TokenEconomizer/main/plugin/.claude-plugin/plugin.json",
        "method": "claude_plugin",
    },
}

# Binaries shared with Codex and the experimental RTK are not updated by `update apply all`:
# only by an explicit `update apply rtk|cbm` (docs/STACK.md, shared machine)
SHARED_BINARIES = {"rtk", "cbm"}

DEFAULTS = {
    "rtk": {
        "PreToolUse": [
            {"matcher": "Bash", "hooks": [
                {"type": "command", "command": f"{HOME}/.local/bin/rtk hook claude"}
            ]}
        ]
    },
    "headroom": {"ANTHROPIC_BASE_URL": "http://127.0.0.1:8787"},
    "cbm": {
        "hooks_PreToolUse": [
            {"matcher": "Grep|Glob", "hooks": [
                {"type": "command", "command": "~/.claude/hooks/cbm-code-discovery-gate", "timeout": 5}
            ]}
        ],
        "hooks_SessionStart": [
            {"matcher": "startup",  "hooks": [{"type": "command", "command": "~/.claude/hooks/cbm-session-reminder"}]},
            {"matcher": "resume",   "hooks": [{"type": "command", "command": "~/.claude/hooks/cbm-session-reminder"}]},
            {"matcher": "clear",    "hooks": [{"type": "command", "command": "~/.claude/hooks/cbm-session-reminder"}]},
            {"matcher": "compact",  "hooks": [{"type": "command", "command": "~/.claude/hooks/cbm-session-reminder"}]},
        ]
    },
    "context-mode": {
        "hooks_SessionStart": [
            {"hooks": [{"type": "command", "command": f"\"{HOME}/.claude/hooks/context-mode-cache-heal.mjs\""}]}
        ],
    },
}


def load(path):
    try:
        return json.loads(Path(path).read_text())
    except Exception:
        return {}


def save(path, data):
    tmp = Path(str(path) + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    tmp.rename(path)


def sh(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True).returncode == 0


def sh_out(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return r.stdout.strip() + r.stderr.strip()


def _add_unique(lst, entries):
    """Adds hook entries missing from the list. Returns True if anything changed."""
    added = False
    for e in entries:
        if e not in lst:
            lst.append(e)
            added = True
    return added


def _bashrc_lines():
    try:
        return BASHRC.read_text().splitlines()
    except Exception:
        return []


def _has_keyword(entry, kw):
    if kw in entry.get("command", ""):
        return True
    for h in entry.get("hooks", []):
        if kw in h.get("command", ""):
            return True
    return False


# ── State detection ──────────────────────────────────────────────────────────

def is_on(tool):
    s  = load(SETTINGS)

    if tool == "rtk":
        return any(
            _has_keyword(h, "rtk")
            for h in s.get("hooks", {}).get("PreToolUse", [])
        )

    if tool == "headroom":
        # Any trace counts as on, so off cleans up a partial installation
        return ("8787" in s.get("env", {}).get("ANTHROPIC_BASE_URL", "")
                or sh("systemctl --user is-active headroom-proxy")
                or sh("systemctl --user is-enabled headroom-proxy")
                or any(l in HEADROOM_BASHRC for l in _bashrc_lines())
                or any("HeadRoom" in e for e in s.get("autoMode", {}).get("environment", [])))

    if tool == "cbm":
        return any(
            _has_keyword(h, "cbm-")
            for event in ("PreToolUse", "SessionStart")
            for h in s.get("hooks", {}).get(event, [])
        )

    if tool in PLUGINS:
        return bool(s.get("enabledPlugins", {}).get(PLUGINS[tool], False))

    return False


# ── Disable ──────────────────────────────────────────────────────────────────

def disable(tool):
    s     = load(SETTINGS)
    stash = load(STASH)
    mod_s = False

    if tool == "rtk":
        pre = s.get("hooks", {}).get("PreToolUse", [])
        keep, gone = [], []
        for h in pre:
            (gone if _has_keyword(h, "rtk") else keep).append(h)
        if gone:
            s["hooks"]["PreToolUse"] = keep
            stash.setdefault("rtk", {})["PreToolUse"] = gone
            mod_s = True

    elif tool == "headroom":
        hs = stash.setdefault("headroom", {})
        # An explicit official URL overrides 8787 inherited by terminals with an old ~/.bashrc;
        # without it Claude Code started from such a terminal hangs on the stopped proxy
        url = s.setdefault("env", {}).get("ANTHROPIC_BASE_URL", "")
        if "8787" in url:
            hs["ANTHROPIC_BASE_URL"] = url
        s["env"]["ANTHROPIC_BASE_URL"] = "https://api.anthropic.com"
        envl = s.get("autoMode", {}).get("environment", [])
        for i, e in enumerate(envl):
            cut = e
            for rx in HEADROOM_AUTOMODE_CUTS:
                cut = re.sub(rx, "", cut)
            if cut != e:
                hs.setdefault("autoMode", {})[cut] = e
                envl[i] = cut
        lines = _bashrc_lines()
        if any(l in HEADROOM_BASHRC for l in lines):
            BASHRC.write_text("".join(l + "\n" for l in lines if l not in HEADROOM_BASHRC))
        mod_s = True
        sh("systemctl --user disable --now headroom-proxy")

    elif tool == "cbm":
        # CBM MCP is attached per project (.mcp.json); only the hooks are switched globally
        for event in ("PreToolUse", "SessionStart"):
            lst = s.get("hooks", {}).get(event, [])
            keep, gone = [], []
            for h in lst:
                (gone if _has_keyword(h, "cbm-") else keep).append(h)
            if gone:
                s["hooks"][event] = keep
                _add_unique(stash.setdefault("cbm", {}).setdefault(f"hooks_{event}", []), gone)
                mod_s = True

    elif tool in PLUGINS:
        s.setdefault("enabledPlugins", {})[PLUGINS[tool]] = False
        mod_s = True
        if tool == "context-mode":
            lst = s.get("hooks", {}).get("SessionStart", [])
            keep, gone = [], []
            for h in lst:
                (gone if _has_keyword(h, "context-mode") else keep).append(h)
            if gone:
                s["hooks"]["SessionStart"] = keep
                _add_unique(stash.setdefault("context-mode", {}).setdefault("hooks_SessionStart", []), gone)

    if mod_s:  save(SETTINGS, s)
    save(STASH, stash)
    return mod_s


# ── Enable ───────────────────────────────────────────────────────────────────

def enable(tool):
    s     = load(SETTINGS)
    stash = load(STASH)
    saved = stash.get(tool, DEFAULTS.get(tool, {}))
    mod_s = False

    if tool == "rtk":
        pre = s.setdefault("hooks", {}).setdefault("PreToolUse", [])
        if not any(_has_keyword(h, "rtk") for h in pre):
            pre.extend(saved.get("PreToolUse", DEFAULTS["rtk"]["PreToolUse"]))
            mod_s = True

    elif tool == "headroom":
        url = saved.get("ANTHROPIC_BASE_URL", "http://127.0.0.1:8787")
        s.setdefault("env", {})["ANTHROPIC_BASE_URL"] = url
        envl = s.get("autoMode", {}).get("environment", [])
        for cut, orig in saved.get("autoMode", {}).items():
            if cut in envl:
                envl[envl.index(cut)] = orig
        lines = _bashrc_lines()
        missing = [l for l in HEADROOM_BASHRC if l not in lines]
        if missing:
            BASHRC.write_text("".join(l + "\n" for l in lines + missing))
        mod_s = True
        sh("systemctl --user enable --now headroom-proxy")

    elif tool == "cbm":
        for event in ("PreToolUse", "SessionStart"):
            entries = saved.get(f"hooks_{event}", DEFAULTS["cbm"].get(f"hooks_{event}", []))
            if _add_unique(s.setdefault("hooks", {}).setdefault(event, []), entries):
                mod_s = True

    elif tool in PLUGINS:
        s.setdefault("enabledPlugins", {})[PLUGINS[tool]] = True
        mod_s = True
        if tool == "context-mode":
            entries = saved.get("hooks_SessionStart", DEFAULTS["context-mode"]["hooks_SessionStart"])
            _add_unique(s.setdefault("hooks", {}).setdefault("SessionStart", []), entries)

    if mod_s:  save(SETTINGS, s)
    stash.pop(tool, None)
    save(STASH, stash)
    return mod_s


# ── Normalize ────────────────────────────────────────────────────────────────

def normalize():
    """Undoes third-party installers: duplicate hooks, global MCP entries,
    standalone Caveman hooks. Idempotent. Returns the list of fixes made."""
    fixes = []
    s = load(SETTINGS)
    mod_s = False
    for event, lst in s.get("hooks", {}).items():
        keep = []
        for h in lst:
            if h in keep:
                fixes.append(f"settings.json: removed duplicate hook {event}")
                continue
            if any(_has_keyword(h, kw) for kw in LEGACY_CAVEMAN_HOOKS):
                fixes.append(f"settings.json: removed standalone Caveman hook ({event})")
                continue
            keep.append(h)
        if len(keep) != len(lst):
            s["hooks"][event] = keep
            mod_s = True
    if mod_s:
        save(SETTINGS, s)

    for path in (CLAUDE_JSON, CLAUDE_MCP_JSON):
        data = load(path)
        mcp = data.get("mcpServers", {})
        gone = [k for k in FORBIDDEN_GLOBAL_MCP if mcp.pop(k, None) is not None]
        if gone:
            save(path, data)
            fixes.append(f"{path}: removed global MCP registration {', '.join(gone)}")
    return fixes


def print_normalize():
    fixes = normalize()
    for f in fixes:
        print(f"  {f}")
    if not fixes:
        print("  Configuration normalized, nothing to fix")
    print()


# ── Status display ───────────────────────────────────────────────────────────

GREEN = "\033[32m"
RED   = "\033[31m"
YELLOW= "\033[33m"
DIM   = "\033[2m"
RESET = "\033[0m"


def print_status():
    states = {t: is_on(t) for t in TOOLS}
    stash  = load(STASH)

    print(f"\n{DIM}{'─'*48}{RESET}")
    print("  Token optimization stack")
    print(f"{DIM}{'─'*48}{RESET}")
    for t in TOOLS:
        on    = states[t]
        badge = f"{GREEN}ON {RESET}" if on else f"{RED}OFF{RESET}"
        print(f"  [{badge}]  {LABELS[t]}")
    # markitdown: read-only line (not switched)
    md_ver = "?"
    try:
        import re as _re
        out = sh_out("markitdown --version 2>/dev/null")
        m = _re.search(r"(\d+\.\d+\.\d+)", out)
        if m:
            md_ver = m.group(1)
    except Exception:
        pass
    print(f"  [{DIM}v{md_ver}{RESET}]  markitdown     (reads doc/pdf/...)")
    print(f"{DIM}{'─'*48}{RESET}")
    te = load(TE_CONFIG)
    if te:
        shared = ", ".join(f"{k}={str(v).lower()}" for k, v in sorted(te.items()))
        print(f"  {DIM}te: shared {TE_CONFIG} ({shared}) - not changed by this switch{RESET}")
    mode = stash.get("_mode")
    if mode:
        print(f"  {DIM}mode: {MODE_LABEL.get(mode, mode)}{RESET}")
    keys = [k for k in stash if not k.startswith("_")]
    if keys:
        print(f"  {DIM}stash: {', '.join(keys)}{RESET}")
    print()


# ── Mode switching ───────────────────────────────────────────────────────────

def set_mode(mode):
    if mode not in MODES:
        print(f"Error: unknown mode '{mode}'. Available: {', '.join(MODES)}")
        sys.exit(1)

    normalize()
    cfg = MODES[mode]
    for t in cfg["off"]:
        if is_on(t):
            disable(t)
            suffix = "  (restart Claude Code)" if t in NEEDS_RESTART else ""
            print(f"  {t}: OFF{suffix}")
        else:
            print(f"  {t}: already OFF")
    for t in cfg["on"]:
        if not is_on(t):
            enable(t)
            suffix = "  (restart Claude Code)" if t in NEEDS_RESTART else ""
            print(f"  {t}: ON{suffix}")
        else:
            print(f"  {t}: already ON")

    stash = load(STASH)
    stash["_mode"] = mode
    save(STASH, stash)

    print()
    print_status()


# ── Version checking ─────────────────────────────────────────────────────────

def _fetch_json(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "stack-toggle/1.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            return json.loads(r.read())
    except Exception:
        return {}


def get_current_version(tool):
    """Returns the current version string, or '?' if unknown."""
    try:
        if tool == "rtk":
            out = sh_out("rtk --version 2>/dev/null")
            m = re.search(r"(\d+\.\d+\.\d+)", out)
            return m.group(1) if m else "?"

        if tool == "headroom":
            out = sh_out("headroom --version 2>/dev/null")
            m = re.search(r"(\d+\.\d+\.\d+)", out)
            return m.group(1) if m else "?"

        if tool == "cbm":
            out = sh_out("codebase-memory-mcp --version 2>/dev/null")
            m = re.search(r"(\d+\.\d+\.\d+)", out)
            return m.group(1) if m else "?"

        if tool in PLUGINS:
            entries = load(INSTALLED_PLUGINS).get("plugins", {}).get(PLUGINS[tool], [])
            if not entries or not Path(entries[0].get("installPath", "")).exists():
                return "BROKEN"
            if tool == "caveman":
                return entries[0].get("gitCommitSha", "?")[:12]
            return entries[0].get("version", "?")

    except Exception:
        pass
    return "?"


def get_latest_version(tool):
    """Returns (latest_str, download_url|None)."""
    r = REPOS.get(tool)
    if not r:
        return "?", None

    try:
        if tool in ("rtk", "cbm"):
            d = _fetch_json(r["api"])
            tag = d.get("tag_name", "?").lstrip("v")
            # Only RTK needs the asset URL; the Codex part installs CBM by pin
            asset_name = r.get("asset")
            url = next(
                (a["browser_download_url"] for a in d.get("assets", []) if a["name"] == asset_name),
                None
            )
            return tag, url

        if tool == "headroom":
            d = _fetch_json(r["api"])
            # Take the latest release (semver order)
            releases = list(d.get("releases", {}).keys())
            releases = [v for v in releases if re.match(r"^\d+\.\d+\.\d+$", v)]
            releases.sort(key=lambda v: [int(x) for x in v.split(".")])
            return (releases[-1] if releases else "?"), None

        if tool in ("context-mode", "ponytail"):
            d = _fetch_json(r["api"])
            tag = d.get("tag_name", "?").lstrip("v")
            return tag, None

        if tool == "te":
            return _fetch_json(r["api"]).get("version", "?"), None

        if tool == "caveman":
            d = _fetch_json(r["api"])
            sha = d.get("sha", "?")[:12]
            date = d.get("commit", {}).get("author", {}).get("date", "")[:10]
            return f"{sha} ({date})", None

    except Exception:
        pass
    return "?", None


def _vt(text):
    """(major, minor, patch) from a version string; () if none."""
    m = re.search(r"(\d+)\.(\d+)\.(\d+)", text or "")
    return tuple(map(int, m.groups())) if m else ()


def codex_cbm_pin():
    """CBM version pinned in BINARY_SPECS of the Codex manage.py; () if not found.
    The file is read as text, not imported."""
    try:
        text = CODEX_MANAGE.read_text(encoding="utf-8")
    except OSError:
        return ()
    m = re.search(r'"codebase-memory-mcp":\s*\{\s*"version":\s*\((\d+),\s*(\d+),\s*(\d+)\)', text)
    return tuple(map(int, m.groups())) if m else ()


def shared_node_busy():
    """Processes already changing the shared CBM/RTK: CBM updater or installer, Codex manage.py."""
    r = subprocess.run(
        ["pgrep", "-af", r"codebase-memory-mcp (update|install)|token-stack/scripts/manage\.py (install|bootstrap)"],
        capture_output=True, text=True)
    return r.stdout.strip()


def print_update_table():
    """Prints the version table. Returns the tools that need an update."""
    UPDATE_TOOLS = ["rtk", "headroom", "cbm", "context-mode", "caveman", "ponytail", "te"]
    needs_update = []

    print(f"\n{DIM}{'─'*70}{RESET}")
    print("  Stack tool versions")
    print(f"{DIM}{'─'*70}{RESET}")
    fmt = "  {:<16} {:<16} {:<20} {}"
    print(fmt.format("Tool", "Current", "Latest", "Status"))
    print(f"  {DIM}{'─'*66}{RESET}")

    for tool in UPDATE_TOOLS:
        current = get_current_version(tool)
        latest, _ = get_latest_version(tool)

        if current == "BROKEN":
            status = f"{RED}BROKEN - reinstall needed{RESET}"
            needs_update.append(tool)
        elif tool == "cbm":
            # The shared CBM target is the Codex pin, not the latest GitHub release
            pin = codex_cbm_pin()
            pin_s = ".".join(map(str, pin))
            if not pin or current == "?":
                status = f"{DIM}unknown (Codex pin: {pin_s or 'not found'}){RESET}"
            elif _vt(current) < pin:
                status = f"{YELLOW}below Codex pin {pin_s}{RESET}"
                needs_update.append(tool)
            elif _vt(latest) > pin:
                status = f"{DIM}= Codex pin {pin_s}; a new release is pinned in the Codex part{RESET}"
            else:
                status = f"{GREEN}up to date (Codex pin {pin_s}){RESET}"
        elif current == "?" or latest == "?":
            status = f"{DIM}unknown{RESET}"
        elif tool == "caveman":
            # Caveman: compare the SHA only
            cur_sha = current[:12]
            lat_sha = latest[:12]
            if cur_sha == lat_sha:
                status = f"{GREEN}up to date{RESET}"
            else:
                status = f"{YELLOW}update available{RESET}"
                needs_update.append(tool)
        else:
            # Semver comparison
            def parse_v(v):
                try:
                    return [int(x) for x in v.split(".")]
                except Exception:
                    return [0]
            cur_v = parse_v(current)
            lat_v = parse_v(latest)
            if cur_v >= lat_v:
                status = f"{GREEN}up to date{RESET}"
            else:
                status = f"{YELLOW}update available{RESET}"
                needs_update.append(tool)

        print(fmt.format(tool, current, latest, status))

    print(f"{DIM}{'─'*70}{RESET}")

    # markitdown separately (not switched, but shown)
    try:
        md_cur_raw = sh_out("markitdown --version 2>/dev/null")
        md_cur_m = re.search(r"(\d+\.\d+\.\d+)", md_cur_raw)
        md_cur = md_cur_m.group(1) if md_cur_m else "?"
    except Exception:
        md_cur = "?"
    md_d = _fetch_json("https://pypi.org/pypi/markitdown/json")
    md_lat = md_d.get("info", {}).get("version", "?")
    md_status = f"{GREEN}up to date{RESET}"
    if md_cur != "?" and md_lat != "?":
        def parse_v(v):
            try:
                return [int(x) for x in v.split(".")]
            except Exception:
                return [0]
        if parse_v(md_cur) < parse_v(md_lat):
            md_status = f"{YELLOW}update available{RESET}"
            needs_update.append("markitdown")
    print(fmt.format("markitdown (*)", md_cur, md_lat, md_status))
    print(f"  {DIM}(*) markitdown is managed outside toggle.py: uv tool upgrade markitdown{RESET}")
    print()

    return needs_update


# ── Update apply ─────────────────────────────────────────────────────────────

def _download_github_binary(tool, download_url):
    """Downloads a tar.gz from GitHub and replaces the binary."""
    r = REPOS[tool]
    bin_path = Path(r["binary"]).expanduser()
    asset    = r["asset"]
    bin_name = Path(asset.replace(".tar.gz", "").replace("-linux-amd64", "").replace("-x86_64-unknown-linux-musl", ""))

    print(f"  Downloading {asset}...")
    with tempfile.TemporaryDirectory() as tmpdir:
        tar_path = os.path.join(tmpdir, asset)
        try:
            req = urllib.request.Request(download_url, headers={"User-Agent": "stack-toggle/1.0"})
            with urllib.request.urlopen(req, timeout=60) as resp, open(tar_path, "wb") as f:
                shutil.copyfileobj(resp, f)
        except Exception as e:
            print(f"  ERROR downloading: {e}")
            return False

        print(f"  Unpacking...")
        try:
            with tarfile.open(tar_path, "r:gz") as tar:
                tar.extractall(tmpdir)
        except Exception as e:
            print(f"  ERROR unpacking: {e}")
            return False

        # Find the binary among the unpacked files
        found = None
        for root, dirs, files in os.walk(tmpdir):
            for f in files:
                fp = os.path.join(root, f)
                # Binary name: rtk or codebase-memory-mcp
                if f == bin_path.name and os.access(fp, os.X_OK):
                    found = fp
                    break
            if found:
                break

        if not found:
            # Fall back to any executable file
            for root, dirs, files in os.walk(tmpdir):
                for f in files:
                    fp = os.path.join(root, f)
                    if fp != tar_path and os.access(fp, os.X_OK):
                        found = fp
                        break
                if found:
                    break

        if not found:
            print(f"  ERROR: binary not found in the archive")
            return False

        print(f"  Installing {bin_path}...")
        try:
            shutil.copy2(found, str(bin_path))
            os.chmod(str(bin_path), 0o755)
        except Exception as e:
            print(f"  ERROR installing: {e}")
            return False

    return True


def apply_cbm_update():
    """CBM is shared with Codex; its version is the Codex pin (docs/STACK.md, shared machine).
    Claude never downloads CBM itself and never runs `codebase-memory-mcp update` or
    `install` (the latter rewrites the configuration of every agent)."""
    pin = codex_cbm_pin()
    if not pin:
        print(f"  cbm: no pin in {CODEX_MANAGE}; the Codex part performs the update")
        return False
    pin_s = ".".join(map(str, pin))
    current = get_current_version("cbm")
    if _vt(current) >= pin:
        print(f"  cbm: {current} is not below Codex pin {pin_s} - the shared binary stays.")
        print(f"  A new version is pinned in BINARY_SPECS of {CODEX_MANAGE},")
        print("  then manage.py install and doctor, then toggle.py normalize here.")
        return True
    busy = shared_node_busy()
    if busy:
        print(f"  cbm: the shared machine is already updating, retry later:\n    {busy}")
        return False
    print(f"  cbm: {current} is below Codex pin {pin_s}; installing the pinned build via Codex bootstrap")
    print("  (SHA-256 checked; RTK is raised to its pin too if lower)")
    ret = subprocess.run([sys.executable, "-I", str(CODEX_MANAGE), "bootstrap"])
    if ret.returncode != 0:
        print("  ERROR: Codex manage.py bootstrap")
        return False
    print_normalize()
    print("  cbm: updated  (restart Claude Code and Codex; Codex check: manage.py doctor)")
    return True


def apply_update(tool):
    """Updates one tool. Returns True on success."""
    r = REPOS.get(tool)

    if tool == "markitdown":
        print(f"  Updating markitdown...")
        ret = subprocess.run("uv tool upgrade markitdown", shell=True)
        if ret.returncode == 0:
            print(f"  markitdown: updated")
            return True
        print(f"  ERROR updating markitdown")
        return False

    if not r:
        print(f"  {tool}: not supported by update apply")
        return False

    method = r["method"]

    if tool == "cbm":
        return apply_cbm_update()

    if method == "github_binary":
        _, url = get_latest_version(tool)
        if not url:
            print(f"  {tool}: no download URL")
            return False
        ok = _download_github_binary(tool, url)
        if ok:
            print(f"  {tool}: updated")
        return ok

    if method == "uv_tool":
        pkg = r["pkg"]
        # headroom needs the [proxy] extras and socksio (SOCKS proxy in the environment)
        install_spec = f"'{pkg}[proxy]' --with socksio" if pkg == "headroom-ai" else pkg
        print(f"  Updating {pkg}...")
        ret = subprocess.run(f"uv tool install {install_spec} --force", shell=True)
        if ret.returncode != 0:
            print(f"  ERROR: uv tool upgrade {pkg}")
            return False
        if "post" in r:
            print(f"  Restarting the service...")
            subprocess.run(r["post"], shell=True)
        print(f"  {tool}: updated")
        return True

    if method == "claude_plugin":
        plugin = PLUGINS[tool]
        marketplace = plugin.split("@")[1]
        action = "update" if get_current_version(tool) != "BROKEN" else "install"
        print(f"  {tool}: claude plugin {action} {plugin}...")
        ret = subprocess.run(
            f"claude plugin marketplace update {marketplace} && claude plugin {action} {plugin}",
            shell=True)
        if ret.returncode == 0:
            print(f"  {tool}: updated  (restart Claude Code)")
            return True
        print(f"  ERROR: claude plugin {action} {plugin}")
        return False

    return False


def cmd_update(args):
    """Handler of update [apply [tool|all]]."""
    if not args or args[0] == "check":
        needs = print_update_table()
        if needs:
            print(f"  {YELLOW}Need an update:{RESET} {', '.join(needs)}")
            print(f"  To apply: python3 {__file__} update apply all")
            shared = [t for t in needs if t in SHARED_BINARIES]
            if shared:
                print(f"  Shared with Codex ({', '.join(shared)}) - only explicitly: update apply <tool>")
        else:
            print(f"  {GREEN}All tools are up to date{RESET}")
        return

    if args[0] == "apply":
        targets_arg = args[1] if len(args) > 1 else "all"

        if targets_arg == "all":
            # Print the table first, then update only tools with an update
            needs = print_update_table()
            skipped = [t for t in needs if t in SHARED_BINARIES]
            targets = [t for t in needs if t not in SHARED_BINARIES]
            if skipped:
                print(f"  {YELLOW}Skipped, shared with Codex:{RESET} {', '.join(skipped)} "
                      f"- only explicitly: update apply <tool> (docs/STACK.md)")
            if not targets:
                print(f"  {GREEN}Nothing to update as part of all{RESET}")
                return
        else:
            targets = [targets_arg]

        print(f"\n  Updating: {', '.join(targets)}\n")
        results = {}
        for t in targets:
            results[t] = apply_update(t)

        print(f"\n{DIM}{'─'*48}{RESET}")
        for t, ok in results.items():
            badge = f"{GREEN}OK{RESET}" if ok else f"{RED}ERROR{RESET}"
            print(f"  [{badge}]  {t}")
        print(f"{DIM}{'─'*48}{RESET}\n")
        return

    print(f"Error: unknown argument '{args[0]}'. Use: update [check] | update apply [tool|all]")
    sys.exit(1)


# ── Entry point ──────────────────────────────────────────────────────────────

def main():
    args = [a.lower() for a in sys.argv[1:]]

    if not args or args[0] == "status":
        print_status()
        return

    action = args[0]

    if action == "update":
        cmd_update(args[1:])
        return

    if action == "normalize":
        print_normalize()
        return

    if action == "mode":
        if len(args) < 2:
            print(f"Error: give a mode. Available: {', '.join(MODES)}")
            sys.exit(1)
        set_mode(args[1])
        return

    if action not in ("on", "off"):
        print(f"Error: unknown action '{action}'. Use: on | off | mode | status | update | normalize")
        sys.exit(1)

    if len(args) < 2:
        print("Error: give a tool. Example: off headroom")
        sys.exit(1)

    targets = TOOLS if args[1] == "all" else [args[1]]
    for t in targets:
        if t not in TOOLS:
            print(f"Error: unknown tool '{t}'. Available: {', '.join(TOOLS)}")
            sys.exit(1)

    for t in targets:
        current = is_on(t)
        if action == "off" and current:
            disable(t)
            suffix = "  (restart Claude Code)" if t in NEEDS_RESTART else ""
            print(f"  {t}: OFF{suffix}")
        elif action == "on" and not current:
            enable(t)
            suffix = "  (restart Claude Code)" if t in NEEDS_RESTART else ""
            print(f"  {t}: ON{suffix}")
        else:
            state = "ON" if current else "OFF"
            print(f"  {t}: already {state} - unchanged")

    print()
    print_status()


if __name__ == "__main__":
    main()
