from dataclasses import dataclass

from sap_cpi.client import CPIClient
from sap_cpi.config import Settings


@dataclass
class Response:
    payload: dict
    status_code: int = 200
    headers: dict[str, str] | None = None
    content: bytes = b"{}"

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests
            raise requests.HTTPError(response=self)

    def json(self):
        return self.payload


class Token:
    def get_token(self):
        return "token"


class Session:
    def __init__(self, response):
        self.response = response
        self.url = None
        self.kwargs = None

    def request(self, method, url, **kwargs):
        self.url, self.kwargs = url, kwargs
        return self.response

    def get(self, url, **kwargs):
        return Response({"csrf": True}, headers={"X-CSRF-Token": "csrf-token"})


def test_api_requests_use_configured_service_root():
    settings = Settings("id", "secret", "https://auth", "https://tenant.example")
    client = CPIClient(settings, Token())
    session = Session(Response({"d": {"results": []}}))
    client.session = session
    client.transport.session = session

    client.list_packages()

    assert session.url == "https://tenant.example/api/v1/IntegrationPackages"
    assert session.kwargs["headers"]["Authorization"] == "Bearer token"


def test_health_404_explains_api_client_requirement():
    settings = Settings("id", "secret", "https://auth", "https://tenant.example")
    client = CPIClient(settings, Token())
    client.transport.session = Session(Response({}, status_code=404))

    import pytest
    with pytest.raises(RuntimeError, match="API-client service instance"):
        client.health()


def test_update_flow_uses_active_artifact_endpoint(tmp_path):
    settings = Settings("id", "secret", "https://auth", "https://tenant.example")
    client = CPIClient(settings, Token())
    bundle = tmp_path / "flow.zip"
    bundle.write_bytes(b"zip-content")
    response = Response({"updated": True})
    session = Session(response)
    client.transport.session = session

    client.update_flow("FLOW_ID", "Flow Name", bundle)

    assert session.url == "https://tenant.example/api/v1/IntegrationDesigntimeArtifacts(Id='FLOW_ID',Version='active')"
    assert session.kwargs["json"]["Name"] == "Flow Name"
    assert "ArtifactContent" in session.kwargs["json"]
