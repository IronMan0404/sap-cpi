from dataclasses import dataclass

from sap_cpi.auth import TokenProvider
from sap_cpi.config import Settings


@dataclass
class FakeResponse:
    payload: dict
    def raise_for_status(self): pass
    def json(self): return self.payload


class FakeSession:
    def __init__(self): self.calls = 0
    def post(self, *args, **kwargs):
        self.calls += 1
        return FakeResponse({"access_token": "token", "expires_in": 3600})


def test_token_is_cached():
    settings = Settings("id", "secret", "https://auth", "https://api")
    session = FakeSession()
    provider = TokenProvider(settings, session)
    assert provider.get_token() == provider.get_token() == "token"
    assert session.calls == 1
