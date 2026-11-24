#!/usr/bin/env python3
"""Minimal toggle.py checks in a temporary HOME: the real ~/.claude, ~/.codex and
~/.tokeneconomizer stay untouched. Run: python3 -B skills/stack/test_toggle.py"""
import importlib.util, json, os, subprocess, sys, tempfile, unittest
from pathlib import Path
from unittest import mock

TOGGLE = Path(__file__).resolve().with_name("toggle.py")
TE_KEY = "tokeneconomizer@tokeneconomizer"


class ToggleTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="stack test ")
        self.addCleanup(tmp.cleanup)
        self.home = Path(tmp.name)
        (self.home / ".claude/skills/stack").mkdir(parents=True)
        (self.home / ".claude/settings.json").write_text(json.dumps(
            {"enabledPlugins": {TE_KEY: True, "caveman@caveman": True}}))
        (self.home / ".tokeneconomizer").mkdir()
        (self.home / ".tokeneconomizer/config.json").write_text('{"shadow": true, "toolprune": "propose"}')
        (self.home / ".codex").mkdir()
        (self.home / ".codex/config.toml").write_text('[plugins."tokeneconomizer@tokeneconomizer"]\nenabled = true\n')
        self.untouched = {p: p.read_bytes() for p in
                          (self.home / ".tokeneconomizer/config.json", self.home / ".codex/config.toml")}

    def run_toggle(self, *args):
        env = dict(os.environ, HOME=str(self.home), PYTHONDONTWRITEBYTECODE="1")
        return subprocess.run([sys.executable, str(TOGGLE), *args], env=env,
                              capture_output=True, text=True, check=True).stdout

    def plugins(self):
        return json.loads((self.home / ".claude/settings.json").read_text())["enabledPlugins"]

    def test_te_switch_is_claude_only(self):
        self.run_toggle("off", "te")
        self.assertIs(self.plugins()[TE_KEY], False)
        self.assertIs(self.plugins()["caveman@caveman"], True)
        out = self.run_toggle("on", "te")
        self.assertIs(self.plugins()[TE_KEY], True)
        for path, data in self.untouched.items():
            self.assertEqual(path.read_bytes(), data, path)
        self.assertNotIn("%", out)
        self.assertIn("shadow=true", out)

    def test_cbm_at_codex_pin_runs_nothing(self):
        spec = importlib.util.spec_from_file_location("toggle", TOGGLE)
        toggle = importlib.util.module_from_spec(spec)
        with mock.patch.dict(os.environ, HOME=str(self.home)):
            spec.loader.exec_module(toggle)
        manage = self.home / "manage.py"
        manage.write_text('"codebase-memory-mcp": {\n    "version": (0, 12, 1),\n')
        with mock.patch.object(toggle, "CODEX_MANAGE", manage), \
             mock.patch.object(toggle, "get_current_version", return_value="0.12.1"), \
             mock.patch.object(toggle.subprocess, "run") as run:
            self.assertEqual(toggle.codex_cbm_pin(), (0, 12, 1))
            self.assertTrue(toggle.apply_cbm_update())
            run.assert_not_called()

    def hooks(self):
        return json.loads((self.home / ".claude/settings.json").read_text()).get("hooks", {})

    def test_on_skips_hooks_without_scripts(self):
        self.assertIn("cbm: OFF", self.run_toggle("on", "cbm"))
        self.run_toggle("on", "context-mode")
        self.assertEqual(self.hooks().get("PreToolUse", []), [])
        self.assertEqual(self.hooks().get("SessionStart", []), [])
        hooks = self.home / ".claude/hooks"
        hooks.mkdir()
        gate = hooks / "cbm-code-discovery-gate"
        gate.write_text("#!/bin/sh\n")
        self.run_toggle("on", "cbm")
        self.assertEqual(self.hooks().get("PreToolUse", []), [])

        gate.chmod(0o755)
        self.run_toggle("on", "cbm")
        self.assertEqual(len(self.hooks()["PreToolUse"]), 1)
        self.assertEqual(self.hooks().get("SessionStart", []), [])

        for name in ("cbm-session-reminder", "context-mode-cache-heal.mjs"):
            script = hooks / name
            script.write_text("#!/bin/sh\n")
            script.chmod(0o755)
        self.run_toggle("on", "cbm")
        self.run_toggle("on", "context-mode")
        self.assertEqual(len(self.hooks()["PreToolUse"]), 1)
        self.assertEqual(len(self.hooks()["SessionStart"]), 5)

    def test_retries_custom_stashed_hook(self):
        settings = self.home / ".claude/settings.json"
        hooks = self.home / ".claude/hooks"
        hooks.mkdir()
        script = hooks / "cbm-custom"
        custom = {"matcher": "resume", "hooks": [
            {"type": "command", "command": f'"{script}" --custom', "timeout": 3},
        ]}
        config = json.loads(settings.read_text())
        config["hooks"] = {"SessionStart": [custom]}
        settings.write_text(json.dumps(config))
        self.run_toggle("off", "cbm")
        self.run_toggle("on", "cbm")
        self.assertEqual(self.hooks()["SessionStart"], [])

        script.write_text("#!/bin/sh\n")
        script.chmod(0o755)
        self.run_toggle("on", "cbm")
        self.run_toggle("on", "cbm")
        self.assertEqual(self.hooks()["SessionStart"], [custom])

    def test_reminder_requires_cbm_registration(self):
        reminder = TOGGLE.parents[2] / "hooks/cbm-session-reminder.sh"
        project = self.home / 'project "quoted"'
        project.mkdir()
        payload = json.dumps({"cwd": str(project)}, indent=2)

        def run():
            return subprocess.run([str(reminder)], input=payload, text=True,
                                  capture_output=True, check=True).stdout

        self.assertEqual(run(), "")
        config = project / ".mcp.json"
        config.write_text('{"mcpServers":{"unrelated":{"args":["codebase-memory-mcp"]}}}')
        self.assertEqual(run(), "")
        config.write_text("{broken")
        self.assertEqual(run(), "")
        config.write_text('{"mcpServers":{"codebase-memory-mcp":{"command":"codebase-memory-mcp"}}}')
        self.assertIn("start code exploration with index_status", run())


if __name__ == "__main__":
    unittest.main()
