"""Subprocess-backed client for the locally authenticated Codex CLI."""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Literal

CodexSandbox = Literal["read-only", "workspace-write"]


class CodexCliClient:
    """Execute structured Codex requests inside a target repository."""

    def __init__(self, executable: str = "codex") -> None:
        self._executable = executable

    def execute(
        self,
        prompt: str,
        *,
        project_path: Path,
        sandbox: CodexSandbox,
        model: str,
        output_schema: dict[str, Any],
    ) -> dict[str, Any]:
        repository = project_path.resolve()
        if not repository.is_dir():
            raise ValueError(f"Repository directory not found: {repository}")

        with tempfile.TemporaryDirectory(prefix="bug-fix-codex-") as directory:
            temporary_directory = Path(directory)
            schema_path = temporary_directory / "output-schema.json"
            response_path = temporary_directory / "response.json"
            schema_path.write_text(json.dumps(output_schema), encoding="utf-8")

            command = [
                self._executable,
                "exec",
                "--cd",
                str(repository),
                "--sandbox",
                sandbox,
                "--ephemeral",
                "--color",
                "never",
                "--output-schema",
                str(schema_path),
                "--output-last-message",
                str(response_path),
            ]
            if model != "default":
                command.extend(("--model", model))
            command.append("-")

            try:
                completed = subprocess.run(
                    command,
                    cwd=repository,
                    input=prompt,
                    text=True,
                    capture_output=True,
                    check=False,
                )
            except FileNotFoundError as error:
                raise RuntimeError(
                    f"Codex CLI executable not found: {self._executable}"
                ) from error

            if completed.returncode != 0:
                details = completed.stderr.strip() or completed.stdout.strip()
                raise RuntimeError(
                    f"Codex CLI failed with exit code {completed.returncode}: {details}"
                )

            try:
                response = json.loads(response_path.read_text(encoding="utf-8"))
            except FileNotFoundError as error:
                raise RuntimeError("Codex CLI did not produce a response") from error
            except json.JSONDecodeError as error:
                raise RuntimeError("Codex CLI produced invalid structured output") from error

        if not isinstance(response, dict):
            raise RuntimeError("Codex CLI response must be a JSON object")
        return response
