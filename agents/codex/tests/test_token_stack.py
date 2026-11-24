import json
import os
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest.mock import patch


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

        self.assertNotIn("extra_policy", config.get("auto_review", {}))
        self.assertEqual(config["model_auto_compact_token_limit"], 160000)
        self.assertEqual(config["permissions"]["workspace-only"]["extends"], ":workspace")
        self.assertIs(config["permissions"]["workspace-only"]["network"]["enabled"], True)
        self.assertEqual(config["permissions"]["workspace-only"]["filesystem"],
                         {"~/.cache/herdr-orch": "write", "~/.cache/herdr-agent-kit": "write"})
        self.assertIs(config["features"]["daemon_auto_start"], False)
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
        self.assertEqual(fs, {"~/.cache/herdr-orch": "write", "~/.cache/herdr-agent-kit": "write",
                              "~/.secrets": "deny", "/srv/app/.env": "deny", "~/.claude/creds": "deny",
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

    def test_install_retains_codex_only_read_denies(self):
        self.run_manage("install")
        path = self.home / ".codex/config.toml"
        path.write_text(path.read_text().replace('[permissions.workspace-only.filesystem]\n',
                        '[permissions.workspace-only.filesystem]\n"~/.private/legacy.env" = "deny"\n'))
        self.run_manage("install")
        self.run_manage("install")
        config = tomllib.loads(path.read_text())
        self.assertEqual(config["permissions"]["workspace-only"]["filesystem"]["~/.private/legacy.env"], "deny")

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
        self.assertNotIn("model_auto_compact_token_limit", config)

    def test_doctor_checks_real_hook(self):
        self.run_manage("install")
        # The real hook runs below. Codex probes need a test double because the
        # host may have no Codex executable or disallow nested sandbox startup.
        codex = self.home / "codex"
        codex.write_text(
            '#!/bin/sh\n'
            'test -f "$CODEX_HOME/config.toml" || exit 1\n'
            'case "$*" in\n'
            '  "--strict-config app-server --print-startup-config"|"sandbox -- /bin/true") exit 0 ;;\n'
            '  *) exit 1 ;;\n'
            'esac\n'
        )
        codex.chmod(0o755)
        with patch.dict(os.environ, PATH=f"{self.home}{os.pathsep}{os.environ['PATH']}"):
            result = self.run_manage("doctor")
        self.assertIn("DOCTOR: OK", result.stdout)
        self.assertIn("rtk rg --files", result.stdout)

    def test_skill_backup_is_preserved_outside_discovery(self):
        old = self.home / ".agents/skills/token-stack.pre-agent-token-stack"
        old.mkdir(parents=True)
        (old / "SKILL.md").write_text("old skill\n")
        self.run_manage("install")
        self.run_manage("install")
        self.assertFalse(old.exists())
        saved = self.home / ".agents/skill-backups" / old.name / "SKILL.md"
        self.assertEqual(saved.read_text(), "old skill\n")

    def test_te_toggle_only_changes_codex_plugin(self):
        self.run_manage("install")
        path = self.home / ".codex/config.toml"
        path.write_text(path.read_text() + '\n[plugins."tokeneconomizer@tokeneconomizer"]\n'
                        'enabled = true # preserve comment\n[notice]\nhide_rate_limit_model_nudge = true\n')
        self.run_manage("off", "te")
        self.assertFalse(tomllib.loads(path.read_text())["plugins"]["tokeneconomizer@tokeneconomizer"]["enabled"])
        self.assertTrue(tomllib.loads(path.read_text())["notice"]["hide_rate_limit_model_nudge"])
        self.assertIn("# preserve comment", path.read_text())
        self.run_manage("on", "te")
        self.assertTrue(tomllib.loads(path.read_text())["plugins"]["tokeneconomizer@tokeneconomizer"]["enabled"])

    def test_local_effort_and_launcher_preserve_user_overrides(self):
        local = self.home / "local"
        (local / "codex").mkdir(parents=True)
        (local / "codex/settings.json").write_text(json.dumps({
            "reasoning_effort": "medium", "trust_all_directories": True,
        }))
        binary = self.home / ".codex/packages/standalone/current/bin/codex"
        binary.parent.mkdir(parents=True)
        binary.write_text("#!/bin/sh\nexit 0\n")
        binary.chmod(0o755)
        launcher = self.home / ".local/bin/codex"
        launcher.parent.mkdir(parents=True)
        launcher.symlink_to(binary)
        path = self.home / ".codex/config.toml"
        path.write_text('model_reasoning_effort = "high"\n' + path.read_text()
                        + '\n[profiles.deep]\nmodel_reasoning_effort = "high"\n')
        env = {**os.environ, "TOKEN_STACK_LOCAL": str(local)}
        for _ in range(2):
            subprocess.run([sys.executable, str(MANAGE), "--home", str(self.home), "install"],
                           text=True, capture_output=True, check=True, env=env)
        config = tomllib.loads(path.read_text())
        self.assertEqual(config["model_reasoning_effort"], "medium")
        self.assertEqual(config["profiles"]["deep"]["model_reasoning_effort"], "high")
        self.assertEqual(config["model"], "keep-me")
        self.assertEqual(launcher.resolve(), (REPO / "scripts/codex-launch.py").resolve())
        self.assertEqual(launcher.with_name("codex.pre-token-stack").resolve(), binary)

    def test_launcher_quotes_directory_and_preserves_arguments(self):
        binary = self.home / ".codex/packages/standalone/current/bin/codex"
        binary.parent.mkdir(parents=True)
        binary.write_text('#!/usr/bin/env python3\nimport json,sys\nprint(json.dumps(sys.argv[1:]))\n')
        binary.chmod(0o755)
        cwd = self.home / 'space " quote $(unused) 🚀'
        cwd.mkdir()
        result = subprocess.run(
            [sys.executable, str(REPO / "scripts/codex-launch.py"), "-C", str(cwd),
             "--config", 'model_reasoning_effort="high"', "prompt"],
            capture_output=True, text=True, check=True, env={**os.environ, "HOME": str(self.home)},
        )
        args = json.loads(result.stdout)
        self.assertEqual(args[0], "--no-daemon")
        trust = tomllib.loads(args[2])["projects"]
        self.assertEqual(trust[str(cwd)]["trust_level"], "trusted")
        self.assertIn(f'projects.{json.dumps(str(cwd), ensure_ascii=False)}.trust_level="trusted"', args)
        self.assertEqual(args[-5:], ["-C", str(cwd), "--config", 'model_reasoning_effort="high"', "prompt"])

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
