"""Tests for API runtime environment validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from wc26.api.environment import (
    RuntimeEnvironmentError,
    main,
    validate_runtime_environment,
)
from wc26.api.settings import ApiSettings, TransferDatasetPaths
from wc26.deployment.dataset_manifest import (
    DatasetDefinition,
    generate_manifest,
    render_manifest,
)


def _create_dataset_paths(tmp_path: Path) -> TransferDatasetPaths:
    features = tmp_path / "features.csv"
    similarity = tmp_path / "similarity.csv"
    heatmap_similarity = tmp_path / "heatmap-similarity.csv"
    heatmap_profiles = tmp_path / "heatmap-profiles.csv"

    for path in (
        features,
        similarity,
        heatmap_similarity,
        heatmap_profiles,
    ):
        path.write_text("column\nvalue\n", encoding="utf-8")

    return TransferDatasetPaths(
        features=features,
        similarity=similarity,
        heatmap_similarity=heatmap_similarity,
        heatmap_profiles=heatmap_profiles,
    )


def test_validate_runtime_environment_accepts_readable_dataset_files(
    tmp_path: Path,
) -> None:
    settings = ApiSettings(
        dataset_paths=_create_dataset_paths(tmp_path),
    )

    validated_settings = validate_runtime_environment(settings)

    assert validated_settings is settings


def test_validate_runtime_environment_reports_all_missing_files(
    tmp_path: Path,
) -> None:
    settings = ApiSettings(
        dataset_paths=TransferDatasetPaths(
            features=tmp_path / "missing-features.csv",
            similarity=tmp_path / "missing-similarity.csv",
            heatmap_similarity=tmp_path / "missing-heatmap-similarity.csv",
            heatmap_profiles=tmp_path / "missing-heatmap-profiles.csv",
        ),
    )

    with pytest.raises(RuntimeEnvironmentError) as error:
        validate_runtime_environment(settings)

    message = str(error.value)

    assert "WC26_FEATURES_PATH" in message
    assert "WC26_SIMILARITY_PATH" in message
    assert "WC26_HEATMAP_SIMILARITY_PATH" in message
    assert "WC26_HEATMAP_PROFILES_PATH" in message


def test_validate_runtime_environment_rejects_directory_paths(
    tmp_path: Path,
) -> None:
    dataset_paths = _create_dataset_paths(tmp_path)
    invalid_features_path = tmp_path / "features-directory"
    invalid_features_path.mkdir()

    settings = ApiSettings(
        dataset_paths=TransferDatasetPaths(
            features=invalid_features_path,
            similarity=dataset_paths.similarity,
            heatmap_similarity=dataset_paths.heatmap_similarity,
            heatmap_profiles=dataset_paths.heatmap_profiles,
        ),
    )

    with pytest.raises(
        RuntimeEnvironmentError,
        match="path must be a file",
    ):
        validate_runtime_environment(settings)


def test_main_reports_valid_runtime_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dataset_paths = _create_dataset_paths(tmp_path)

    monkeypatch.setenv(
        "WC26_FEATURES_PATH",
        str(dataset_paths.features),
    )
    monkeypatch.setenv(
        "WC26_SIMILARITY_PATH",
        str(dataset_paths.similarity),
    )
    monkeypatch.setenv(
        "WC26_HEATMAP_SIMILARITY_PATH",
        str(dataset_paths.heatmap_similarity),
    )
    monkeypatch.setenv(
        "WC26_HEATMAP_PROFILES_PATH",
        str(dataset_paths.heatmap_profiles),
    )

    main()

    output = capsys.readouterr().out

    assert "WC26 API runtime environment is valid." in output
    assert "WC26_FEATURES_PATH=" in output
    assert "WC26_HEATMAP_PROFILES_PATH=" in output


def _create_runtime_manifest(
    tmp_path: Path,
    dataset_paths: TransferDatasetPaths,
) -> Path:
    definitions = (
        DatasetDefinition(
            key="features",
            relative_path=(dataset_paths.features.relative_to(tmp_path)),
        ),
        DatasetDefinition(
            key="similarity",
            relative_path=(dataset_paths.similarity.relative_to(tmp_path)),
        ),
        DatasetDefinition(
            key="heatmap_similarity",
            relative_path=(dataset_paths.heatmap_similarity.relative_to(tmp_path)),
        ),
        DatasetDefinition(
            key="heatmap_profiles",
            relative_path=(dataset_paths.heatmap_profiles.relative_to(tmp_path)),
        ),
    )

    manifest = generate_manifest(
        repository_root=tmp_path,
        definitions=definitions,
    )

    manifest_path = tmp_path / "config" / "runtime_dataset_manifest.json"
    manifest_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    manifest_path.write_text(
        render_manifest(manifest),
        encoding="utf-8",
    )

    return manifest_path


def test_production_environment_validates_dataset_integrity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dataset_paths = _create_dataset_paths(tmp_path)
    manifest_path = _create_runtime_manifest(
        tmp_path,
        dataset_paths,
    )

    monkeypatch.setenv(
        "WC26_DATASET_MANIFEST_PATH",
        str(manifest_path),
    )

    settings = ApiSettings(
        environment="production",
        dataset_paths=dataset_paths,
    )

    validated_settings = validate_runtime_environment(settings)

    assert validated_settings is settings


def test_production_environment_rejects_tampered_dataset(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dataset_paths = _create_dataset_paths(tmp_path)
    manifest_path = _create_runtime_manifest(
        tmp_path,
        dataset_paths,
    )

    with dataset_paths.features.open(
        "a",
        encoding="utf-8",
    ) as file:
        file.write("tampered\n")

    monkeypatch.setenv(
        "WC26_DATASET_MANIFEST_PATH",
        str(manifest_path),
    )

    settings = ApiSettings(
        environment="production",
        dataset_paths=dataset_paths,
    )

    with pytest.raises(
        RuntimeEnvironmentError,
        match="dataset integrity validation failed",
    ):
        validate_runtime_environment(settings)


def test_production_environment_requires_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dataset_paths = _create_dataset_paths(tmp_path)

    monkeypatch.setenv(
        "WC26_DATASET_MANIFEST_PATH",
        str(tmp_path / "missing-manifest.json"),
    )

    settings = ApiSettings(
        environment="production",
        dataset_paths=dataset_paths,
    )

    with pytest.raises(
        RuntimeEnvironmentError,
        match="WC26_DATASET_MANIFEST_PATH",
    ):
        validate_runtime_environment(settings)
