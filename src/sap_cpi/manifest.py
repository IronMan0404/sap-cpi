"""Validated YAML manifest for repeatable CPI content delivery."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .config import ConfigurationError


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigurationError(f"Manifest field '{field}' is required")
    return value.strip()


@dataclass(frozen=True)
class PackageSpec:
    id: str
    name: str
    version: str
    template: Path | None


@dataclass(frozen=True)
class FlowSpec:
    id: str
    name: str
    version: str
    template: Path
    configuration: dict[str, Any]


@dataclass(frozen=True)
class DeploymentSpec:
    poll_seconds: float = 5.0
    timeout_seconds: float = 300.0


@dataclass(frozen=True)
class DeliveryManifest:
    package: PackageSpec
    flow: FlowSpec
    deployment: DeploymentSpec
    source: Path


def load_manifest(path: str | Path) -> DeliveryManifest:
    source = Path(path).resolve()
    try:
        document = yaml.safe_load(source.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigurationError(f"Manifest file not found: {path}") from exc
    except (OSError, yaml.YAMLError) as exc:
        raise ConfigurationError(f"Could not read manifest: {path}") from exc
    if not isinstance(document, dict):
        raise ConfigurationError("Manifest root must be an object")
    package = document.get("package") or {}
    flow = document.get("flow") or {}
    deployment = document.get("deployment") or {}
    if not isinstance(package, dict) or not isinstance(flow, dict) or not isinstance(deployment, dict):
        raise ConfigurationError("Manifest package, flow, and deployment sections must be objects")
    template = package.get("template")
    package_spec = PackageSpec(
        _text(package.get("id"), "package.id"),
        _text(package.get("name"), "package.name"),
        _text(package.get("version"), "package.version"),
        (source.parent / template).resolve() if template else None,
    )
    configuration = flow.get("configuration", {})
    if not isinstance(configuration, dict):
        raise ConfigurationError("Manifest field 'flow.configuration' must be an object")
    try:
        poll = float(deployment.get("poll_seconds", 5))
        timeout = float(deployment.get("timeout_seconds", 300))
    except (TypeError, ValueError) as exc:
        raise ConfigurationError("Deployment polling values must be numbers") from exc
    if poll <= 0 or timeout <= 0:
        raise ConfigurationError("Deployment polling values must be greater than zero")
    return DeliveryManifest(
        package_spec,
        FlowSpec(_text(flow.get("id"), "flow.id"), _text(flow.get("name"), "flow.name"), _text(flow.get("version"), "flow.version"), (source.parent / _text(flow.get("template"), "flow.template")).resolve(), configuration),
        DeploymentSpec(poll, timeout),
        source,
    )
