"""Output port used to obtain mandatory context for an agent role."""

from abc import ABC, abstractmethod
from typing import Literal

from ports.context import AgentContext

AgentRole = Literal["architect", "developer", "reviewer"]


class AgentContextProviderPort(ABC):
    """Loads project documentation and skill instructions for a role."""

    @abstractmethod
    def load_context(self, role: AgentRole) -> AgentContext:
        """Return a context whose configured files have already been read."""
