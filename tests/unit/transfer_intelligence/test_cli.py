from __future__ import annotations

import sys
from pathlib import Path

import pytest

from wc26.analytics.transfer_intelligence.cli import (
    parse_args,
)
from wc26.analytics.transfer_intelligence.config import (
    DEFAULT_FEATURES,
    DEFAULT_HEATMAP_PROFILES,
    DEFAULT_HEATMAP_SIMILARITY,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_SIMILARITY,
)


def test_parse_args_accepts_required_player(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "find_replacements.py",
            "--player",
            "Michael Olise",
        ],
    )

    args = parse_args()

    assert args.player == "Michael Olise"


def test_parse_args_uses_default_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "find_replacements.py",
            "--player",
            "Michael Olise",
        ],
    )

    args = parse_args()

    assert Path(args.features) == DEFAULT_FEATURES
    assert Path(args.similarity) == DEFAULT_SIMILARITY
    assert Path(args.heatmap_similarity) == DEFAULT_HEATMAP_SIMILARITY
    assert Path(args.heatmap_profiles) == DEFAULT_HEATMAP_PROFILES
    assert Path(args.output_dir) == DEFAULT_OUTPUT_DIR


def test_parse_args_requires_player(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["find_replacements.py"],
    )

    with pytest.raises(SystemExit) as error:
        parse_args()

    assert error.value.code == 2


def test_parse_args_displays_help(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "find_replacements.py",
            "--help",
        ],
    )

    with pytest.raises(SystemExit) as error:
        parse_args()

    captured = capsys.readouterr()

    assert error.value.code == 0
    assert "--player" in captured.out
    assert "--minimum-minutes" in captured.out
    assert "--neutral-heatmap-score" in captured.out
    assert "--top-n" in captured.out
