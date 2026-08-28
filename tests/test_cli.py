from argparse import Namespace
import zipfile

from sap_cpi.cli import _build_parser, _bundle_digest, _run
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


def test_bundle_digest_ignores_cpi_generated_metadata(tmp_path):
    first = tmp_path / "first.zip"
    second = tmp_path / "second.zip"
    for target, metadata in ((first, "one"), (second, "two")):
        with zipfile.ZipFile(target, "w") as archive:
            archive.writestr("src/main/resources/scenario.iflw", "design")
            archive.writestr("src/main/resources/script.groovy", "script")
            archive.writestr("metainfo.prop", metadata)
            archive.writestr("src/main/resources/parameters.prop", metadata)
    assert _bundle_digest(first) == _bundle_digest(second)
