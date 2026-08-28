from sap_cpi.transport import AuthenticatedTransport


class Token:
    def get_token(self):
        return "token"


class Response:
    status_code = 200
    headers = {"X-CSRF-Token": "csrf"}

    def raise_for_status(self):
        pass


class Session:
    def __init__(self):
        self.urls = []

    def get(self, url, **kwargs):
        self.urls.append(url)
        return Response()

    def request(self, method, url, **kwargs):
        self.urls.append(url)
        return Response()


def test_mutations_fetch_csrf_from_metadata():
    session = Session()
    transport = AuthenticatedTransport(Token(), 10, session, "https://tenant/api/v1/$metadata")
    transport.request("POST", "https://tenant/api/v1/IntegrationDesigntimeArtifacts", json={})
    assert session.urls == ["https://tenant/api/v1/$metadata", "https://tenant/api/v1/IntegrationDesigntimeArtifacts"]
