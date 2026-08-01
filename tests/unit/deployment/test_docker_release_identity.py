"""Tests for Docker image release identity configuration."""

from __future__ import annotations

import re
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCKERFILE_PATH = REPOSITORY_ROOT / "Dockerfile"


def read_runtime_stage() -> str:
    """Return the final Docker runtime stage."""

    content = DOCKERFILE_PATH.read_text(encoding="utf-8")

    runtime_match = re.search(
        r"(?m)^FROM\s+.+\s+AS\s+runtime\s*$",
        content,
        flags=re.IGNORECASE,
    )

    if runtime_match is None:
        raise AssertionError("Docker runtime stage is missing.")

    runtime_start = runtime_match.start()

    next_stage = re.search(
        r"(?m)^FROM\s+",
        content[runtime_match.end() :],
    )

    if next_stage is None:
        return content[runtime_start:]

    runtime_end = runtime_match.end() + next_stage.start()

    return content[runtime_start:runtime_end]


def test_runtime_stage_declares_railway_git_arguments() -> None:
    runtime_stage = read_runtime_stage()

    assert 'ARG RAILWAY_GIT_COMMIT_SHA=""' in runtime_stage
    assert 'ARG RAILWAY_GIT_BRANCH=""' in runtime_stage


def test_runtime_stage_persists_release_identity() -> None:
    runtime_stage = read_runtime_stage()

    assert 'WC26_RELEASE_SHA="${RAILWAY_GIT_COMMIT_SHA}"' in runtime_stage
    assert 'WC26_RELEASE_BRANCH="${RAILWAY_GIT_BRANCH}"' in runtime_stage


def test_release_arguments_precede_release_environment() -> None:
    runtime_stage = read_runtime_stage()

    commit_argument_index = runtime_stage.index("ARG RAILWAY_GIT_COMMIT_SHA")
    branch_argument_index = runtime_stage.index("ARG RAILWAY_GIT_BRANCH")
    release_environment_index = runtime_stage.index("ENV WC26_RELEASE_SHA")

    assert commit_argument_index < release_environment_index
    assert branch_argument_index < release_environment_index
