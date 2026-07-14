# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import re
import unicodedata
from pathlib import Path

import pandas as pd


DEFAULT_CSV = Path(
    "/Users/melihsiskular/PycharmProjects/wc2026/data/processed/player_similarity/"
    "player_similarity_breakdown_long.csv"
)

DEFAULT_RESULTS_DIR = Path(
    "/Users/melihsiskular/PycharmProjects/wc2026/data/processed/player_similarity/results"
)


def slugify(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode(
        "ascii",
        "ignore",
    ).decode("ascii")

    return (
        re.sub(r"[^a-zA-Z0-9]+", "_", ascii_text)
        .strip("_")
        .lower()
    )


def load_breakdown(
    csv_path: Path,
) -> pd.DataFrame:
    if csv_path.exists():
        return pd.read_csv(
            csv_path,
            low_memory=False,
        )

    raise FileNotFoundError(
        "Similarity breakdown dosyasÄ± bulunamadÄ±."
    )


def resolve_player_name(
    dataframe: pd.DataFrame,
    query: str,
) -> str:
    names = (
        dataframe["source_player_name"]
        .dropna()
        .drop_duplicates()
    )

    exact = names[
        names.str.casefold().eq(query.casefold())
    ]

    if len(exact) == 1:
        return str(exact.iloc[0])

    partial = names[
        names.str.contains(
            query,
            case=False,
            regex=False,
        )
    ]

    if len(partial) == 1:
        return str(partial.iloc[0])

    if partial.empty:
        raise ValueError(f"Oyuncu bulunamadÄ±: {query}")

    raise ValueError(
        "Birden fazla eÅleÅme: "
        + ", ".join(partial.head(10).tolist())
    )


def available_similarity_columns(
    dataframe: pd.DataFrame,
) -> list[str]:
    return [
        column
        for column in dataframe.columns
        if column.endswith("_similarity_pct")
    ]


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--player", required=True)
    parser.add_argument("--top-n", type=int, default=10)

    parser.add_argument(
        "--minimum-similarity",
        type=float,
        default=20.0,
        help="YÃ¼zde cinsinden alt overall similarity sÄ±nÄ±rÄ±.",
    )

    parser.add_argument(
        "--csv",
        type=Path,
        default=DEFAULT_CSV,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=None,
    )

    return parser.parse_args()


def main():
    args = parse_args()

    dataframe = load_breakdown(
        args.csv,
    )

    player_name = resolve_player_name(
        dataframe,
        args.player,
    )

    results = (
        dataframe[
            dataframe["source_player_name"].eq(player_name)
            & dataframe["overall_similarity_pct"].ge(
                args.minimum_similarity
            )
        ]
        .sort_values(
            [
                "overall_similarity",
                "target_minutes",
            ],
            ascending=[False, False],
        )
        .head(args.top_n)
        .copy()
    )

    if args.output is None:
        output_path = (
            DEFAULT_RESULTS_DIR
            / f"{slugify(player_name)}_similarity_breakdown.csv"
        )
    else:
        output_path = args.output

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    results.to_csv(
        output_path,
        index=False,
        encoding="utf-8-sig",
    )

    similarity_columns = available_similarity_columns(
        results
    )

    display_columns = [
        "target_player_name",
        "target_team",
        "target_minutes",
        "target_rating",
        *similarity_columns,
    ]

    display_columns = [
        column
        for column in display_columns
        if column in results.columns
    ]

    print(f"\nHedef oyuncu: {player_name}")
    print("\nBenzerlik kÄ±rÄ±lÄ±mÄ±:")

    if results.empty:
        print("SonuÃ§ bulunamadÄ±.")
    else:
        print(
            results[display_columns]
            .to_string(index=False)
        )

    print(f"\nÃÄ±ktÄ±: {output_path}")


if __name__ == "__main__":
    main()
