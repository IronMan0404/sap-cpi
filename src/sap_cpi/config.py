"""Configuration loading without exposing service-key secrets."""

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from dotenv import load_dotenv


class ConfigurationError(ValueError):
    """Raised when local CPI configuration is missing or invalid."""


@dataclass(frozen=True)
class Settings:
    client_id: str
    client_secret: str
    token_url: str
    api_url: str
    timeout: float = 30.0
    api_path: str = "/api/v1"

    @property
    def api_root(self) -> str:
        return f"{self.api_url}{self.api_path}"


def _required_string(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigurationError(f"Service key field '{name}' is missing or invalid")
    return value.strip()


def _https_url(value: Any, name: str) -> str:
    url = _required_string(value, name).rstrip("/")
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ConfigurationError(f"Service key field '{name}' must be an HTTPS URL")
    return url


def _api_path(value: Any) -> str:
    path = _required_string(value, "api_path") if value else "/api/v1"
    return "/" + path.strip("/")


def load_settings(path: str | Path | None = None) -> Settings:
    load_dotenv()
    explicit_path = path is not None
    env_client_id = os.getenv("CPI_CLIENT_ID")
    env_client_secret = os.getenv("CPI_CLIENT_SECRET")
    env_token_url = os.getenv("CPI_TOKEN_URL")
    env_api_url = os.getenv("CPI_API_URL")
    if not explicit_path and all((env_client_id, env_client_secret, env_token_url, env_api_url)):
        try:
            timeout = float(os.getenv("CPI_TIMEOUT", "30"))
        except ValueError as exc:
            raise ConfigurationError("CPI_TIMEOUT must be a number") from exc
        if timeout <= 0:
            raise ConfigurationError("CPI_TIMEOUT must be greater than zero")
        return Settings(
            client_id=_required_string(env_client_id, "clientid"),
            client_secret=_required_string(env_client_secret, "clientsecret"),
            token_url=_required_string(env_token_url, "tokenurl"),
            api_url=_https_url(env_api_url, "url"),
            timeout=timeout,
            api_path=_api_path(os.getenv("CPI_API_PATH", "/api/v1")),
        )
    key_path = Path(path or os.getenv("CPI_SERVICE_KEY_FILE", "./DEMO-API-KEY.json"))
    try:
        document = json.loads(key_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigurationError(f"Service key file not found: {key_path}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigurationError(f"Service key file is not valid JSON: {key_path}") from exc
    except OSError as exc:
        raise ConfigurationError(f"Could not read service key file: {key_path}") from exc

    oauth = document.get("oauth") if isinstance(document, dict) else None
    if not isinstance(oauth, dict):
        raise ConfigurationError("Service key must contain an 'oauth' object")

    client_id = (None if explicit_path else os.getenv("CPI_CLIENT_ID")) or oauth.get("clientid")
    client_secret = (None if explicit_path else os.getenv("CPI_CLIENT_SECRET")) or oauth.get("clientsecret")
    token_url = (None if explicit_path else os.getenv("CPI_TOKEN_URL")) or oauth.get("tokenurl")
    api_url = (None if explicit_path else os.getenv("CPI_API_URL")) or oauth.get("url")
    try:
        timeout = float(os.getenv("CPI_TIMEOUT", "30"))
    except ValueError as exc:
        raise ConfigurationError("CPI_TIMEOUT must be a number") from exc
    if timeout <= 0:
        raise ConfigurationError("CPI_TIMEOUT must be greater than zero")

    return Settings(
        client_id=_required_string(client_id, "clientid"),
        client_secret=_required_string(client_secret, "clientsecret"),
        token_url=_required_string(token_url, "tokenurl"),
        api_url=_https_url(api_url, "url"),
        timeout=timeout,
        api_path=_api_path(os.getenv("CPI_API_PATH", "/api/v1")),
    )
