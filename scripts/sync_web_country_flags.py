"""Sync World Cup country flags into the Next.js public directory."""

from __future__ import annotations

import csv
import shutil
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

SUMMARY_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "player_matches_analysis"
    / "player_tournament_full_summary_enriched.csv"
)

SOURCE_FLAGS_DIR = (
    PROJECT_ROOT
    / "data"
    / "assets"
    / "country_flags"
    / "4x3"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "web"
    / "public"
    / "country-flags"
)


# Stable tournament country identity → local flag asset code.
#
# Most values are ISO alpha-2 codes. England and Scotland use the
# subdivision flag filenames already present in the local asset set.
FLAG_CODE_BY_ALPHA3: dict[str, str] = {
    "ARG": "ar",
    "AUS": "au",
    "AUT": "at",
    "BEL": "be",
    "BIH": "ba",
    "BRA": "br",
    "CAN": "ca",
    "CHE": "ch",
    "CIV": "ci",
    "COD": "cd",
    "COL": "co",
    "CPV": "cv",
    "CUW": "cw",
    "CZE": "cz",
    "DEU": "de",
    "DZA": "dz",
    "ECU": "ec",
    "EGY": "eg",
    "ENG": "gb-eng",
    "ESP": "es",
    "FRA": "fr",
    "GHA": "gh",
    "HRV": "hr",
    "HTI": "ht",
    "IRN": "ir",
    "IRQ": "iq",
    "JOR": "jo",
    "JPN": "jp",
    "KOR": "kr",
    "MAR": "ma",
    "MEX": "mx",
    "NLD": "nl",
    "NOR": "no",
    "NZL": "nz",
    "PAN": "pa",
    "PRT": "pt",
    "PRY": "py",
    "QAT": "qa",
    "SAU": "sa",
    "SCO": "gb-sct",
    "SEN": "sn",
    "SWE": "se",
    "TUN": "tn",
    "TUR": "tr",
    "URY": "uy",
    "USA": "us",
    "UZB": "uz",
    "ZAF": "za",
}


def normalize_alpha3(value: str) -> str:
    code = value.strip().upper()

    if (
        len(code) != 3
        or not code.isascii()
        or not code.isalpha()
    ):
        raise ValueError(
            f"Invalid country_alpha3 value: {value!r}"
        )

    return code


def load_tournament_country_codes() -> set[str]:
    with SUMMARY_PATH.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        reader = csv.DictReader(handle)

        if "country_alpha3" not in (reader.fieldnames or []):
            raise RuntimeError(
                "Tournament summary is missing country_alpha3."
            )

        codes: set[str] = set()

        for row in reader:
            raw_code = row.get("country_alpha3", "")

            if not raw_code:
                raise RuntimeError(
                    "Tournament summary contains missing country_alpha3."
                )

            codes.add(
                normalize_alpha3(raw_code)
            )

    return codes


def validate_manifest(
    tournament_codes: set[str],
) -> None:
    missing_mappings = (
        tournament_codes
        - FLAG_CODE_BY_ALPHA3.keys()
    )

    if missing_mappings:
        raise RuntimeError(
            "Missing flag-code mappings for: "
            + ", ".join(
                sorted(missing_mappings)
            )
        )

    unused_mappings = (
        FLAG_CODE_BY_ALPHA3.keys()
        - tournament_codes
    )

    if unused_mappings:
        raise RuntimeError(
            "Flag-code manifest contains countries "
            "outside the tournament dataset: "
            + ", ".join(
                sorted(unused_mappings)
            )
        )


def main() -> None:
    tournament_codes = (
        load_tournament_country_codes()
    )

    validate_manifest(
        tournament_codes
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    expected_files: set[str] = set()

    for alpha3 in sorted(tournament_codes):
        asset_code = (
            FLAG_CODE_BY_ALPHA3[alpha3]
        )

        source = (
            SOURCE_FLAGS_DIR
            / f"{asset_code}.svg"
        )

        if not source.exists():
            raise RuntimeError(
                "Missing local flag asset for "
                f"{alpha3}: {source}"
            )

        destination_name = (
            f"{alpha3.lower()}.svg"
        )

        shutil.copyfile(
            source,
            OUTPUT_DIR / destination_name,
        )

        expected_files.add(
            destination_name
        )

    for existing in OUTPUT_DIR.glob(
        "*.svg"
    ):
        if existing.name not in expected_files:
            existing.unlink()

    print(
        f"Synced {len(tournament_codes)} country flags "
        f"to {OUTPUT_DIR.relative_to(PROJECT_ROOT)}"
    )


if __name__ == "__main__":
    main()
