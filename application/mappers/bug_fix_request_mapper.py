"""Map a bug-fix request into the workflow's domain input."""

from application.dto import BugFixRequest
from domain.models import BugReport


class BugFixRequestMapper:
    def map(self, request: BugFixRequest) -> BugReport:
        title = request.title.strip()
        description = request.description.strip()
        project_path = request.project_path.expanduser().resolve()

        if not title:
            raise ValueError("Bug title cannot be empty")
        if not description:
            raise ValueError("Bug description cannot be empty")
        if not project_path.is_dir():
            raise ValueError(f"Project directory not found: {project_path}")

        return BugReport(
            title=title,
            description=description,
            project_path=project_path,
        )
