from pathlib import Path

import pytest

from wc26.core.paths import (
    ProjectPaths,
    ProjectRootNotFoundError,
    find_project_root,
)


def test_find_project_root_from_nested_directory(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname = 'example'\nversion = '0.1.0'\n",
        encoding="utf-8",
    )

    nested_directory = tmp_path / "a" / "b" / "c"
    nested_directory.mkdir(parents=True)

    assert find_project_root(nested_directory) == tmp_path



def test_project_paths_are_derived_from_root(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname = 'example'\nversion = '0.1.0'\n",
        encoding="utf-8",
    )

    paths = ProjectPaths.discover(tmp_path)

    assert paths.root == tmp_path
    assert paths.data == tmp_path / "data"
    assert paths.processed_data == tmp_path / "data" / "processed"
    assert paths.artifacts == tmp_path / "artifacts"


def test_missing_project_root_raises_error(tmp_path: Path) -> None:
    with pytest.raises(ProjectRootNotFoundError):
        find_project_root(tmp_path)
