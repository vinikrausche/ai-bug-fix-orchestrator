import json
import tempfile
import unittest
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch

from adapters.codex_cli_client import CodexCliClient


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
        self.assertEqual(command[:2], ["codex", "exec"])
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


if __name__ == "__main__":
    unittest.main()
