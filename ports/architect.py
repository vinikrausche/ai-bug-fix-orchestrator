"""Input port for the architect role."""

from abc import ABC, abstractmethod

from domain.models import BugReport, FixPlan
from ports.context import AgentContext


class ArchitectPort(ABC):
    """Provider-independent contract used to plan a bug fix."""

    @abstractmethod
    def create_fix_plan(self, bug: BugReport, context: AgentContext) -> FixPlan:
        """Analyze a bug and return a plan without changing the repository."""
