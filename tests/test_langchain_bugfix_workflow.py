import unittest
from pathlib import Path

from adapters.orchestration.langchain_bugfix_workflow import LangChainBugFixWorkflow
from domain.models import BugReport, FixPlan, ImplementationResult, ReviewResult
from ports.architect import ArchitectPort
from ports.agent_context_provider import AgentContextProviderPort, AgentRole
from ports.context import AgentContext, ContextDocument
from ports.developer import DeveloperPort
from ports.reviewer import ReviewerPort


class FakeContextProvider(AgentContextProviderPort):
    def __init__(self) -> None:
        self.loaded_contexts: list[tuple[AgentRole, Path]] = []
        self.contexts = {
            role: AgentContext(
                repository=Path("/workspace"),
                documentation=(ContextDocument(Path("docs/project.md"), "docs"),),
                shared_skills=(ContextDocument(Path("skills/shared.md"), "shared"),),
                role_skills=(ContextDocument(Path(f"skills/{role}.md"), role),),
            )
            for role in ("architect", "developer", "reviewer")
        }

    def load_context(self, role: AgentRole, project_path: Path) -> AgentContext:
        self.loaded_contexts.append((role, project_path))
        return self.contexts[role]


class FakeArchitect(ArchitectPort):
    def __init__(self, calls: list[str], plan: FixPlan) -> None:
        self.calls = calls
        self.plan = plan
        self.received_context: AgentContext | None = None

    def create_fix_plan(
        self, bug: BugReport, context: AgentContext
    ) -> FixPlan:
        self.calls.append("architect")
        self.received_context = context
        return self.plan


class FakeDeveloper(DeveloperPort):
    def __init__(self, calls: list[str], implementation: ImplementationResult) -> None:
        self.calls = calls
        self.implementation = implementation
        self.received_plan: FixPlan | None = None
        self.received_context: AgentContext | None = None

    def implement_fix(
        self,
        bug: BugReport,
        plan: FixPlan,
        context: AgentContext,
    ) -> ImplementationResult:
        self.calls.append("developer")
        self.received_plan = plan
        self.received_context = context
        return self.implementation


class FakeReviewer(ReviewerPort):
    def __init__(self, calls: list[str], review: ReviewResult) -> None:
        self.calls = calls
        self.review = review
        self.received_implementation: ImplementationResult | None = None
        self.received_context: AgentContext | None = None

    def review_fix(
        self,
        bug: BugReport,
        plan: FixPlan,
        implementation: ImplementationResult,
        context: AgentContext,
    ) -> ReviewResult:
        self.calls.append("reviewer")
        self.received_implementation = implementation
        self.received_context = context
        return self.review


class LangChainBugFixWorkflowTest(unittest.TestCase):
    def test_runs_all_steps_with_accumulated_state_and_role_contexts(self) -> None:
        calls: list[str] = []
        plan = FixPlan("plan", "cause", ("change code",))
        implementation = ImplementationResult("implemented", (Path("app.py"),))
        review = ReviewResult(True, "approved")
        context_provider = FakeContextProvider()
        architect = FakeArchitect(calls, plan)
        developer = FakeDeveloper(calls, implementation)
        reviewer = FakeReviewer(calls, review)
        workflow = LangChainBugFixWorkflow(
            architect, developer, reviewer, context_provider
        )

        project_path = Path("/workspace")
        result = workflow.run(BugReport("Startup crash", "broken behavior", project_path))

        self.assertEqual(calls, ["architect", "developer", "reviewer"])
        self.assertIs(developer.received_plan, plan)
        self.assertIs(reviewer.received_implementation, implementation)
        self.assertEqual(
            context_provider.loaded_contexts,
            [
                ("architect", project_path),
                ("developer", project_path),
                ("reviewer", project_path),
            ],
        )
        self.assertIs(
            architect.received_context, context_provider.contexts["architect"]
        )
        self.assertIs(
            developer.received_context, context_provider.contexts["developer"]
        )
        self.assertIs(reviewer.received_context, context_provider.contexts["reviewer"])
        self.assertIs(result, review)


if __name__ == "__main__":
    unittest.main()
