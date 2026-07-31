# Deployment Guide

This guide describes how to build, validate and run the WC26 Transfer
Intelligence API in production-like environments.

The deployment design separates two independently versioned artifacts:

```text
Application release
└── Docker image identified by an immutable image tag

Dataset release
└── Runtime bundle identified by its manifest bundle SHA-256
```

Application code and runtime datasets can therefore be deployed or rolled back
independently.

## Deployment Architecture

The production runtime flow is:

```text
Docker image
    ↓
Runtime environment validation
    ↓
Dataset manifest validation
    ↓
Dataset size, SHA-256 and CSV schema validation
    ↓
Runtime catalog loading
    ↓
FastAPI readiness
```

The API process is started with:

```bash
python -m wc26.api.server
```

The production launcher validates the runtime environment before starting
Uvicorn. A missing, unreadable, modified or structurally invalid dataset stops
the process before the API begins accepting traffic.

## Runtime Configuration

The API requires four processed datasets:

| Key | Default path |
|---|---|
| `features` | `data/processed/transfer_intelligence/transfer_feature_table.csv` |
| `similarity` | `data/processed/player_similarity/player_similarity_breakdown_long.csv` |
| `heatmap_similarity` | `data/processed/player_heatmaps/heatmap_similarity_long.csv` |
| `heatmap_profiles` | `data/processed/player_heatmaps/player_heatmap_profiles.csv` |

The runtime paths are configured through:

```text
WC26_FEATURES_PATH
WC26_SIMILARITY_PATH
WC26_HEATMAP_SIMILARITY_PATH
WC26_HEATMAP_PROFILES_PATH
```

Production also requires:

```text
WC26_DATASET_MANIFEST_PATH
```

See `.env.example` for the complete runtime configuration.

## Dataset Manifest

The file:

```text
config/runtime_dataset_manifest.json
```

defines the identity and expected metadata of the runtime dataset bundle.

Each dataset entry records:

```text
logical dataset key
repository-relative path
file size
SHA-256 checksum
row count
column count
ordered column names
```

The manifest also contains a bundle SHA-256 calculated from the canonical
metadata of all runtime datasets.

Regenerate the manifest after intentionally changing a runtime dataset:

```bash
python -m wc26.deployment.dataset_manifest
```

Verify that the checked-in manifest matches the current datasets:

```bash
python -m wc26.deployment.dataset_manifest --check
```

A dataset change without a corresponding manifest update is an incomplete
release.

## Runtime Integrity Validation

Validate the manifest and all four configured datasets:

```bash
python -m wc26.deployment.dataset_integrity
```

Equivalent installed console command:

```bash
wc26-validate-datasets
```

Validation covers:

- manifest JSON structure and supported version;
- manifest bundle checksum;
- runtime dataset keys;
- file existence and readability;
- file size and SHA-256 checksum;
- ordered CSV columns;
- column count and row count.

Production startup automatically runs the same integrity checks through:

```bash
python -m wc26.api.environment
```

A failed validation exits with status code `1` and prevents server startup.

## Docker Image

Build the production image:

```bash
docker build \
  --progress=plain \
  -t wc26-transfer-api:dev \
  .
```

The image:

- uses Python 3.12;
- runs as the non-root `wc26` user;
- includes a Docker healthcheck;
- performs build-time runtime validation;
- starts through `python -m wc26.api.server`;
- exposes port `8000`;
- contains no compiler or wheel artifacts in the runtime layer.

Validate image policy:

```bash
./scripts/docker_image_policy.sh
```

Run the embedded-dataset smoke test:

```bash
./scripts/docker_smoke_test.sh
```

Run the hardened runtime test:

```bash
./scripts/docker_hardened_runtime_test.sh
```

The hardened test runs the API with:

```text
read-only root filesystem
writable tmpfs at /tmp
all Linux capabilities dropped
no-new-privileges
PID limit
memory limit
loopback-only published port
```

## Dataset Runtime Modes

The same application image supports three dataset modes.

### Embedded Mode

The default Docker image contains the four runtime CSV files and the manifest
under `/app`.

Run:

```bash
./scripts/docker_smoke_test.sh
```

Embedded mode is suitable when application and dataset releases should be
distributed as one image.

### External Read-Only Mode

Datasets may be mounted from the host or a managed volume.

Run the complete external-mode test:

```bash
./scripts/docker_external_dataset_test.sh
```

The script verifies that:

