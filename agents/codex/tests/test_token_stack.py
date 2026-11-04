import json
import os
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
MANAGE = REPO / "skills/token-stack/scripts/manage.py"


class TokenStackTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name)
        codex = self.home / ".codex"
        codex.mkdir(parents=True)
        (codex / "config.toml").write_text(
            'model = "keep-me"\n\n[projects."/work"]\ntrust_level = "trusted"\n',
            encoding="utf-8",
        )
        (codex / "hooks.json").write_text(
            json.dumps(
                {
                    "hooks": {
                        "SessionStart": [
                            {"hooks": [{"type": "command", "command": "keep-me"}]}
                        ]
                    }
                }
            ),
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp.cleanup()

    def run_manage(self, *args):
        # The real repository may have local/ rules; tests start without them.
        return subprocess.run(
            [sys.executable, str(MANAGE), "--home", str(self.home), *args],
            text=True,
            capture_output=True,
            check=True,
            env={**os.environ, "TOKEN_STACK_LOCAL": str(self.home / "no-local")},
        )

    def test_install_is_idempotent_and_preserves_user_config(self):
        self.run_manage("install")
        config_path = self.home / ".codex/config.toml"
        hooks_path = self.home / ".codex/hooks.json"
        first_config = config_path.read_bytes()
        first_hooks = hooks_path.read_bytes()

        config = tomllib.loads(first_config.decode())
        self.assertEqual(config["model"], "keep-me")
        self.assertEqual(config["projects"]["/work"]["trust_level"], "trusted")
        self.assertEqual(list(config["mcp_servers"]), ["codebase-memory"])
        self.assertEqual(config["tool_output_token_limit"], 10000)
        self.assertEqual(config["default_permissions"], "workspace-only")
        self.assertEqual(config["approval_policy"], "on-request")
        self.assertEqual(config["approvals_reviewer"], "auto_review")
        self.assertIn("explicitly requested", config["auto_review"]["extra_policy"])
        self.assertEqual(config["permissions"]["workspace-only"]["extends"], ":workspace")
        self.assertNotIn("filesystem", config["permissions"]["workspace-only"])
        hooks = json.loads(first_hooks)
        self.assertIn("keep-me", json.dumps(hooks))
        rtk = hooks["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
        # Stable path: a repository move must not change the trusted hook hash.
        self.assertEqual(
            rtk, f"python3 {self.home}/.agents/skills/token-stack/scripts/rtk-codex-hook.py"
        )
        self.assertTrue((self.home / ".codex/AGENTS.md").is_symlink())
        self.assertTrue((self.home / ".agents/skills/token-stack").is_symlink())

        self.run_manage("install")
        self.assertEqual(config_path.read_bytes(), first_config)
        self.assertEqual(hooks_path.read_bytes(), first_hooks)

    def test_codex_mirrors_claude_read_denies(self):
        (self.home / ".claude").mkdir()
        (self.home / ".claude/settings.json").write_text(json.dumps({
            "permissions": {"deny": ["Read(~/.secrets/**)", "Read(//srv/app/.env)",
                                     "Edit(~/.secrets/**)", "Bash(*secret*)", "Read(**/*.pem)",
                                     "Read(/creds/**)", "Read(.env)"]},
            "sandbox": {"filesystem": {"denyRead": ["~/.secrets/**", "/opt/key", "./local.env"]}},
        }), encoding="utf-8")
        self.run_manage("install")
        config = tomllib.loads((self.home / ".codex/config.toml").read_text())
        fs = config["permissions"]["workspace-only"]["filesystem"]
        self.assertEqual(fs, {"~/.secrets": "deny", "/srv/app/.env": "deny", "~/.claude/creds": "deny",
                              "/opt/key": "deny", "~/.claude/local.env": "deny"})

    def test_local_rules_are_appended_to_global_agents_md(self):
        local = self.home / "local"
        (local / "codex").mkdir(parents=True)
        (local / "codex/AGENTS.md").write_text("## This machine\n\nlocal rule\n", encoding="utf-8")
        subprocess.run([sys.executable, str(MANAGE), "--home", str(self.home), "install"],
                       text=True, capture_output=True, check=True,
                       env={**os.environ, "TOKEN_STACK_LOCAL": str(local)})
        guidance = self.home / ".codex/AGENTS.md"
        self.assertFalse(guidance.is_symlink())
        text = guidance.read_text(encoding="utf-8")
        self.assertTrue(text.startswith((REPO / "AGENTS.md").read_text(encoding="utf-8").rstrip()))
        self.assertTrue(text.endswith("local rule\n"))

    def test_components_toggle_independently(self):
        self.run_manage("install")
        for component in ("rtk", "cbm", "native"):
            self.run_manage("off", component)
            status = json.loads(self.run_manage("status", "--json").stdout)
            names = {"rtk": "RTK", "cbm": "Codebase Memory", "native": "Native limits"}
            self.assertFalse(status[names[component]]["enabled"])
            self.run_manage("on", component)

        self.run_manage("off", "all")
        status = json.loads(self.run_manage("status", "--json").stdout)
        self.assertFalse(status["RTK"]["enabled"])
        self.assertFalse(status["Codebase Memory"]["enabled"])
        self.assertFalse(status["Native limits"]["enabled"])
        self.assertTrue(status["Global guidance"]["enabled"])
        self.assertTrue(status["Token Stack skill"]["enabled"])
        config = tomllib.loads((self.home / ".codex/config.toml").read_text())
        self.assertEqual(config["default_permissions"], "workspace-only")
        self.assertEqual(config["approvals_reviewer"], "auto_review")

    def test_doctor_checks_real_hook(self):
        self.run_manage("install")
        result = self.run_manage("doctor")
        self.assertIn("DOCTOR: OK", result.stdout)
        self.assertIn("rtk rg --files", result.stdout)

    def test_te_toggle_only_changes_codex_plugin(self):
        self.run_manage("install")
        path = self.home / ".codex/config.toml"
        path.write_text(path.read_text() + '\n[plugins."tokeneconomizer@tokeneconomizer"]\nenabled = true\n')
        self.run_manage("off", "te")
        self.assertFalse(tomllib.loads(path.read_text())["plugins"]["tokeneconomizer@tokeneconomizer"]["enabled"])
        self.run_manage("on", "te")
        self.assertTrue(tomllib.loads(path.read_text())["plugins"]["tokeneconomizer@tokeneconomizer"]["enabled"])

    def test_install_preserves_tables_inserted_inside_cbm_markers(self):
        self.run_manage("install")
        path = self.home / ".codex/config.toml"
        text = path.read_text().replace(
            "# <<< codex-token-stack cbm <<<",
            '[plugins."tokeneconomizer@tokeneconomizer"]\nenabled = true\n\n'
            '[marketplaces.tokeneconomizer]\nsource = "https://example.test/TokenEconomizer"\n'
            "# <<< codex-token-stack cbm <<<",
        )
        path.write_text(text)
        self.run_manage("install")
        config = tomllib.loads(path.read_text())
        self.assertTrue(config["plugins"]["tokeneconomizer@tokeneconomizer"]["enabled"])
        self.assertEqual(config["marketplaces"]["tokeneconomizer"]["source"], "https://example.test/TokenEconomizer")


if __name__ == "__main__":
    unittest.main()
