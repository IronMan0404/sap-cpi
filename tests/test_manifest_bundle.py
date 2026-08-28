import zipfile

from sap_cpi.bundle import build_flow_bundle
from sap_cpi.manifest import load_manifest


def test_manifest_and_template_build(tmp_path):
    template = tmp_path / "template.zip"
    with zipfile.ZipFile(template, "w") as archive:
        archive.writestr("META-INF/flow.xml", "<?xml version='1.0'?><url>{{endpoint}}</url>")
    manifest_file = tmp_path / "cpi.yaml"
    manifest_file.write_text(
        "package:\n  id: PKG\n  name: Package\n  version: 1.0.0\n"
        "flow:\n  id: FLOW\n  name: Flow\n  version: 1.0.0\n"
        f"  template: {template.name}\n  configuration:\n    endpoint: https://example.test\n",
        encoding="utf-8",
    )
    manifest = load_manifest(manifest_file)
    output = build_flow_bundle(manifest.flow, tmp_path / "build.zip")
    with zipfile.ZipFile(output) as archive:
        assert "https://example.test" in archive.read("META-INF/flow.xml").decode()
