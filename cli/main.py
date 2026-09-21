"""Command-line input adapter for the bug-fix workflow."""

import argparse
from collections.abc import Sequence
from pathlib import Path

from application.dto import BugFixRequest
from application.mappers import BugFixRequestMapper
from domain.models import ReviewResult
from ports.workflow import BugFixWorkflowPort


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Investigate and fix a project bug")
    parser.add_argument("--title", required=True)
    parser.add_argument("--description", required=True)
    parser.add_argument("--project", required=True, type=Path, dest="project_path")
    return parser


def main(
    workflow: BugFixWorkflowPort,
    argv: Sequence[str] | None = None,
) -> ReviewResult:
    args = build_parser().parse_args(argv)
    request = BugFixRequest(
        title=args.title,
        description=args.description,
        project_path=args.project_path,
    )
    bug = BugFixRequestMapper().map(request)
    result = workflow.run(bug)
    print(result)
    return result
