import json
import tempfile
import unittest
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch

from adapters.codex_cli_client import CodexCliClient
from adapters.sensitive_data_scanner import SensitiveDataError


class CodexCliClientTest(unittest.TestCase):
    def test_executes_in_target_repository_with_schema_and_sandbox(self) -> None:
        schema = {
            "type": "object",
            "properties": {"summary": {"type": "string"}},
            "required": ["summary"],
            "additionalProperties": False,
        }

        def complete(command: list[str], **kwargs: object) -> CompletedProcess[str]:
            response_path = Path(command[command.index("--output-last-message") + 1])
            response_path.write_text(
                json.dumps({"summary": "completed"}), encoding="utf-8"
            )
            return CompletedProcess(command, 0, "", "")

        with tempfile.TemporaryDirectory() as directory, patch(
            "adapters.codex_cli_client.subprocess.run", side_effect=complete
        ) as run:
            repository = Path(directory).resolve()
            response = CodexCliClient().execute(
                "inspect and fix",
                project_path=repository,
                sandbox="workspace-write",
                model="default",
                output_schema=schema,
            )

        self.assertEqual(response, {"summary": "completed"})
        command = run.call_args.args[0]
        self.assertEqual(command[0], "codex")
        self.assertIn("exec", command)
        self.assertIn('shell_environment_policy.inherit="core"', command)
        self.assertIn(
            "shell_environment_policy.ignore_default_excludes=false", command
        )
        self.assertEqual(command[command.index("--cd") + 1], str(repository))
        self.assertEqual(
            command[command.index("--sandbox") + 1], "workspace-write"
        )
        self.assertNotIn("--model", command)
        self.assertEqual(run.call_args.kwargs["cwd"], repository)
        self.assertEqual(run.call_args.kwargs["input"], "inspect and fix")
        self.assertFalse(run.call_args.kwargs["check"])

    def test_reports_a_codex_process_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch(
            "adapters.codex_cli_client.subprocess.run",
            return_value=CompletedProcess([], 1, "", "authentication failed"),
        ):
            with self.assertRaisesRegex(RuntimeError, "authentication failed"):
                CodexCliClient().execute(
                    "inspect",
                    project_path=Path(directory),
                    sandbox="read-only",
                    model="codex-model",
                    output_schema={"type": "object"},
                )

    def test_refuses_repository_with_environment_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch(
            "adapters.codex_cli_client.subprocess.run"
        ) as run:
            repository = Path(directory)
            (repository / ".env").write_text("DATABASE_URL=secret", encoding="utf-8")

            with self.assertRaisesRegex(SensitiveDataError, r"\.env"):
                CodexCliClient().execute(
                    "inspect",
                    project_path=repository,
                    sandbox="read-only",
                    model="default",
                    output_schema={"type": "object"},
                )

        run.assert_not_called()

    def test_refuses_repository_with_private_key_signature(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch(
            "adapters.codex_cli_client.subprocess.run"
        ) as run:
            repository = Path(directory)
            private_key_marker = "-----BEGIN PRIVATE " + "KEY-----"
            (repository / "settings.py").write_text(
                f'KEY = "{private_key_marker}"', encoding="utf-8"
            )

            with self.assertRaisesRegex(SensitiveDataError, "private key"):
                CodexCliClient().execute(
                    "inspect",
                    project_path=repository,
                    sandbox="read-only",
                    model="default",
                    output_schema={"type": "object"},
                )

        run.assert_not_called()

    def test_allows_placeholder_environment_template(self) -> None:
        def complete(command: list[str], **kwargs: object) -> CompletedProcess[str]:
            response_path = Path(command[command.index("--output-last-message") + 1])
            response_path.write_text('{"ok": true}', encoding="utf-8")
            return CompletedProcess(command, 0, "", "")

        with tempfile.TemporaryDirectory() as directory, patch(
            "adapters.codex_cli_client.subprocess.run", side_effect=complete
        ):
            repository = Path(directory)
            (repository / ".env.example").write_text(
                "API_KEY=<replace_me>", encoding="utf-8"
            )
            result = CodexCliClient().execute(
                "inspect",
                project_path=repository,
                sandbox="read-only",
                model="default",
                output_schema={"type": "object"},
            )

        self.assertEqual(result, {"ok": True})


if __name__ == "__main__":
    unittest.main()
