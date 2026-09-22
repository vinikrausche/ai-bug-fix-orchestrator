"""Preflight checks that keep common credentials out of Codex sessions."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


_SKIPPED_DIRECTORIES = {
    ".git",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".svn",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "venv",
}
_SENSITIVE_FILENAMES = {
    ".env",
    ".netrc",
    ".npmrc",
    ".pypirc",
    "auth.json",
    "credentials.json",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
    "id_rsa",
}
_SENSITIVE_SUFFIXES = {
    ".jks",
    ".key",
    ".keystore",
    ".mobileprovision",
    ".p12",
    ".pfx",
}
_SAFE_ENV_SUFFIXES = {"example", "sample", "template"}
_MAX_SCANNED_FILE_SIZE = 2 * 1024 * 1024

_SIGNATURES = (
    (
        "private key",
        re.compile(
            r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE " r"KEY-----"
        ),
    ),
    ("AWS access key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    (
        "GitHub token",
        re.compile(
            r"\b(?:github_pat_[A-Za-z0-9_]{20,}|gh[pousr]_[A-Za-z0-9_]{20,})\b"
        ),
    ),
    ("OpenAI API key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{30,}\b")),
)
_GENERIC_SECRET = re.compile(
    r"(?im)\b(api[_-]?key|client[_-]?secret|access[_-]?token|password|passwd)\b"
    r"\s*[:=]\s*[\"']?([^\s\"',}{]{8,})"
)


@dataclass(frozen=True)
class SensitiveDataFinding:
    """A high-confidence sensitive-data match without the secret value."""

    path: Path
    reason: str


class SensitiveDataError(ValueError):
    """Raised before Codex starts when repository data looks sensitive."""


def find_sensitive_data(repository: Path) -> tuple[SensitiveDataFinding, ...]:
    """Return high-confidence secret findings without exposing matched values."""
    findings: list[SensitiveDataFinding] = []

    for path in repository.rglob("*"):
        relative_path = path.relative_to(repository)
        if any(part in _SKIPPED_DIRECTORIES for part in relative_path.parts):
            continue
        if path.is_symlink():
            try:
                path.resolve().relative_to(repository)
            except (OSError, RuntimeError, ValueError):
                findings.append(
                    SensitiveDataFinding(relative_path, "symlink leaves repository")
                )
            continue
        if not path.is_file():
            continue

        filename_reason = _sensitive_filename_reason(path.name)
        if filename_reason:
            findings.append(SensitiveDataFinding(relative_path, filename_reason))
            continue

        try:
            if path.stat().st_size > _MAX_SCANNED_FILE_SIZE:
                continue
            raw_content = path.read_bytes()
        except OSError:
            continue
        if b"\x00" in raw_content:
            continue

        reason = _content_reason(raw_content.decode("utf-8", errors="ignore"))
        if reason:
            findings.append(SensitiveDataFinding(relative_path, reason))

    return tuple(findings)


def assert_repository_has_no_sensitive_data(repository: Path) -> None:
    """Refuse to start Codex when a preflight finding is present."""
    findings = find_sensitive_data(repository)
    if not findings:
        return

    details = ", ".join(f"{finding.path} ({finding.reason})" for finding in findings)
    raise SensitiveDataError(
        "Refusing to send a repository with potentially sensitive data to Codex: "
        f"{details}. Remove or redact the data before retrying."
    )


def _sensitive_filename_reason(filename: str) -> str | None:
    lowered = filename.lower()
    if lowered in _SENSITIVE_FILENAMES:
        return "sensitive filename"
    if lowered.startswith(".env."):
        suffix = lowered.removeprefix(".env.")
        if suffix not in _SAFE_ENV_SUFFIXES:
            return "environment file"
    if Path(lowered).suffix in _SENSITIVE_SUFFIXES:
        return "credential or private-key file"
    if lowered.startswith("service-account") and lowered.endswith(".json"):
        return "service-account file"
    return None


def _content_reason(content: str) -> str | None:
    for reason, signature in _SIGNATURES:
        if signature.search(content):
            return reason

    for match in _GENERIC_SECRET.finditer(content):
        value = match.group(2).strip().lower()
        if not _looks_like_placeholder(value):
            return f"hardcoded {match.group(1)}"
    return None


def _looks_like_placeholder(value: str) -> bool:
    placeholders = (
        "changeme",
        "dummy",
        "example",
        "placeholder",
        "replace_me",
        "replace-me",
        "sample",
        "test-only",
    )
    return value.startswith(("${", "{{", "<")) or any(
        placeholder in value for placeholder in placeholders
    )
