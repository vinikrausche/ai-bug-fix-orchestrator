"""Codex-backed implementations of the agent role ports."""

import json
from pathlib import Path
from typing import Any, Protocol

from adapters.codex_cli_client import CodexSandbox
from domain.models import (
    BugReport,
    FixPlan,
    ImplementationResult,
    ReviewResult,
    TestResult,
)
from ports.architect import ArchitectPort
from ports.context import AgentContext
from ports.developer import DeveloperPort
from ports.reviewer import ReviewerPort


class CodexClient(Protocol):
    def execute(
        self,
        prompt: str,
        *,
        project_path: Path,
        sandbox: CodexSandbox,
        model: str,
        output_schema: dict[str, Any],
    ) -> dict[str, Any]:
        """Run Codex in a repository and return its structured response."""


_TEST_RESULT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "command": {"type": "string"},
        "passed": {"type": "boolean"},
        "details": {"type": "string"},
    },
    "required": ["command", "passed", "details"],
    "additionalProperties": False,
}

_FIX_PLAN_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "root_cause": {"type": "string"},
        "steps": {"type": "array", "items": {"type": "string"}},
        "affected_files": {"type": "array", "items": {"type": "string"}},
        "risks": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["summary", "root_cause", "steps", "affected_files", "risks"],
    "additionalProperties": False,
}

_IMPLEMENTATION_RESULT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "changed_files": {"type": "array", "items": {"type": "string"}},
        "tests": {"type": "array", "items": _TEST_RESULT_SCHEMA},
        "notes": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["summary", "changed_files", "tests", "notes"],
    "additionalProperties": False,
}

_REVIEW_RESULT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "approved": {"type": "boolean"},
        "summary": {"type": "string"},
        "findings": {"type": "array", "items": {"type": "string"}},
        "tests": {"type": "array", "items": _TEST_RESULT_SCHEMA},
    },
    "required": ["approved", "summary", "findings", "tests"],
    "additionalProperties": False,
}


class CodexAgentAdapter:
    """Shared prompt and execution behavior for Codex-backed roles."""

    def __init__(self, client: CodexClient, model: str) -> None:
        self._client = client
        self._model = model

    def process_request(
        self,
        request: str,
        context: AgentContext,
        *,
        sandbox: CodexSandbox,
        output_schema: dict[str, Any],
    ) -> dict[str, Any]:
        prompt = (
            f"{context.render_instructions()}\n\n"
            "# TARGET REPOSITORY\n"
            f"{context.repository}\n\n"
            "# TASK\n"
            f"{request}"
        )
        return self._client.execute(
            prompt,
            project_path=context.repository,
            sandbox=sandbox,
            model=self._model,
            output_schema=output_schema,
        )


class CodexArchitectAdapter(CodexAgentAdapter, ArchitectPort):
    def create_fix_plan(self, bug: BugReport, context: AgentContext) -> FixPlan:
        response = self.process_request(
            (
                "Act as the Architect. Work autonomously from the reported problem. "
                "Inspect the repository, discover relevant documentation, source files, "
                "tests, project structure, and the likely root cause. Do not modify any "
                "file. Return the smallest safe implementation plan.\n\n"
                f"Bug title: {bug.title}\n"
                f"Bug description: {bug.description}"
            ),
            context,
            sandbox="read-only",
            output_schema=_FIX_PLAN_SCHEMA,
        )
        return FixPlan(
            summary=str(response["summary"]),
            root_cause=str(response["root_cause"]),
            steps=tuple(str(step) for step in response["steps"]),
            affected_files=tuple(Path(path) for path in response["affected_files"]),
            risks=tuple(str(risk) for risk in response["risks"]),
        )


class CodexDeveloperAdapter(CodexAgentAdapter, DeveloperPort):
    def implement_fix(
        self,
        bug: BugReport,
        plan: FixPlan,
        context: AgentContext,
    ) -> ImplementationResult:
        response = self.process_request(
            (
                "Act as the Developer. Inspect the repository as needed, implement the "
                "smallest change that resolves the bug, run relevant tests when useful, "
                "and inspect git diff after editing. Modify files only inside the target "
                "repository. Do not perform unrelated refactoring.\n\n"
                f"Bug title: {bug.title}\n"
                f"Bug description: {bug.description}\n\n"
                f"Fix plan:\n{_render_plan(plan)}"
            ),
            context,
            sandbox="workspace-write",
            output_schema=_IMPLEMENTATION_RESULT_SCHEMA,
        )
        return ImplementationResult(
            summary=str(response["summary"]),
            changed_files=tuple(Path(path) for path in response["changed_files"]),
            tests=_parse_test_results(response["tests"]),
            notes=tuple(str(note) for note in response["notes"]),
        )


class CodexReviewerAdapter(CodexAgentAdapter, ReviewerPort):
    def review_fix(
        self,
        bug: BugReport,
        plan: FixPlan,
        implementation: ImplementationResult,
        context: AgentContext,
    ) -> ReviewResult:
        response = self.process_request(
            (
                "Act as the Reviewer. Do not modify files. Inspect the resulting git diff, "
                "discover how this project is run and tested, execute relevant validation, "
                "and determine whether the original bug is fixed. Do not approve when a "
                "relevant test fails.\n\n"
                f"Bug title: {bug.title}\n"
                f"Bug description: {bug.description}\n\n"
                f"Fix plan:\n{_render_plan(plan)}\n\n"
                f"Implementation result:\n{_render_implementation(implementation)}"
            ),
            context,
            sandbox="read-only",
            output_schema=_REVIEW_RESULT_SCHEMA,
        )
        return ReviewResult(
            approved=bool(response["approved"]),
            summary=str(response["summary"]),
            findings=tuple(str(finding) for finding in response["findings"]),
            tests=_parse_test_results(response["tests"]),
            metadata={"provider": "codex"},
        )


def _parse_test_results(values: list[dict[str, Any]]) -> tuple[TestResult, ...]:
    return tuple(
        TestResult(
            command=str(value["command"]),
            passed=bool(value["passed"]),
            details=str(value["details"]),
        )
        for value in values
    )


def _render_plan(plan: FixPlan) -> str:
    return json.dumps(
        {
            "summary": plan.summary,
            "root_cause": plan.root_cause,
            "steps": plan.steps,
            "affected_files": [str(path) for path in plan.affected_files],
            "risks": plan.risks,
        },
        indent=2,
    )


def _render_implementation(implementation: ImplementationResult) -> str:
    return json.dumps(
        {
            "summary": implementation.summary,
            "changed_files": [str(path) for path in implementation.changed_files],
            "tests": [
                {
                    "command": test.command,
                    "passed": test.passed,
                    "details": test.details,
                }
                for test in implementation.tests
            ],
            "notes": implementation.notes,
        },
        indent=2,
    )
