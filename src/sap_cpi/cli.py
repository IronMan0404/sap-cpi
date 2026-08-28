"""Command-line interface for the SAP Cloud Integration client."""

import argparse
import hashlib
import json
import sys
import tempfile
import time
import zipfile
from dataclasses import replace
from pathlib import Path
from typing import Any

from .client import CPIClient, CPIClientError
from .bundle import build_flow_bundle
from .config import ConfigurationError, load_settings
from .manifest import load_manifest


def _bundle_digest(path: str | Path) -> str:
    digest = hashlib.sha256()
    with zipfile.ZipFile(path) as bundle:
        for name in sorted(item for item in bundle.namelist() if not item.endswith("/")):
            digest.update(name.encode("utf-8"))
            digest.update(b"\0")
            digest.update(bundle.read(name))
            digest.update(b"\0")
    return digest.hexdigest()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SAP Cloud Integration client")
    parser.add_argument("--key-file", help="Path to a local service-key JSON file")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("health", "status", "list-packages", "list-artifacts"):
        commands.add_parser(name)
    commands.add_parser("login", help="Validate OAuth access to the CPI tenant")

    legacy = commands.add_parser("list", help="List CPI content or message processing logs")
    legacy_commands = legacy.add_subparsers(dest="list_command", required=True)
    legacy_commands.add_parser("content")
    messages = legacy_commands.add_parser("messages")
    messages.add_argument("-e", "--errors", action="store_true")
    messages.add_argument("-top", "--top", type=int, default=10)
    messages.add_argument("-f", "--from-time", dest="start")
    messages.add_argument("-t", "--to-time", dest="end")

    download = commands.add_parser("download", help="Download an integration-flow artifact")
    download.add_argument("-id", "--id", dest="artifact_id", required=True)
    download.add_argument("-o", "--output")
    download.add_argument("--version", default="active")

    package = commands.add_parser("package", help="Manage integration packages")
    package_commands = package.add_subparsers(dest="package_command", required=True)
    package_create = package_commands.add_parser("create")
    package_create.add_argument("--manifest", required=True)
    package_create.add_argument("--apply", action="store_true")
    package_download = package_commands.add_parser("download")
    package_download.add_argument("--id", required=True)
    package_download.add_argument("--output", required=True)

    flow = commands.add_parser("flow", help="Build and deploy integration flows")
    flow_commands = flow.add_subparsers(dest="flow_command", required=True)
    flow_build = flow_commands.add_parser("build")
    flow_build.add_argument("--manifest", required=True)
    flow_build.add_argument("--output", default="build/flow.zip")
    flow_pull = flow_commands.add_parser("pull")
    flow_pull.add_argument("--manifest", required=True)
    flow_pull.add_argument("--output", default=None)
    flow_pull.add_argument("--version", default="active")
    flow_upload = flow_commands.add_parser("upload")
    flow_upload.add_argument("--manifest", required=True)
    flow_upload.add_argument("--bundle", default=None)
    flow_upload.add_argument("--apply", action="store_true")
    flow_upload.add_argument("--version", default=None)
    flow_update = flow_commands.add_parser("update")
    flow_update.add_argument("--manifest", required=True)
    flow_update.add_argument("--bundle", default=None)
    flow_update.add_argument("--apply", action="store_true")
    flow_update.add_argument("--version", default=None)
    flow_version = flow_commands.add_parser("version")
    flow_version.add_argument("--manifest", required=True)
    flow_version.add_argument("--apply", action="store_true")
    flow_version.add_argument("--version", default=None)
    flow_deploy = flow_commands.add_parser("deploy")
    flow_deploy.add_argument("--manifest", required=True)
    flow_deploy.add_argument("--apply", action="store_true")
    flow_deploy.add_argument("--version", default=None)
    flow_verify = flow_commands.add_parser("verify")
    flow_verify.add_argument("--manifest", required=True)
    flow_verify.add_argument("--bundle", required=True)
    flow_verify.add_argument("--version", default="active")
    flow_status = flow_commands.add_parser("status")
    flow_status.add_argument("--id", required=True)
    flow_status.add_argument("--task-id")
    return parser


