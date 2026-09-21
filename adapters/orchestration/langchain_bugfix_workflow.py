"""LangChain implementation of the linear bug-fix workflow."""

from typing import NotRequired, TypedDict

from langchain_core.runnables import RunnableLambda

from domain.models import BugReport, FixPlan, ImplementationResult, ReviewResult
from ports.architect import ArchitectPort
from ports.configuration import AgentContextProviderPort
from ports.developer import DeveloperPort
from ports.reviewer import ReviewerPort
from ports.workflow import BugFixWorkflowPort


class BugFixWorkflowState(TypedDict):
    """Values accumulated while the workflow executes."""

    bug: BugReport
    plan: NotRequired[FixPlan]
    implementation: NotRequired[ImplementationResult]
    review: NotRequired[ReviewResult]


class LangChainBugFixWorkflow(BugFixWorkflowPort):
    """Run architect, developer, and reviewer ports in sequence."""

    def __init__(
        self,
        architect: ArchitectPort,
        developer: DeveloperPort,
        reviewer: ReviewerPort,
        context_provider: AgentContextProviderPort,
    ) -> None:
        self._architect = architect
        self._developer = developer
        self._reviewer = reviewer
        self._context_provider = context_provider
        self._chain = (
            RunnableLambda(self._architect_step)
            | RunnableLambda(self._developer_step)
            | RunnableLambda(self._reviewer_step)
        )

    def _architect_step(self, state: BugFixWorkflowState) -> BugFixWorkflowState:
        context = self._context_provider.load_context("architect")
        plan = self._architect.create_fix_plan(state["bug"], context)
        return {**state, "plan": plan}

    def _developer_step(self, state: BugFixWorkflowState) -> BugFixWorkflowState:
        context = self._context_provider.load_context("developer")
        implementation = self._developer.implement_fix(
            state["bug"], state["plan"], context
        )
        return {**state, "implementation": implementation}

    def _reviewer_step(self, state: BugFixWorkflowState) -> BugFixWorkflowState:
        context = self._context_provider.load_context("reviewer")
        review = self._reviewer.review_fix(
            state["bug"], state["plan"], state["implementation"], context
        )
        return {**state, "review": review}

    def run(self, bug: BugReport) -> ReviewResult:
        result: BugFixWorkflowState = self._chain.invoke({"bug": bug})
        return result["review"]
