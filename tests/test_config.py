import json

import pytest

from sap_cpi.config import ConfigurationError, load_settings


def write_key(path):
    path.write_text(json.dumps({"oauth": {
        "clientid": "client", "clientsecret": "secret",
        "tokenurl": "https://auth.example/token", "url": "https://tenant.example"
    }}), encoding="utf-8")


def test_load_settings(tmp_path):
    key = tmp_path / "key.json"
    write_key(key)
    settings = load_settings(key)
    assert settings.client_id == "client"
    assert settings.api_url == "https://tenant.example"
    assert settings.api_root == "https://tenant.example/api/v1"


def test_rejects_non_https_api_url(tmp_path):
    key = tmp_path / "key.json"
    write_key(key)
    document = json.loads(key.read_text(encoding="utf-8"))
    document["oauth"]["url"] = "http://tenant.example"
    key.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(ConfigurationError, match="HTTPS"):
        load_settings(key)


def test_missing_key_is_safe(tmp_path):
    with pytest.raises(ConfigurationError, match="not found"):
        load_settings(tmp_path / "missing.json")


def test_invalid_key_shape(tmp_path):
    key = tmp_path / "key.json"
    key.write_text("{}", encoding="utf-8")
    with pytest.raises(ConfigurationError, match="oauth"):
        load_settings(key)
