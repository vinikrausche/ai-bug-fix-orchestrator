"""Input accepted by the bug-fix use case."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BugFixRequest:
    title: str
    description: str
    project_path: Path
