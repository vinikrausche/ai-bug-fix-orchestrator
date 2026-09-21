import unittest
from pathlib import Path
from typing import Any

from adapters.codex_agent_adapter import (
    CodexArchitectAdapter,
    CodexDeveloperAdapter,
    CodexReviewerAdapter,
)
from adapters.codex_cli_client import CodexSandbox
from domain.models import BugReport, FixPlan, ImplementationResult
from ports.context import AgentContext, ContextDocument


class RecordingCodexClient:
    def __init__(self, responses: list[dict[str, Any]]) -> None:
        self.responses = responses
        self.requests: list[dict[str, Any]] = []

    def execute(
        self,
        prompt: str,
        *,
        project_path: Path,
        sandbox: CodexSandbox,
        model: str,
        output_schema: dict[str, Any],
    ) -> dict[str, Any]:
        self.requests.append(
            {
                "prompt": prompt,
                "project_path": project_path,
                "sandbox": sandbox,
                "model": model,
                "output_schema": output_schema,
            }
        )
        return self.responses.pop(0)


class CodexAgentAdapterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.context = AgentContext(
            repository=Path("/workspace"),
            documentation=(),
            shared_skills=(ContextDocument(Path("skills/shared.md"), "shared-skill"),),
            role_skills=(ContextDocument(Path("skills/role.md"), "role-skill"),),
        )
        self.bug = BugReport("Startup crash", "Application exits", Path("/workspace"))

    def test_architect_uses_read_only_and_maps_fix_plan(self) -> None:
        client = RecordingCodexClient(
            [
                {
                    "summary": "Fix startup",
                    "root_cause": "Invalid import",
                    "steps": ["Correct the import"],
                    "affected_files": ["app.py"],
                    "risks": [],
                }
            ]
        )

        plan = CodexArchitectAdapter(client, "architect-model").create_fix_plan(
            self.bug, self.context
        )

        self.assertEqual(plan.root_cause, "Invalid import")
        self.assertEqual(plan.affected_files, (Path("app.py"),))
        self.assertEqual(client.requests[0]["sandbox"], "read-only")
        self.assertEqual(client.requests[0]["project_path"], Path("/workspace"))
        self.assertIn("Startup crash", client.requests[0]["prompt"])
        self.assertIn("shared-skill", client.requests[0]["prompt"])

    def test_developer_uses_workspace_write_and_maps_implementation(self) -> None:
        client = RecordingCodexClient(
            [
                {
                    "summary": "Corrected import",
                    "changed_files": ["app.py"],
                    "tests": [
                        {"command": "pytest", "passed": True, "details": "1 passed"}
                    ],
                    "notes": [],
                }
            ]
        )
        plan = FixPlan("Fix startup", "Invalid import", ("Correct import",))

        result = CodexDeveloperAdapter(client, "developer-model").implement_fix(
            self.bug, plan, self.context
        )

        self.assertEqual(result.changed_files, (Path("app.py"),))
        self.assertTrue(result.tests[0].passed)
        self.assertEqual(client.requests[0]["sandbox"], "workspace-write")
        self.assertIn("Invalid import", client.requests[0]["prompt"])

    def test_reviewer_uses_read_only_and_maps_review(self) -> None:
        client = RecordingCodexClient(
            [
                {
                    "approved": True,
                    "summary": "Fix verified",
                    "findings": [],
                    "tests": [
                        {"command": "pytest", "passed": True, "details": "1 passed"}
                    ],
                }
            ]
        )
        plan = FixPlan("Fix startup", "Invalid import", ("Correct import",))
        implementation = ImplementationResult("Corrected import", (Path("app.py"),))

        result = CodexReviewerAdapter(client, "reviewer-model").review_fix(
            self.bug, plan, implementation, self.context
        )

        self.assertTrue(result.approved)
        self.assertEqual(result.metadata, {"provider": "codex"})
        self.assertEqual(client.requests[0]["sandbox"], "read-only")
        self.assertIn("git diff", client.requests[0]["prompt"])


if __name__ == "__main__":
    unittest.main()
