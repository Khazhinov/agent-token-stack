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
        tmp = tempfile.TemporaryDirectory()
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


if __name__ == "__main__":
    unittest.main()
