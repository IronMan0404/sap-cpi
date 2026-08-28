"""OAuth 2.0 client-credentials authentication for SAP BTP."""

from dataclasses import dataclass
import time

import requests

from .config import Settings


class AuthenticationError(RuntimeError):
    """Raised when an OAuth token cannot be obtained."""


@dataclass
class TokenProvider:
    settings: Settings
    session: requests.Session | None = None

    def __post_init__(self) -> None:
        self._session = self.session or requests.Session()
        self._token: str | None = None
        self._expires_at = 0.0

    def get_token(self) -> str:
        if self._token and time.monotonic() < self._expires_at:
            return self._token
        try:
            response = self._session.post(
                self.settings.token_url,
                data={"grant_type": "client_credentials"},
                auth=(self.settings.client_id, self.settings.client_secret),
                timeout=self.settings.timeout,
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise AuthenticationError("Could not obtain SAP OAuth access token") from exc

        token = payload.get("access_token")
        if not isinstance(token, str) or not token:
            raise AuthenticationError("SAP OAuth response did not contain access_token")
        expires_in = payload.get("expires_in", 300)
        try:
            lifetime = max(float(expires_in), 1.0)
        except (TypeError, ValueError):
            lifetime = 300.0
        self._token = token
        self._expires_at = time.monotonic() + lifetime - min(30.0, lifetime / 2)
        return token
