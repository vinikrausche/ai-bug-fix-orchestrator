"""Input port for the bug-fix workflow."""

from abc import ABC, abstractmethod

from domain.models import BugReport, ReviewResult


class BugFixWorkflowPort(ABC):
    """Provider- and framework-independent bug-fix orchestration contract."""

    @abstractmethod
    def run(self, bug: BugReport) -> ReviewResult:
        """Run the bug-fix workflow and return its final review."""
