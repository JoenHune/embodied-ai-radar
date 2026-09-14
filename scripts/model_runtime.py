"""Explicit, allowlisted model configuration; never execute an env file."""
from __future__ import annotations

import os
import shlex
from pathlib import Path
from typing import MutableMapping

ROOT = Path(__file__).resolve().parents[1]
LLM_KEYS = {"LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL"}
LOGGER_KEYS = {"CODEX_PROXY_BASE_URL": "LLM_BASE_URL", "CODEX_PROXY_API_KEY": "LLM_API_KEY", "CODEX_PROXY_MODEL": "LLM_MODEL"}


class ModelConfigurationError(ValueError):
    """Fixed diagnostic codes only: values may contain credentials."""


def read_model_configuration(path: Path, *, loggerbot: bool = False, root: Path = ROOT) -> dict[str, str]:
    path = path.expanduser().resolve()
    if path.is_relative_to(root.resolve()):
        raise ModelConfigurationError("model_configuration_must_be_outside_repository")
    if not path.is_file():
        raise ModelConfigurationError("model_configuration_file_missing")
    mapping = LOGGER_KEYS if loggerbot else {key: key for key in LLM_KEYS}
    values = {}
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeError) as exc:
        raise ModelConfigurationError("model_configuration_unreadable") from exc
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        key, separator, value = line.partition("=")
        key = key.strip()
        if key not in mapping:
            if loggerbot:
                # Do not even parse unrelated Feishu/OAuth/private settings.
                continue
            raise ModelConfigurationError("unsupported_model_configuration_field")
        if not separator or mapping[key] in values:
            raise ModelConfigurationError("invalid_or_duplicate_model_configuration_field")
        try:
            parts = shlex.split(value.strip(), comments=True, posix=True)
        except ValueError as exc:
            raise ModelConfigurationError("invalid_model_configuration_value") from exc
        values[mapping[key]] = " ".join(parts)
    if loggerbot and not values.get("LLM_BASE_URL"):
        raise ModelConfigurationError("loggerbot_proxy_not_configured")
    return values


def load_model_configuration(*, env_file: Path | None = None, loggerbot_env_file: Path | None = None,
                             environ: MutableMapping[str, str] | None = None, root: Path = ROOT) -> dict:
    if env_file and loggerbot_env_file:
        raise ModelConfigurationError("choose_one_model_configuration_source")
    target = os.environ if environ is None else environ
    path = loggerbot_env_file or env_file
    if not path:
        return {"source": "environment", "configured": bool(target.get("LLM_BASE_URL"))}
    values = read_model_configuration(path, loggerbot=bool(loggerbot_env_file), root=root)
    # An explicitly configured endpoint owns its credential pair. Never mix a
    # process endpoint with an unrelated file's secret or vice versa.
    if target.get("LLM_BASE_URL"):
        return {"source": "environment", "configured": True}
    for key in LLM_KEYS:
        target.pop(key, None)
    target.update(values)
    return {"source": "loggerbot_model_fields" if loggerbot_env_file else "runtime_file",
            "configured": bool(target.get("LLM_BASE_URL"))}
