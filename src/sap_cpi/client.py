"""Minimal SAP Cloud Integration OData API client."""

import base64
from pathlib import Path
from typing import Any

import requests

from .auth import AuthenticationError, TokenProvider
from .config import Settings
from .transport import AuthenticatedTransport, TransportError


class CPIClientError(RuntimeError):
    """Raised for non-successful CPI API requests."""


class CPIClient:
    def __init__(self, settings: Settings, token_provider: TokenProvider | None = None) -> None:
        self.settings = settings
        self.session = requests.Session()
        self.tokens = token_provider or TokenProvider(settings, self.session)
        self.transport = AuthenticatedTransport(self.tokens, settings.timeout, self.session, f"{settings.api_root}/$metadata")

    def _request(self, method: str, resource: str, **kwargs: Any) -> requests.Response:
        url = f"{self.settings.api_root}/{resource.lstrip('/')}"
        try:
            return self.transport.request(method, url, **kwargs)
        except TransportError as exc:
            message = str(exc)
            if "(HTTP 404)" in message:
                message += ". Verify the service key URL is from an API-client service instance with Cloud Integration API roles"
            raise CPIClientError(message) from exc

    def _get(self, resource: str) -> Any:
        response = self._request("GET", resource)
        try:
            return response.json()
        except ValueError as exc:
            raise CPIClientError("CPI API returned invalid JSON") from exc

    def authenticate(self) -> None:
        """Validate OAuth credentials without making an OData request."""
        try:
            self.tokens.get_token()
        except AuthenticationError as exc:
            raise CPIClientError("CPI OAuth authentication failed") from exc

    def _json_request(self, method: str, resource: str, payload: dict[str, Any] | None = None) -> Any:
        response = self._request(method, resource, json=payload) if payload is not None else self._request(method, resource)
        if not response.content:
            return None
        try:
            return response.json()
        except ValueError as exc:
            raise CPIClientError("CPI API returned invalid JSON") from exc

    @staticmethod
    def _bundle_payload(bundle: str | Path, field: str) -> dict[str, str]:
        path = Path(bundle)
        if not path.is_file():
            raise CPIClientError(f"Artifact bundle not found: {path}")
        return {field: base64.b64encode(path.read_bytes()).decode("ascii")}

    def create_package(self, package_id: str, name: str, version: str, bundle: str | Path, overwrite: bool = False) -> Any:
        payload = self._bundle_payload(bundle, "PackageContent")
        payload.update({"Id": package_id, "Name": name, "Version": version})
        suffix = "?Overwrite=true" if overwrite else ""
        return self._json_request("POST", f"IntegrationPackages{suffix}", payload)

    def upload_flow(self, package_id: str, artifact_id: str, name: str, version: str, bundle: str | Path) -> Any:
        payload = self._bundle_payload(bundle, "ArtifactContent")
        # CPI assigns the draft version during create; sending Version causes HTTP 400.
        payload.update({"Id": artifact_id, "Name": name, "PackageId": package_id})
        return self._json_request("POST", "IntegrationDesigntimeArtifacts", payload)

    def update_flow(self, artifact_id: str, name: str, bundle: str | Path) -> Any:
        """Replace an existing artifact's active draft with an exported bundle."""
        payload = self._bundle_payload(bundle, "ArtifactContent")
        payload["Name"] = name
        resource = f"IntegrationDesigntimeArtifacts(Id='{artifact_id}',Version='active')"
        return self._json_request("PUT", resource, payload)

    def download_package(self, package_id: str, output: str | Path) -> Path:
        if not package_id.strip():
            raise CPIClientError("Package ID is required")
        response = self._request("GET", f"IntegrationPackages('{package_id}')/$value", headers={"Accept": "application/octet-stream"})
        destination = Path(output)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(response.content)
        return destination

    def save_flow_version(self, artifact_id: str, version: str) -> Any:
        resource = f"IntegrationDesigntimeArtifactSaveAsVersion?Id='{artifact_id}'&SaveAsVersion='{version}'"
        return self._json_request("POST", resource)

    def deploy_flow(self, artifact_id: str, version: str) -> Any:
        resource = f"DeployIntegrationDesigntimeArtifact?Id='{artifact_id}'&Version='{version}'"
        response = self._request("POST", resource)
        if not response.content:
            return None
        try:
            return response.json()
        except ValueError as exc:
            # Some CPI tenants return the asynchronous deployment TaskId as
            # plain text with HTTP 202 instead of a JSON document.
            task_id = response.text.strip()
            if response.status_code == 202 and task_id:
                return {"TaskId": task_id}
            raise CPIClientError("CPI API returned invalid JSON") from exc

    def deployment_status(self, task_id: str) -> Any:
        return self._json_request("GET", f"BuildAndDeployStatus(TaskId='{task_id}')")

    def runtime_status(self, artifact_id: str) -> Any:
        return self._json_request("GET", f"IntegrationRuntimeArtifacts('{artifact_id}')")

    def health(self) -> Any:
        """Read a lightweight resource to validate authentication and API access."""
        return self._get("IntegrationPackages?$top=1")

    def list_packages(self) -> Any:
        return self._get("IntegrationPackages")

    def list_artifacts(self) -> Any:
        return self._get("IntegrationDesigntimeArtifacts")

    def list_content(self) -> dict[str, Any]:
        try:
            return {"packages": self.list_packages(), "artifacts": self.list_artifacts()}
        except CPIClientError as exc:
            raise CPIClientError(f"Could not list integration content: {exc}") from exc

    def list_messages(self, top: int = 10, error_only: bool = False, start: str | None = None, end: str | None = None) -> Any:
        filters = []
        if error_only:
            filters.append("Status eq 'FAILED'")
        if start:
            filters.append(f"LogStart ge datetime'{start}'")
        if end:
            filters.append(f"LogEnd le datetime'{end}'")
        params = [f"$top={max(1, top)}", "$orderby=LogStart desc"]
        if filters:
            params.append("$filter=" + " and ".join(filters))
        return self._get("MessageProcessingLogs?" + "&".join(params))

    def download_artifact(self, artifact_id: str, output: str | Path, version: str = "active") -> Path:
        if not artifact_id.strip():
            raise CPIClientError("Artifact ID is required")
        resource = f"IntegrationDesigntimeArtifacts(Id='{artifact_id}',Version='{version}')/$value"
        response = self._request("GET", resource, headers={"Accept": "application/octet-stream"})
        content = response.content
        if "json" in response.headers.get("Content-Type", "").lower():
            try:
                artifact = response.json()
                encoded = artifact.get("ArtifactContent")
                if not encoded:
                    raise CPIClientError("Artifact response did not contain ArtifactContent")
                content = base64.b64decode(encoded)
            except (ValueError, KeyError) as exc:
                raise CPIClientError("Artifact response was not valid base64 JSON") from exc
        destination = Path(output)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
        return destination
