"""Input port for the reviewer role."""

from abc import ABC, abstractmethod

from domain.models import BugReport, FixPlan, ImplementationResult, ReviewResult
from ports.context import AgentContext


class ReviewerPort(ABC):
    """Provider-independent contract used to validate an implementation."""

    @abstractmethod
    def review_fix(
        self,
        bug: BugReport,
        plan: FixPlan,
        implementation: ImplementationResult,
        context: AgentContext,
    ) -> ReviewResult:
        """Review the diff and tests without modifying source files."""
