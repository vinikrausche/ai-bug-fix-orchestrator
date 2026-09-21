import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from cli.main import main
from domain.models import BugReport, ReviewResult
from ports.workflow import BugFixWorkflowPort


class RecordingWorkflow(BugFixWorkflowPort):
    def __init__(self) -> None:
        self.bug: BugReport | None = None
        self.result = ReviewResult(approved=True, summary="Fix approved")

    def run(self, bug: BugReport) -> ReviewResult:
        self.bug = bug
        return self.result


class CliTest(unittest.TestCase):
    def test_maps_three_arguments_invokes_workflow_and_prints_result(self) -> None:
        workflow = RecordingWorkflow()
        output = StringIO()

        with tempfile.TemporaryDirectory() as directory, redirect_stdout(output):
            result = main(
                workflow,
                [
                    "--title",
                    "Application crashes on startup",
                    "--description",
                    "Running the project produces an error.",
                    "--project",
                    directory,
                ],
            )

        self.assertIs(result, workflow.result)
        self.assertIsNotNone(workflow.bug)
        assert workflow.bug is not None
        self.assertEqual(workflow.bug.title, "Application crashes on startup")
        self.assertEqual(
            workflow.bug.description, "Running the project produces an error."
        )
        self.assertEqual(workflow.bug.project_path, Path(directory).resolve())
        self.assertIn("Fix approved", output.getvalue())


if __name__ == "__main__":
    unittest.main()
