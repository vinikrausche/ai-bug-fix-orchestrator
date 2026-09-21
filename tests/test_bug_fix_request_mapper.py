import tempfile
import unittest
from pathlib import Path

from application.dto import BugFixRequest
from application.mappers import BugFixRequestMapper


class BugFixRequestMapperTest(unittest.TestCase):
    def test_maps_all_user_input_to_the_internal_bug(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            request = BugFixRequest(
                title="  Startup crash  ",
                description="  The application exits immediately.  ",
                project_path=Path(directory),
            )

            bug = BugFixRequestMapper().map(request)

            self.assertEqual(bug.title, "Startup crash")
            self.assertEqual(bug.description, "The application exits immediately.")
            self.assertEqual(bug.project_path, Path(directory).resolve())

    def test_rejects_a_missing_project_directory(self) -> None:
        request = BugFixRequest("Bug", "Description", Path("does-not-exist"))

        with self.assertRaisesRegex(ValueError, "Project directory not found"):
            BugFixRequestMapper().map(request)


if __name__ == "__main__":
    unittest.main()