- the host bundle is valid;
- mounted paths override embedded paths;
- all mounts are read-only;
- write attempts are rejected;
- startup integrity validation succeeds;
- all public API workflows work;
- Docker health becomes healthy.

External mode allows dataset updates without rebuilding the application image.

### Versioned Release Mode

Versioned release mode stores immutable dataset directories under:

```text
dist/runtime-datasets/
```

Example:

```text
dist/runtime-datasets/
├── <bundle-sha256>/
│   ├── config/
│   │   └── runtime_dataset_manifest.json
│   └── data/
│       └── processed/
│           ├── transfer_intelligence/
│           ├── player_similarity/
│           └── player_heatmaps/
├── current -> <active-bundle-sha256>
├── previous -> <previous-bundle-sha256>
├── wc26-runtime-datasets-<bundle-sha256>.tar.gz
└── wc26-runtime-datasets-<bundle-sha256>.tar.gz.sha256
```

Generated files under `dist/` are deployment artifacts and are ignored by Git.

## Build a Versioned Dataset Bundle

Build the current runtime dataset release:

```bash
python -m wc26.deployment.dataset_bundle
```

Equivalent console command:

```bash
wc26-build-dataset-bundle
```

The build process:

1. Loads the checked-in manifest.
2. Validates the source datasets.
3. Copies the manifest and datasets into a staging directory.
4. Validates the staged bundle.
5. Atomically publishes the immutable bundle directory.
6. Creates a deterministic `tar.gz` archive.
7. Writes an archive SHA-256 sidecar file.

The bundle directory name is the manifest bundle SHA-256.

Running the command again with unchanged data is idempotent:

```text
Created=false
```

A conflicting artifact is rejected instead of being overwritten silently.

## Verify the Archive

Find the generated archive:

```bash
archive_path="$(
  find dist/runtime-datasets \
    -maxdepth 1 \
    -type f \
    -name 'wc26-runtime-datasets-*.tar.gz' \
    -print \
    | head -n 1
)"
```

Verify its checksum:

```bash
(
  cd "$(dirname "${archive_path}")"
  shasum -a 256 -c "$(basename "${archive_path}.sha256")"
)
```

Inspect the archive:

```bash
tar -tzf "${archive_path}" | sed -n '1,80p'
```

The archive contains one versioned root directory and does not contain mutable
`current` or `previous` pointers.

## Activate a Dataset Release

Read the current manifest identity:

```bash
bundle_sha256="$(
  python - <<'PY'
import json
from pathlib import Path

manifest = json.loads(
    Path("config/runtime_dataset_manifest.json").read_text(
        encoding="utf-8"
    )
)

print(manifest["bundle_sha256"])
PY
)"
```

Activate the bundle:

```bash
python -m wc26.deployment.dataset_release \
  activate \
  "${bundle_sha256}"
```

Equivalent console command:

```bash
wc26-dataset-release activate "${bundle_sha256}"
```

Activation validates the complete target bundle before changing release
pointers.

The `current` link is replaced atomically:

```text
current -> <new-bundle-sha256>
```

When another bundle was already active:

```text
previous -> <old-current-bundle-sha256>
```

Activating the already active bundle is idempotent and returns:

```text
Changed=false
```

## Inspect Release Status

```bash
python -m wc26.deployment.dataset_release status
```

Example:

```text
CurrentBundleSHA256=<active-bundle-sha256>
PreviousBundleSHA256=<previous-bundle-sha256-or-none>
```

Release pointers must:

- be symbolic links;
- contain a single relative target;
- point to a 64-character bundle SHA-256 directory;
- reference a valid and complete bundle.

Unsafe or unexpected pointer targets are rejected.

## Roll Back a Dataset Release

Roll back to the previous validated bundle:

```bash
python -m wc26.deployment.dataset_release rollback
```

Rollback swaps the release pointers:

```text
before
current  -> bundle-b
previous -> bundle-a

after
current  -> bundle-a
previous -> bundle-b
```

Both bundles are validated before the swap.

Rollback exits with status code `1` when no previous release exists and does
not change the active release.

## Run Docker with the Current Release

Set the host release root:

```bash
release_root="$(pwd)/dist/runtime-datasets"
```

Validate the mounted release inside the image:

