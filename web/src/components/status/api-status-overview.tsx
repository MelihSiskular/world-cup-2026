"use client";

import {
  useEffect,
  useState,
} from "react";

import {
  fetchApiHealth,
  fetchApiReadiness,
  fetchDeploymentIdentity,
} from "@/lib/api/browser-status";
import type {
  DeploymentIdentityResponse,
  HealthResponse,
  ReadinessResponse,
} from "@/lib/api/types";

type StatusSnapshot =
  Readonly<{
    health: HealthResponse;
    readiness: ReadinessResponse;
    deployment: DeploymentIdentityResponse;
  }>;

type OverviewState =
  | Readonly<{
      status: "loading";
    }>
  | Readonly<{
      status: "success";
      data: StatusSnapshot;
    }>
  | Readonly<{
      status: "error";
      message: string;
    }>;

async function fetchStatusSnapshot(
  signal?: AbortSignal,
): Promise<StatusSnapshot> {
  const [
    health,
    readiness,
    deployment,
  ] = await Promise.all([
    fetchApiHealth(signal),
    fetchApiReadiness(signal),
    fetchDeploymentIdentity(signal),
  ]);

  return {
    health,
    readiness,
    deployment,
  };
}

function isAbortError(
  error: unknown,
): boolean {
  return (
    error instanceof DOMException &&
    error.name === "AbortError"
  );
}

function getStatusErrorMessage(
  error: unknown,
): string {
  return error instanceof Error
    ? error.message
    : "The API status could not be loaded.";
}

function formatTimestamp(
  value: string | null,
): string {
  if (!value) {
    return "Not reported";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat(
    "en",
    {
      dateStyle: "medium",
      timeStyle: "short",
    },
  ).format(date);
}

function StatusCard({
  label,
  value,
  description,
}: Readonly<{
  label: string;
  value: string;
  description: string;
}>) {
  return (
    <article className="rounded-2xl border border-border bg-surface p-6 shadow-sm">
      <p className="text-sm font-semibold text-muted">
        {label}
      </p>

      <p className="mt-3 text-xl font-bold tracking-[-0.025em]">
        {value}
      </p>

      <p className="mt-2 text-sm leading-6 text-muted">
        {description}
      </p>
    </article>
  );
}

export function ApiStatusOverview() {
  const [
    state,
    setState,
  ] = useState<OverviewState>({
    status: "loading",
  });

  useEffect(() => {
    const controller =
      new AbortController();

    void fetchStatusSnapshot(
      controller.signal,
    ).then(
      (data) => {
        setState({
          status: "success",
          data,
        });
      },
      (error: unknown) => {
        if (isAbortError(error)) {
          return;
        }

        setState({
          status: "error",
          message:
            getStatusErrorMessage(error),
        });
      },
    );

    return () => {
      controller.abort();
    };
  }, []);

  async function refreshStatus(): Promise<void> {
    setState({
      status: "loading",
    });

    try {
      const data =
        await fetchStatusSnapshot();

      setState({
        status: "success",
        data,
      });
    } catch (error) {
      setState({
        status: "error",
        message:
          getStatusErrorMessage(error),
      });
    }
  }

  if (state.status === "loading") {
    return (
      <div
        className="rounded-2xl border border-border bg-surface p-8 text-sm text-muted shadow-sm"
        role="status"
        aria-live="polite"
      >
        Checking the analytics API…
      </div>
    );
  }

  if (state.status === "error") {
    return (
      <div
        className="rounded-2xl border border-error/25 bg-error/10 p-6"
        role="alert"
      >
        <p className="font-semibold text-error">
          API status unavailable
        </p>

        <p className="mt-2 text-sm leading-6 text-muted">
          {state.message}
        </p>

        <button
          type="button"
          className="mt-5 rounded-lg border border-error/30 bg-surface px-4 py-2 text-sm font-semibold text-error"
          onClick={() => {
            void refreshStatus();
          }}
        >
          Retry
        </button>
      </div>
    );
  }

  const {
    health,
    readiness,
    deployment,
  } = state.data;

  return (
    <div>
      <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
        <StatusCard
          label="API health"
          value={
            health.status === "ok"
              ? "Operational"
              : health.status
          }
          description={`Environment: ${health.environment}`}
        />

        <StatusCard
          label="Player catalogue"
          value={
            readiness.status === "ready"
              ? "Ready"
              : "Not ready"
          }
          description={`Loaded: ${formatTimestamp(
            readiness.catalog_loaded_at,
          )}`}
        />

        <StatusCard
          label="Deployment"
          value={deployment.provider}
          description={`Version ${deployment.version} · ${
            deployment.branch ??
            "unknown branch"
          }`}
        />

        <StatusCard
          label="Dataset bundle"
          value={
            deployment.dataset_bundle_sha256
              ? deployment.dataset_bundle_sha256.slice(
                  0,
                  12,
                )
              : "Not reported"
          }
          description="Deterministic analytics dataset fingerprint"
        />
      </div>

      <div className="mt-6 flex flex-wrap items-center justify-between gap-4 rounded-xl border border-border bg-surface-secondary px-5 py-4 text-sm text-muted">
        <span>
          API started{" "}
          {formatTimestamp(
            health.started_at,
          )}
        </span>

        <button
          type="button"
          className="rounded-lg border border-border bg-surface px-4 py-2 font-semibold text-foreground transition-colors hover:bg-page"
          onClick={() => {
            void refreshStatus();
          }}
        >
          Refresh status
        </button>
      </div>
    </div>
  );
}
