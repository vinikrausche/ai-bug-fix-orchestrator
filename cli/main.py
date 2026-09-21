"""Command-line input adapter for the bug-fix workflow."""

import argparse
from collections.abc import Sequence
from pathlib import Path

from application.dto import BugFixRequest
from application.mappers import BugFixRequestMapper
from cli.bootstrap import build_bug_fix_workflow
from domain.models import ReviewResult
from ports.workflow import BugFixWorkflowPort


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Investigate and fix a project bug")
    parser.add_argument("--title", required=True)
    parser.add_argument("--description", required=True)
    parser.add_argument("--project", required=True, type=Path, dest="project_path")
    return parser


def main(
    argv: Sequence[str] | None = None,
    workflow: BugFixWorkflowPort | None = None,
) -> ReviewResult:
    args = build_parser().parse_args(argv)
    request = BugFixRequest(
        title=args.title,
        description=args.description,
        project_path=args.project_path,
    )
    bug = BugFixRequestMapper().map(request)
    active_workflow = workflow or build_bug_fix_workflow()
    result = active_workflow.run(bug)
    print(result)
    return result


if __name__ == "__main__":
    main()