```bash
docker run \
  --rm \
  --entrypoint python \
  --env WC26_ENVIRONMENT=production \
  --env WC26_DATASET_MANIFEST_PATH=/runtime/releases/current/config/runtime_dataset_manifest.json \
  --env WC26_FEATURES_PATH=/runtime/releases/current/data/processed/transfer_intelligence/transfer_feature_table.csv \
  --env WC26_SIMILARITY_PATH=/runtime/releases/current/data/processed/player_similarity/player_similarity_breakdown_long.csv \
  --env WC26_HEATMAP_SIMILARITY_PATH=/runtime/releases/current/data/processed/player_heatmaps/heatmap_similarity_long.csv \
  --env WC26_HEATMAP_PROFILES_PATH=/runtime/releases/current/data/processed/player_heatmaps/player_heatmap_profiles.csv \
  --mount \
    "type=bind,source=${release_root},target=/runtime/releases,readonly" \
  wc26-transfer-api:dev \
  -m wc26.api.environment
```

Start the API:

```bash
docker run \
  --detach \
  --rm \
  --name wc26-api \
  --publish 127.0.0.1:8000:8000 \
  --env WC26_ENVIRONMENT=production \
  --env WC26_DATASET_MANIFEST_PATH=/runtime/releases/current/config/runtime_dataset_manifest.json \
  --env WC26_FEATURES_PATH=/runtime/releases/current/data/processed/transfer_intelligence/transfer_feature_table.csv \
  --env WC26_SIMILARITY_PATH=/runtime/releases/current/data/processed/player_similarity/player_similarity_breakdown_long.csv \
  --env WC26_HEATMAP_SIMILARITY_PATH=/runtime/releases/current/data/processed/player_heatmaps/heatmap_similarity_long.csv \
  --env WC26_HEATMAP_PROFILES_PATH=/runtime/releases/current/data/processed/player_heatmaps/player_heatmap_profiles.csv \
  --mount \
    "type=bind,source=${release_root},target=/runtime/releases,readonly" \
  wc26-transfer-api:dev
```

Check readiness:

```bash
curl --fail http://127.0.0.1:8000/ready
```

Check Docker health:

```bash
docker inspect wc26-api --format '{{.State.Health.Status}}'
```

## Safe Dataset Update Procedure

Use this sequence for every intentional runtime dataset update:

```text
1. Generate or replace the four processed CSV files.
2. Regenerate the runtime dataset manifest.
3. Check that the manifest is not stale.
4. Run full runtime integrity validation.
5. Build the immutable versioned bundle and archive.
6. Verify the archive checksum.
7. Activate the new bundle SHA-256.
8. Start or restart the container with the current release.
9. Wait for GET /ready to return 200.
10. Run API smoke tests.
11. Keep the previous bundle available for rollback.
```

Commands:

```bash
python -m wc26.deployment.dataset_manifest
python -m wc26.deployment.dataset_manifest --check
python -m wc26.deployment.dataset_integrity
python -m wc26.deployment.dataset_bundle
python -m wc26.deployment.dataset_release activate "<bundle-sha256>"
```

Do not modify files inside an existing versioned bundle. Bundle directories are
immutable release artifacts.

## Failure and Recovery Rules

### Manifest check fails

The processed datasets changed without regenerating the manifest.

```bash
python -m wc26.deployment.dataset_manifest
python -m wc26.deployment.dataset_manifest --check
```

### Integrity validation fails

At least one configured file differs from the release manifest.

Common causes:

```text
wrong mounted path
partial file transfer
manual modification
stale manifest
corrupt archive extraction
wrong bundle selected
```

Do not start the API until validation succeeds.

### Container does not become ready

Inspect logs:

```bash
docker logs wc26-api
```

Validate the mounted release independently:

```bash
docker exec \
  wc26-api \
  python -m wc26.deployment.dataset_integrity
```

### Newly activated dataset is invalid in production

Roll back:

```bash
python -m wc26.deployment.dataset_release rollback
```

Restart the container so the runtime catalog loads the restored `current`
release.

The API loads datasets once during process startup. Changing `current` does not
replace the already loaded in-memory catalog of a running process.

## Pre-Deployment Checklist

```bash
python -m ruff check \
  src/wc26 \
  tests

python -m ruff format \
  --check \
  src/wc26 \
  tests

python -m mypy src/wc26

python -m pytest \
  -m "not integration"

python -m wc26.deployment.dataset_manifest \
  --check

python -m wc26.deployment.dataset_integrity

docker build \
  -t wc26-transfer-api:dev \
  .

./scripts/docker_image_policy.sh
./scripts/docker_smoke_test.sh
./scripts/docker_hardened_runtime_test.sh
./scripts/docker_external_dataset_test.sh
```

A release is ready only when the image, runtime datasets, container health and
public API workflows all pass validation.
