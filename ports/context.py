"""Context shared by every agent role port."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ContextDocument:
    """A documentation or skill file already read from the workspace."""

    path: Path
    content: str

    def __post_init__(self) -> None:
        if not self.content.strip():
            raise ValueError(f"Context file cannot be empty: {self.path}")


@dataclass(frozen=True)
class AgentContext:
    """Mandatory project knowledge supplied on every role invocation.

    Project documentation is discovered from ``repository`` by the agents.
    Skill documents are loaded from the orchestrator configuration.
    """

    repository: Path
    documentation: tuple[ContextDocument, ...]
    shared_skills: tuple[ContextDocument, ...]
    role_skills: tuple[ContextDocument, ...]

    def __post_init__(self) -> None:
        if not self.shared_skills:
            raise ValueError("At least one shared skill is required")
        if not self.role_skills:
            raise ValueError("At least one role-specific skill is required")

    def render_instructions(self) -> str:
        """Render all mandatory context for a provider request."""
        sections = (
            ("SHARED SKILLS", self.shared_skills),
            ("ROLE SKILLS", self.role_skills),
        )
        if self.documentation:
            sections = (("PROJECT DOCUMENTATION", self.documentation), *sections)
        rendered_sections = []
        for title, documents in sections:
            rendered_documents = "\n\n".join(
                f"## {document.path}\n{document.content}" for document in documents
            )
            rendered_sections.append(f"# {title}\n{rendered_documents}")
        return "\n\n".join(rendered_sections)
