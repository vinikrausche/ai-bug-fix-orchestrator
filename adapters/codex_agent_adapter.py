"""Adapter for a Codex client.

The concrete Codex SDK/CLI integration can be injected later without leaking
provider details into the application or role ports.
"""

from typing import Protocol

from ports.context import AgentContext


class CodexClient(Protocol):
    def handle_request(self, request: str) -> str:
        """Send a request to Codex and return its response."""


class CodexAgentAdapter:
    def __init__(self, client: CodexClient) -> None:
        self._client = client

    def process_request(self, request: str, context: AgentContext) -> str:
        prompt = (
            f"{context.render_instructions()}\n\n"
            "# TASK\n"
            f"Repository: {context.repository}\n\n"
            f"{request}"
        )
        return self._client.handle_request(prompt)
