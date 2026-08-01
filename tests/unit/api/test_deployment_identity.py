"""Tests for runtime deployment identity."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from wc26.api import create_app
from wc26.api.deployment import (
    resolve_deployment_identity,
)
from wc26.api.settings import ApiSettings
from wc26.deployment.dataset_integrity import (
    load_dataset_manifest,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
MANIFEST_PATH = REPOSITORY_ROOT / "config" / "runtime_dataset_manifest.json"


def test_resolve_local_deployment_identity() -> None:
    identity = resolve_deployment_identity(
        {},
        manifest_path=Path("missing-manifest.json"),
    )

    assert identity.provider == "local"
    assert identity.commit_sha is None
    assert identity.branch is None
    assert identity.deployment_id is None
    assert identity.dataset_bundle_sha256 is None


def test_resolve_railway_deployment_identity() -> None:
    expected_bundle_sha256, _ = load_dataset_manifest(MANIFEST_PATH)

    identity = resolve_deployment_identity(
        {
            "RAILWAY_GIT_COMMIT_SHA": ("a" * 40),
            "RAILWAY_GIT_BRANCH": ("feat/cloud-deployment"),
            "RAILWAY_DEPLOYMENT_ID": ("deployment-123"),
        },
        manifest_path=MANIFEST_PATH,
    )

    assert identity.provider == "railway"
    assert identity.commit_sha == "a" * 40
    assert identity.branch == "feat/cloud-deployment"
    assert identity.deployment_id == "deployment-123"
    assert identity.dataset_bundle_sha256 == expected_bundle_sha256


def test_explicit_release_identity_overrides_platform_values() -> None:
    identity = resolve_deployment_identity(
        {
            "WC26_DEPLOYMENT_PROVIDER": ("Custom"),
            "WC26_RELEASE_SHA": "explicit-sha",
            "WC26_RELEASE_BRANCH": ("release/v1"),
            "WC26_DEPLOYMENT_ID": ("explicit-deployment"),
            "RAILWAY_GIT_COMMIT_SHA": ("railway-sha"),
            "RAILWAY_GIT_BRANCH": ("railway-branch"),
            "RAILWAY_DEPLOYMENT_ID": ("railway-deployment"),
        },
        manifest_path=Path("missing-manifest.json"),
    )

    assert identity.provider == "custom"
    assert identity.commit_sha == "explicit-sha"
    assert identity.branch == "release/v1"
    assert identity.deployment_id == "explicit-deployment"


def test_deployment_endpoint_exposes_runtime_identity(
    monkeypatch,
) -> None:
    expected_bundle_sha256, _ = load_dataset_manifest(MANIFEST_PATH)

    monkeypatch.setenv(
        "RAILWAY_GIT_COMMIT_SHA",
        "b" * 40,
    )
    monkeypatch.setenv(
        "RAILWAY_GIT_BRANCH",
        "feat/docker-deployment-foundation",
    )
    monkeypatch.setenv(
        "RAILWAY_DEPLOYMENT_ID",
        "deployment-456",
    )
    monkeypatch.setenv(
        "WC26_DATASET_MANIFEST_PATH",
        str(MANIFEST_PATH),
    )

    application = create_app(
        settings=ApiSettings(
            environment="production",
        )
    )

    with TestClient(application) as client:
        response = client.get("/deployment")

    assert response.status_code == 200
    assert response.json() == {
        "service": ("wc26-transfer-intelligence"),
        "version": "0.1.0",
        "environment": "production",
        "provider": "railway",
        "commit_sha": "b" * 40,
        "branch": ("feat/docker-deployment-foundation"),
        "deployment_id": "deployment-456",
        "dataset_bundle_sha256": (expected_bundle_sha256),
    }


def test_deployment_route_is_present_in_openapi() -> None:
    application = create_app()

    schema = application.openapi()

    assert "/deployment" in schema["paths"]
