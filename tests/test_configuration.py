import unittest
from pathlib import Path

from adapters.yaml_configuration_adapter import YamlAgentConfigurationAdapter


class YamlAgentConfigurationAdapterTest(unittest.TestCase):
    def setUp(self) -> None:
        project_root = Path(__file__).resolve().parent.parent
        self.adapter = YamlAgentConfigurationAdapter(
            project_root / "config" / "agents.yaml"
        )

    def test_all_roles_load_documentation_and_their_skills(self) -> None:
        expected_role_skill = {
            "architect": "bugfix-planning",
            "developer": "safe-bugfix",
            "reviewer": "diff-review",
        }

        for role, expected_skill in expected_role_skill.items():
            with self.subTest(role=role):
                context = self.adapter.load_context(role)  # type: ignore[arg-type]

                self.assertGreaterEqual(len(context.documentation), 2)
                self.assertIn("project-context", context.shared_skills[0].content)
                self.assertTrue(
                    any(expected_skill in skill.content for skill in context.role_skills)
                )

    def test_all_roles_are_configured_with_codex(self) -> None:
        for role in ("architect", "developer", "reviewer"):
            with self.subTest(role=role):
                settings = self.adapter.agent_settings(role)  # type: ignore[arg-type]
                self.assertEqual(settings.adapter, "codex")


if __name__ == "__main__":
    unittest.main()
