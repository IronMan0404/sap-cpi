"""Authenticated HTTP transport shared by CPI API operations."""

from typing import Any

import requests

from .auth import AuthenticationError, TokenProvider


class TransportError(RuntimeError):
    """Raised when an authenticated HTTP request fails."""


class AuthenticatedTransport:
    def __init__(self, token_provider: TokenProvider, timeout: float, session: requests.Session | None = None, csrf_url: str | None = None) -> None:
        self.tokens = token_provider
        self.timeout = timeout
        self.session = session or requests.Session()
        self.csrf_url = csrf_url

    def request(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        headers = {"Authorization": f"Bearer {self.tokens.get_token()}", "Accept": "application/json"}
        headers.update(kwargs.pop("headers", {}))
        try:
            if method.upper() in {"POST", "PUT", "PATCH", "DELETE"}:
                csrf = self.session.get(
                    self.csrf_url or url,
                    headers={**headers, "X-CSRF-Token": "Fetch"},
                    timeout=self.timeout,
                )
                csrf.raise_for_status()
                token = csrf.headers.get("X-CSRF-Token")
                if token:
                    headers["X-CSRF-Token"] = token
            response = self.session.request(method, url, headers=headers, timeout=self.timeout, **kwargs)
            response.raise_for_status()
            return response
        except AuthenticationError as exc:
            raise TransportError("CPI OAuth authentication failed") from exc
        except requests.RequestException as exc:
            status = getattr(getattr(exc, "response", None), "status_code", None)
            suffix = f" (HTTP {status})" if status else ""
            response = getattr(exc, "response", None)
            detail = ""
            response_text = getattr(response, "text", "") if response is not None else ""
            if response_text:
                try:
                    payload = response.json()
                    detail = payload.get("error", {}).get("message", {}).get("value", "")
                    if not detail:
                        detail = payload.get("error", {}).get("message", "")
                except (ValueError, AttributeError):
                    detail = ""
            if detail:
                suffix += f": {detail}"
            raise TransportError(f"CPI API request failed{suffix}") from exc
