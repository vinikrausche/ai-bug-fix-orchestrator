"""Output port used to obtain context for an agent role."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Literal

from ports.context import AgentContext

AgentRole = Literal["architect", "developer", "reviewer"]


class AgentContextProviderPort(ABC):
    """Loads configured skill instructions for a role and target project."""

    @abstractmethod
    def load_context(self, role: AgentRole, project_path: Path) -> AgentContext:
        """Return role context rooted at the runtime target repository."""
