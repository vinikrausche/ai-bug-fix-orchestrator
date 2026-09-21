import unittest
from pathlib import Path

from adapters.codex_agent_adapter import CodexAgentAdapter
from ports.context import AgentContext, ContextDocument


class RecordingCodexClient:
    def __init__(self) -> None:
        self.request = ""

    def handle_request(self, request: str) -> str:
        self.request = request
        return "response"


class CodexAgentAdapterTest(unittest.TestCase):
    def test_request_contains_documentation_and_all_skills(self) -> None:
        client = RecordingCodexClient()
        adapter = CodexAgentAdapter(client)
        context = AgentContext(
            repository=Path("/workspace"),
            documentation=(ContextDocument(Path("docs/project.md"), "project-doc"),),
            shared_skills=(ContextDocument(Path("skills/shared.md"), "shared-skill"),),
            role_skills=(ContextDocument(Path("skills/role.md"), "role-skill"),),
        )

        response = adapter.process_request("fix the bug", context)

        self.assertEqual(response, "response")
        self.assertIn("project-doc", client.request)
        self.assertIn("shared-skill", client.request)
        self.assertIn("role-skill", client.request)
        self.assertIn("fix the bug", client.request)


if __name__ == "__main__":
    unittest.main()
