"""Tests for the Railway deployment configuration."""

from __future__ import annotations

import tomllib
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
RAILWAY_CONFIG_PATH = REPOSITORY_ROOT / "railway.toml"


def load_railway_config() -> dict[str, object]:
    """Load the repository Railway configuration."""

    with RAILWAY_CONFIG_PATH.open("rb") as file:
        return tomllib.load(file)


def test_railway_uses_the_production_dockerfile() -> None:
    config = load_railway_config()
    build = config["build"]

    assert isinstance(build, dict)
    assert build["builder"] == "DOCKERFILE"
    assert build["dockerfilePath"] == "Dockerfile"
    assert (REPOSITORY_ROOT / "Dockerfile").is_file()


def test_railway_uses_readiness_for_deployment_healthchecks() -> None:
    config = load_railway_config()
    deploy = config["deploy"]

    assert isinstance(deploy, dict)
    assert deploy["healthcheckPath"] == "/ready"
    assert deploy["healthcheckTimeout"] == 120


def test_railway_restarts_failed_processes_with_a_bounded_policy() -> None:
    config = load_railway_config()
    deploy = config["deploy"]

    assert isinstance(deploy, dict)
    assert deploy["restartPolicyType"] == "ON_FAILURE"
    assert deploy["restartPolicyMaxRetries"] == 10


def test_railway_does_not_override_the_docker_start_command() -> None:
    config = load_railway_config()
    deploy = config["deploy"]

    assert isinstance(deploy, dict)
    assert "startCommand" not in deploy
