import unittest

from adapters.codex_agent_adapter import (
    CodexArchitectAdapter,
    CodexDeveloperAdapter,
    CodexReviewerAdapter,
)
from adapters.codex_cli_client import CodexCliClient
from adapters.orchestration.langchain_bugfix_workflow import LangChainBugFixWorkflow
from cli.bootstrap import build_bug_fix_workflow


class BootstrapTest(unittest.TestCase):
    def test_builds_langchain_workflow_with_codex_roles_and_shared_client(self) -> None:
        workflow = build_bug_fix_workflow()

        self.assertIsInstance(workflow, LangChainBugFixWorkflow)
        self.assertIsInstance(workflow._architect, CodexArchitectAdapter)
        self.assertIsInstance(workflow._developer, CodexDeveloperAdapter)
        self.assertIsInstance(workflow._reviewer, CodexReviewerAdapter)
        self.assertIsInstance(workflow._architect._client, CodexCliClient)
        self.assertIs(workflow._architect._client, workflow._developer._client)
        self.assertIs(workflow._developer._client, workflow._reviewer._client)


if __name__ == "__main__":
    unittest.main()
