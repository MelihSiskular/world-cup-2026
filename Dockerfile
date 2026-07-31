# syntax=docker/dockerfile:1.7

FROM python:3.12-slim-bookworm AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

COPY pyproject.toml README.md ./
COPY src ./src

RUN python -m pip wheel \
    --wheel-dir /wheels \
    .


FROM python:3.12-slim-bookworm AS installer

ENV VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

RUN python -m venv "$VIRTUAL_ENV"

COPY --from=builder /wheels /wheels

RUN python -m pip install \
        --no-cache-dir \
        --no-index \
        --find-links=/wheels \
        wc26-transfer-intelligence \
    && rm -rf /wheels


FROM python:3.12-slim-bookworm AS runtime

ARG RAILWAY_GIT_COMMIT_SHA=""
ARG RAILWAY_GIT_BRANCH=""

ENV WC26_RELEASE_SHA="${RAILWAY_GIT_COMMIT_SHA}" \
    WC26_RELEASE_BRANCH="${RAILWAY_GIT_BRANCH}"


ENV VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

COPY --from=installer /opt/venv /opt/venv


ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    WC26_ENVIRONMENT=production \
    WC26_API_HOST=0.0.0.0 \
    WC26_DATASET_MANIFEST_PATH=/app/config/runtime_dataset_manifest.json \
    WC26_FEATURES_PATH=/app/data/processed/transfer_intelligence/transfer_feature_table.csv \
    WC26_SIMILARITY_PATH=/app/data/processed/player_similarity/player_similarity_breakdown_long.csv \
    WC26_HEATMAP_SIMILARITY_PATH=/app/data/processed/player_heatmaps/heatmap_similarity_long.csv \
    WC26_HEATMAP_PROFILES_PATH=/app/data/processed/player_heatmaps/player_heatmap_profiles.csv

WORKDIR /app

RUN groupadd \
        --system \
        --gid 10001 \
        wc26 \
    && useradd \
        --system \
        --uid 10001 \
        --gid wc26 \
        --home-dir /app \
        --shell /usr/sbin/nologin \
        wc26


COPY --chown=wc26:wc26 \
    config/runtime_dataset_manifest.json \
    /app/config/runtime_dataset_manifest.json

COPY --chown=wc26:wc26 \
    data/processed/transfer_intelligence/transfer_feature_table.csv \
    /app/data/processed/transfer_intelligence/transfer_feature_table.csv

COPY --chown=wc26:wc26 \
    data/processed/player_similarity/player_similarity_breakdown_long.csv \
    /app/data/processed/player_similarity/player_similarity_breakdown_long.csv

COPY --chown=wc26:wc26 \
    data/processed/player_heatmaps/heatmap_similarity_long.csv \
    data/processed/player_heatmaps/player_heatmap_profiles.csv \
    /app/data/processed/player_heatmaps/

USER wc26

RUN python -m wc26.api.environment

EXPOSE 8000

HEALTHCHECK \
    --interval=30s \
    --timeout=5s \
    --start-period=60s \
    --retries=3 \
    CMD python -c "import os, urllib.request; port = os.environ.get('WC26_API_PORT') or os.environ.get('PORT', '8000'); urllib.request.urlopen(f'http://127.0.0.1:{port}/ready', timeout=5).read()"

CMD ["python", "-m", "wc26.api.server"]