def _run(args: argparse.Namespace, client: CPIClient) -> Any:
    if args.command == "login":
        client.authenticate()
        return {"status": "authenticated", "apiUrl": client.settings.api_url}
    if args.command in ("health", "status"):
        return client.health()
    if args.command == "list-packages":
        return client.list_packages()
    if args.command == "list-artifacts":
        return client.list_artifacts()
    if args.command == "list":
        if args.list_command == "content":
            return client.list_content()
        return client.list_messages(args.top, args.errors, args.start, args.end)
    if args.command == "package":
        if args.package_command == "download":
            path = client.download_package(args.id, args.output)
            return {"status": "downloaded", "file": str(path)}
        manifest = load_manifest(args.manifest)
        if manifest.package.template is None:
            raise ConfigurationError("Manifest field 'package.template' is required for package create")
        if not manifest.package.template.is_file():
            raise ConfigurationError(f"Package template not found: {manifest.package.template}")
        if not args.apply:
            return {"dryRun": True, "operation": "create-package", "packageId": manifest.package.id, "bundle": str(manifest.package.template)}
        return client.create_package(manifest.package.id, manifest.package.name, manifest.package.version, manifest.package.template)
    if args.command == "flow":
        if args.flow_command == "build":
            manifest = load_manifest(args.manifest)
            path = build_flow_bundle(manifest.flow, args.output)
            return {"status": "built", "file": str(path)}
        if args.flow_command == "pull":
            manifest = load_manifest(args.manifest)
            output = args.output or str(manifest.flow.template)
            path = client.download_artifact(manifest.flow.id, output, args.version)
            return {"status": "pulled", "file": str(path), "artifactId": manifest.flow.id, "version": args.version}
        if args.flow_command == "status":
            return client.runtime_status(args.id) if not args.task_id else client.deployment_status(args.task_id)
        manifest = load_manifest(args.manifest)
        if getattr(args, "version", None):
            manifest = replace(manifest, flow=replace(manifest.flow, version=args.version))
        if args.flow_command == "upload":
            bundle = args.bundle or f"build/{manifest.flow.id}.zip"
            if not Path(bundle).is_file():
                raise ConfigurationError(f"Flow bundle not found: {bundle}")
            if not args.apply:
                return {"dryRun": True, "operation": "upload-flow", "artifactId": manifest.flow.id, "bundle": bundle}
            return client.upload_flow(manifest.package.id, manifest.flow.id, manifest.flow.name, manifest.flow.version, bundle)
        if args.flow_command == "update":
            bundle = args.bundle or f"build/{manifest.flow.id}.zip"
            if not Path(bundle).is_file():
                raise ConfigurationError(f"Flow bundle not found: {bundle}")
            if not args.apply:
                return {"dryRun": True, "operation": "update-flow", "artifactId": manifest.flow.id, "bundle": bundle}
            return client.update_flow(manifest.flow.id, manifest.flow.name, bundle)
        if args.flow_command == "version":
            if not args.apply:
                return {"dryRun": True, "operation": "save-flow-version", "artifactId": manifest.flow.id, "version": manifest.flow.version}
            return client.save_flow_version(manifest.flow.id, manifest.flow.version)
        if args.flow_command == "verify":
            bundle = Path(args.bundle)
            if not bundle.is_file():
                raise ConfigurationError(f"Flow bundle not found: {bundle}")
            with tempfile.TemporaryDirectory() as directory:
                downloaded = client.download_artifact(manifest.flow.id, Path(directory) / "cpi-flow.zip", args.version)
                expected_hash = _bundle_digest(bundle)
                actual_hash = _bundle_digest(downloaded)
            if expected_hash != actual_hash:
                raise CPIClientError(
                    f"Uploaded artifact checksum mismatch for {manifest.flow.id} "
                    f"version {args.version}: expected {expected_hash}, got {actual_hash}"
                )
            return {"status": "verified", "artifactId": manifest.flow.id, "version": args.version, "sha256": actual_hash}
        if args.flow_command == "deploy":
            if not args.apply:
                return {"dryRun": True, "operation": "deploy-flow", "artifactId": manifest.flow.id, "version": manifest.flow.version}
            task = client.deploy_flow(manifest.flow.id, manifest.flow.version)
            task_id = task.get("TaskId") if isinstance(task, dict) else None
            if not task_id and isinstance(task, dict) and isinstance(task.get("d"), dict):
                task_id = task["d"].get("TaskId")
            if not task_id:
                raise CPIClientError("Deployment response did not contain TaskId")
            deadline = time.monotonic() + manifest.deployment.timeout_seconds
            status = None
            while time.monotonic() < deadline:
                status = client.deployment_status(task_id)
                text = json.dumps(status).lower()
                if "success" in text or "failed" in text or "error" in text:
                    break
                time.sleep(manifest.deployment.poll_seconds)
            return {"taskId": task_id, "deployment": status, "runtime": client.runtime_status(manifest.flow.id)}
    if args.command == "download":
        output = args.output or f"{args.artifact_id}-{args.version}.zip"
        path = client.download_artifact(args.artifact_id, output, args.version)
        return {"status": "downloaded", "file": str(path)}
    raise ConfigurationError(f"Unsupported command: {args.command}")


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        result = _run(args, CPIClient(load_settings(args.key_file)))
        print(json.dumps(result, indent=2))
        return 0
    except (ConfigurationError, CPIClientError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
