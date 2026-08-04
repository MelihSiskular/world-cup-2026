"""Export the local FastAPI OpenAPI contract for the web application."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "src"
OUTPUT_PATH = PROJECT_ROOT / "web" / "openapi" / "wc26.openapi.json"

if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from wc26.api import create_app  # noqa: E402


def main() -> None:
    """Write the current local FastAPI OpenAPI document."""

    schema = create_app().openapi()

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    OUTPUT_PATH.write_text(
        f"{json.dumps(schema, indent=2)}\n",
        encoding="utf-8",
    )

    paths = schema.get("paths", {})
    component_schemas = schema.get("components", {}).get("schemas", {})

    print(f"Exported OpenAPI schema to {OUTPUT_PATH}")
    print(f"Paths: {len(paths)}")
    print(f"Component schemas: {len(component_schemas)}")


if __name__ == "__main__":
    main()
