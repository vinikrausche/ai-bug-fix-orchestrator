"""YAML-backed agent configuration adapter."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from ports.agent_context_provider import AgentContextProviderPort, AgentRole
from ports.context import AgentContext, ContextDocument


@dataclass(frozen=True)
class AgentSettings:
    """Provider selection used by the composition root."""

    adapter: str
    model: str


class YamlAgentConfigurationAdapter(AgentContextProviderPort):
    """Reads provider selection and role skills from a YAML file."""

    _ROLES: tuple[AgentRole, ...] = ("architect", "developer", "reviewer")

    def __init__(self, configuration_file: Path) -> None:
        self._configuration_file = configuration_file.resolve()
        self._application_root = self._configuration_file.parent.parent
        self._configuration = self._read_configuration()
        self._validate_configuration()

    def agent_settings(self, role: AgentRole) -> AgentSettings:
        agent = self._agent(role)
        return AgentSettings(adapter=agent["adapter"], model=agent["model"])

    def load_context(self, role: AgentRole, project_path: Path) -> AgentContext:
        agent = self._agent(role)
        repository = project_path.expanduser().resolve()
        if not repository.is_dir():
            raise ValueError(f"Repository directory not found: {repository}")

        return AgentContext(
            repository=repository,
            documentation=(),
            shared_skills=self._read_files(agent["skills"]["shared"]),
            role_skills=self._read_files(agent["skills"]["role"]),
        )

    def _read_configuration(self) -> dict[str, Any]:
        try:
            raw = yaml.safe_load(self._configuration_file.read_text(encoding="utf-8"))
        except FileNotFoundError as error:
            raise ValueError(
                f"Configuration file not found: {self._configuration_file}"
            ) from error
        except yaml.YAMLError as error:
            raise ValueError(f"Invalid YAML: {self._configuration_file}") from error

        if not isinstance(raw, dict):
            raise ValueError("Agent configuration must be a YAML mapping")
        return raw

    def _validate_configuration(self) -> None:
        try:
            for role in self._ROLES:
                agent = self._configuration["agents"][role]
                if not agent["adapter"] or not agent["model"]:
                    raise ValueError(f"Adapter and model are required for {role}")
                if not agent["skills"]["shared"]:
                    raise ValueError(f"Shared skills are required for {role}")
                if not agent["skills"]["role"]:
                    raise ValueError(f"Role skills are required for {role}")
        except (KeyError, TypeError) as error:
            raise ValueError(
                f"Missing or invalid configuration field: {error}"
            ) from error

    def _agent(self, role: AgentRole) -> dict[str, Any]:
        if role not in self._ROLES:
            raise ValueError(f"Unsupported agent role: {role}")
        return self._configuration["agents"][role]

    def _read_files(self, paths: list[str]) -> tuple[ContextDocument, ...]:
        documents = []
        for configured_path in paths:
            path = self._resolve_path(configured_path)
            try:
                content = path.read_text(encoding="utf-8")
            except FileNotFoundError as error:
                raise ValueError(f"Configured context file not found: {path}") from error
            documents.append(ContextDocument(path=path, content=content))
        return tuple(documents)

    def _resolve_path(self, configured_path: str) -> Path:
        path = (self._application_root / configured_path).resolve()
        if not path.is_relative_to(self._application_root):
            raise ValueError(
                f"Configured skill path leaves application root: {configured_path}"
            )
        return path
