"""Provider- and framework-independent workflow values."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class BugReport:
    description: str
    source: Path | None = None

    def __post_init__(self) -> None:
        if not self.description.strip():
            raise ValueError("Bug description cannot be empty")


@dataclass(frozen=True)
class FixPlan:
    summary: str
    root_cause: str
    steps: tuple[str, ...]
    affected_files: tuple[Path, ...] = ()
    risks: tuple[str, ...] = ()


@dataclass(frozen=True)
class TestResult:
    command: str
    passed: bool
    details: str = ""


@dataclass(frozen=True)
class ImplementationResult:
    summary: str
    changed_files: tuple[Path, ...]
    tests: tuple[TestResult, ...] = ()
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class ReviewResult:
    approved: bool
    summary: str
    findings: tuple[str, ...] = ()
    tests: tuple[TestResult, ...] = ()
    metadata: dict[str, str] = field(default_factory=dict)
