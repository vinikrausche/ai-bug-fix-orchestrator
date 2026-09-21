import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

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
                [
                    "--title",
                    "Application crashes on startup",
                    "--description",
                    "Running the project produces an error.",
                    "--project",
                    directory,
                ],
                workflow=workflow,
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

    def test_builds_the_real_workflow_when_one_is_not_injected(self) -> None:
        workflow = RecordingWorkflow()

        with tempfile.TemporaryDirectory() as directory, patch(
            "cli.main.build_bug_fix_workflow", return_value=workflow
        ) as build_workflow, redirect_stdout(StringIO()):
            main(
                [
                    "--title",
                    "Application crashes",
                    "--description",
                    "Investigate the failure",
                    "--project",
                    directory,
                ]
            )

        build_workflow.assert_called_once_with()
        self.assertIsNotNone(workflow.bug)


if __name__ == "__main__":
    unittest.main()
