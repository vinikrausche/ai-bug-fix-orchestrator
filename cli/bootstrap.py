"""Composition root for the executable bug-fix workflow."""

from pathlib import Path

from adapters.codex_agent_adapter import (
    CodexArchitectAdapter,
    CodexDeveloperAdapter,
    CodexReviewerAdapter,
)
from adapters.codex_cli_client import CodexCliClient
from adapters.orchestration.langchain_bugfix_workflow import LangChainBugFixWorkflow
from adapters.yaml_configuration_adapter import (
    AgentSettings,
    YamlAgentConfigurationAdapter,
)
from ports.agent_context_provider import AgentRole
from ports.workflow import BugFixWorkflowPort


def build_bug_fix_workflow(
    configuration_file: Path | None = None,
) -> BugFixWorkflowPort:
    application_root = Path(__file__).resolve().parent.parent
    configuration = YamlAgentConfigurationAdapter(
        configuration_file or application_root / "config" / "agents.yaml"
    )
    client = CodexCliClient()

    architect_settings = _codex_settings(configuration, "architect")
    developer_settings = _codex_settings(configuration, "developer")
    reviewer_settings = _codex_settings(configuration, "reviewer")

    return LangChainBugFixWorkflow(
        architect=CodexArchitectAdapter(client, architect_settings.model),
        developer=CodexDeveloperAdapter(client, developer_settings.model),
        reviewer=CodexReviewerAdapter(client, reviewer_settings.model),
        context_provider=configuration,
    )


def _codex_settings(
    configuration: YamlAgentConfigurationAdapter,
    role: AgentRole,
) -> AgentSettings:
    settings = configuration.agent_settings(role)
    if settings.adapter != "codex":
        raise ValueError(
            f"Unsupported adapter for {role}: {settings.adapter}. Expected: codex"
        )
    return settings
