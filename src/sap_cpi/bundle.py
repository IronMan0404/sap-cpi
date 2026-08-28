"""Build and validate CPI artifact bundles from ZIP templates."""

from pathlib import Path
import zipfile

from .config import ConfigurationError
from .manifest import FlowSpec


def build_flow_bundle(spec: FlowSpec, output: str | Path) -> Path:
    if not spec.template.is_file():
        raise ConfigurationError(
            f"Flow template not found: {spec.template}. "
            "Place a valid SAP CPI flow ZIP at this path; see docs/cli-smoke-test.md"
        )
    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    replacements = {"{{ " + key + " }}": str(value) for key, value in spec.configuration.items()}
    replacements.update({"{{" + key + "}}": str(value) for key, value in spec.configuration.items()})
    try:
        with zipfile.ZipFile(spec.template) as source, zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as target:
            names = source.namelist()
            if not names:
                raise ConfigurationError("Flow template ZIP is empty")
            for item in source.infolist():
                content = source.read(item.filename)
                if not item.is_dir() and (content.startswith(b"<?xml") or b"{{" in content):
                    try:
                        text = content.decode("utf-8")
                    except UnicodeDecodeError:
                        text = ""
                    for old, new in replacements.items():
                        text = text.replace(old, new)
                    content = text.encode("utf-8")
                target.writestr(item, content)
    except zipfile.BadZipFile as exc:
        raise ConfigurationError(f"Flow template is not a valid ZIP: {spec.template}") from exc
    return destination
