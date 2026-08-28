from argparse import Namespace

from sap_cpi.cli import _build_parser, _run
from sap_cpi.config import Settings


class Client:
    settings = Settings("id", "secret", "https://auth", "https://tenant")

    class tokens:
        @staticmethod
        def get_token():
            return "token"

    def health(self):
        return {"ok": True}

    def authenticate(self):
        return None


def test_status_is_health_alias():
    args = _build_parser().parse_args(["status"])
    assert _run(args, Client()) == {"ok": True}


def test_login_requests_oauth_token():
    args = Namespace(command="login")
    assert _run(args, Client())["status"] == "authenticated"


def test_flow_version_accepts_release_version_override():
    args = _build_parser().parse_args(
        ["flow", "version", "--manifest", "config/SAP_SMOKE_TEST.yaml", "--version", "1.0.1"]
    )
    assert args.version == "1.0.1"
