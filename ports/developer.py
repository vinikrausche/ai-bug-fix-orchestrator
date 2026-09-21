"""Input port for the developer role."""

from abc import ABC, abstractmethod

from domain.models import BugReport, FixPlan, ImplementationResult
from ports.context import AgentContext


class DeveloperPort(ABC):
    """Provider-independent contract used to implement a planned bug fix."""

    @abstractmethod
    def implement_fix(
        self,
        bug: BugReport,
        plan: FixPlan,
        context: AgentContext,
    ) -> ImplementationResult:
        """Apply the smallest reasonable change described by the plan."""
