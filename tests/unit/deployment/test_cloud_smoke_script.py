"""Tests for the production cloud smoke-test script."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from http.server import (
    BaseHTTPRequestHandler,
    ThreadingHTTPServer,
)
from pathlib import Path
from typing import Any

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = REPOSITORY_ROOT / "scripts" / "cloud_smoke_test.sh"

pytestmark = pytest.mark.skipif(
    shutil.which("bash") is None or shutil.which("curl") is None,
    reason="bash and curl are required",
)


def build_handler(
    *,
    environment: str,
) -> type[BaseHTTPRequestHandler]:
    """Build a deterministic cloud API stub handler."""

    class Handler(BaseHTTPRequestHandler):
        def log_message(
            self,
            format: str,
            *args: object,
        ) -> None:
            del format, args

        def send_json(
            self,
            document: dict[str, Any],
            *,
            status: int = 200,
        ) -> None:
            payload = json.dumps(document).encode("utf-8")

            self.send_response(status)
            self.send_header(
                "Content-Type",
                "application/json",
            )
            self.send_header(
                "Content-Length",
                str(len(payload)),
            )
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self) -> None:
            if self.path == "/health":
                self.send_json(
                    {
                        "status": "ok",
                        "service": ("wc26-transfer-intelligence"),
                        "version": "0.1.0",
                        "environment": environment,
                        "started_at": ("2026-07-31T12:00:00Z"),
                        "uptime_seconds": 10.0,
                    }
                )
                return

            if self.path == "/ready":
                self.send_json(
                    {
                        "status": "ready",
                        "service": ("wc26-transfer-intelligence"),
                        "version": "0.1.0",
                        "environment": environment,
                        "started_at": ("2026-07-31T12:00:00Z"),
                        "uptime_seconds": 10.0,
                        "catalog_loaded_at": ("2026-07-31T12:00:01Z"),
                    }
                )
                return

            if self.path.startswith("/api/v1/players/search?"):
                self.send_json(
                    {
                        "query": "olise",
                        "count": 1,
                        "players": [
                            {
                                "player_id": 978838,
                                "player_name": ("Michael Olise"),
                            }
                        ],
                    }
                )
                return

            if self.path == ("/api/v1/players/978838"):
                self.send_json(
                    {
                        "player_id": 978838,
                        "player_name": ("Michael Olise"),
                    }
                )
                return

            if self.path == "/deployment":
                self.send_json(
                    {
                        "service": ("wc26-transfer-intelligence"),
                        "version": "0.1.0",
                        "environment": environment,
                        "provider": "railway",
                        "commit_sha": "a" * 40,
                        "branch": ("feat/docker-deployment-foundation"),
                        "deployment_id": ("deployment-123"),
                        "dataset_bundle_sha256": ("b" * 64),
                    }
                )
                return

            if self.path == "/openapi.json":
                self.send_json(
                    {
                        "openapi": "3.1.0",
                        "paths": {
                            "/health": {},
                            "/ready": {},
                            "/deployment": {},
                            ("/api/v1/players/search"): {},
                            ("/api/v1/players/{player_id}"): {},
                            ("/api/v1/transfer-intelligence/analyze"): {},
                        },
                    }
                )
                return

            if self.path == "/docs":
                payload = b"<html><title>Swagger UI</title></html>"

                self.send_response(200)
                self.send_header(
                    "Content-Type",
                    "text/html",
                )
                self.send_header(
                    "Content-Length",
                    str(len(payload)),
                )
                self.end_headers()
                self.wfile.write(payload)
                return

            self.send_json(
                {
                    "detail": "Not Found",
                },
                status=404,
            )

        def do_POST(self) -> None:
            if self.path != ("/api/v1/transfer-intelligence/analyze"):
                self.send_json(
                    {
                        "detail": "Not Found",
                    },
                    status=404,
                )
                return

            content_length = int(
                self.headers.get(
                    "Content-Length",
                    "0",
                )
            )
            request_body = json.loads(self.rfile.read(content_length))

            if request_body != {
                "player_id": 978838,
            }:
                self.send_json(
                    {
                        "detail": "Invalid request",
                    },
                    status=422,
                )
                return

            self.send_json(
                {
                    "target": {
                        "player_id": 978838,
                        "player_name": ("Michael Olise"),
                    },
                    "modes": {
                        "similar": [],
                        "value": [],
                    },
                }
            )

    return Handler


@contextmanager
def run_stub_server(
    *,
    environment: str,
) -> Iterator[str]:
    """Run a local cloud API stub."""

    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        build_handler(
            environment=environment,
        ),
    )
    thread = threading.Thread(
        target=server.serve_forever,
        daemon=True,
    )
    thread.start()

    host, port = server.server_address

    try:
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def run_smoke_script(
    base_url: str,
    *,
    expected_commit_sha: str = "a" * 40,
) -> subprocess.CompletedProcess[str]:
    """Execute the smoke script against one URL."""

    environment = os.environ.copy()
    environment.update(
        {
            "WC26_EXPECTED_COMMIT_SHA": (expected_commit_sha),
            "WC26_CLOUD_SMOKE_ALLOW_HTTP": "1",
            ("WC26_CLOUD_READY_TIMEOUT_SECONDS"): "5",
            ("WC26_CLOUD_READY_INTERVAL_SECONDS"): "1",
            ("WC26_CLOUD_REQUEST_TIMEOUT_SECONDS"): "5",
        }
    )

    return subprocess.run(
        [
            "bash",
            str(SCRIPT_PATH),
            base_url,
        ],
        cwd=REPOSITORY_ROOT,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )


def test_cloud_smoke_script_accepts_valid_production_api() -> None:
    with run_stub_server(
        environment="production",
    ) as base_url:
        result = run_smoke_script(base_url)

    assert result.returncode == 0
    assert "Production API contracts validated." in result.stdout
    assert "Cloud smoke test passed." in result.stdout


def test_cloud_smoke_script_rejects_non_production_api() -> None:
    with run_stub_server(
        environment="development",
    ) as base_url:
        result = run_smoke_script(base_url)

    assert result.returncode != 0
    assert "environment is not production" in result.stderr


def test_cloud_smoke_script_rejects_unexpected_commit() -> None:
    with run_stub_server(
        environment="production",
    ) as base_url:
        result = run_smoke_script(
            base_url,
            expected_commit_sha="c" * 40,
        )

    assert result.returncode != 0
    assert "deployment commit SHA does not match WC26_EXPECTED_COMMIT_SHA" in result.stderr
