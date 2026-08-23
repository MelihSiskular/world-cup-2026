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

type StatusSnapshot = Readonly<{
  health: HealthResponse;
  readiness: ReadinessResponse;
  deployment: DeploymentIdentityResponse;
  checkedAt: string;
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
    checkedAt: new Date().toISOString(),
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
    : "The system status could not be loaded.";
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
    <article className="rounded-2xl border border-border bg-surface p-5 shadow-sm sm:p-6">
      <p className="text-sm font-semibold text-muted">
        {label}
      </p>

      <p className="mt-2 text-xl font-bold tracking-[-0.025em]">
        {value}
      </p>

      <p className="mt-2 text-sm leading-6 text-muted">
        {description}
      </p>
    </article>
  );
}

function TechnicalDetail({
  label,
  value,
}: Readonly<{
  label: string;
  value: string;
}>) {
  return (
    <div className="min-w-0 rounded-xl border border-border bg-page p-4">
      <dt className="text-xs font-semibold text-muted">
        {label}
      </dt>

      <dd className="mt-2 min-w-0 break-words text-sm font-semibold">
        {value}
      </dd>
    </div>
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
        Checking system availability…
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
          System status unavailable
        </p>

        <p className="mt-2 text-sm leading-6 text-muted">
          {state.message}
        </p>

        <button
          type="button"
          className="mt-5 min-h-11 rounded-lg border border-error/30 bg-surface px-4 py-2 text-sm font-semibold text-error"
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
    checkedAt,
  } = state.data;

  const allServicesReady =
    health.status === "ok" &&
    readiness.status === "ready";

  return (
    <div className="space-y-5">
      <section
        aria-labelledby="overall-system-status-title"
        className={[
          "rounded-2xl border p-5 shadow-sm sm:p-6",
          allServicesReady
            ? "border-success/25 bg-success/10"
            : "border-warning/25 bg-warning/10",
        ].join(" ")}
      >
        <div className="flex items-start gap-3">
          <span
            aria-hidden="true"
            className={[
              "mt-1.5 size-2.5 shrink-0 rounded-full",
              allServicesReady
                ? "bg-success"
                : "bg-warning",
            ].join(" ")}
          />

          <div>
            <p className="text-xs font-semibold tracking-[0.12em] text-muted uppercase">
              Current availability
            </p>

            <h2
              id="overall-system-status-title"
              className="mt-2 text-xl font-bold tracking-[-0.025em]"
            >
              {allServicesReady
                ? "All scouting services operational"
                : "Player data requires attention"}
            </h2>

            <p className="mt-2 text-sm leading-6 text-muted">
              {allServicesReady
                ? "Player search and transfer analysis are ready to use."
                : "Core services are responding, but the player catalogue is not ready."}
            </p>
          </div>
        </div>
      </section>

      <div className="grid gap-5 md:grid-cols-2">
        <StatusCard
          label="Scouting API"
          value="Operational"
          description="Core scouting requests are responding normally."
        />

        <StatusCard
          label="Player data"
          value={
            readiness.status === "ready"
              ? "Ready"
              : "Not ready"
          }
          description={
            readiness.catalog_loaded_at
              ? `Last loaded ${formatTimestamp(
                  readiness.catalog_loaded_at,
                )}`
              : "Load time not reported."
          }
        />
      </div>

      <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-border bg-surface-secondary px-5 py-4 text-sm text-muted">
        <span>
          Last checked{" "}
          {formatTimestamp(checkedAt)}
        </span>

        <button
          type="button"
          className="min-h-11 rounded-lg border border-border bg-surface px-4 py-2 font-semibold text-foreground transition-colors hover:bg-page"
          onClick={() => {
            void refreshStatus();
          }}
        >
          Refresh status
        </button>
      </div>

      <details className="group overflow-hidden rounded-xl border border-border bg-surface">
        <summary className="flex min-h-11 cursor-pointer list-none items-center justify-between gap-4 px-5 py-3.5 font-semibold text-brand-dark transition-colors hover:bg-surface-secondary [&::-webkit-details-marker]:hidden">
          <span>Technical details</span>

          <span
            aria-hidden="true"
            className="text-lg leading-none text-muted transition-transform group-open:rotate-45"
          >
            +
          </span>
        </summary>

        <dl className="grid gap-3 border-t border-border p-4 sm:grid-cols-2 lg:grid-cols-3">
          <TechnicalDetail
            label="Environment"
            value={health.environment}
          />

          <TechnicalDetail
            label="Deployment"
            value={deployment.provider}
          />

          <TechnicalDetail
            label="Version"
            value={deployment.version}
          />

          <TechnicalDetail
            label="Branch"
            value={
              deployment.branch ??
              "Not reported"
            }
          />

          <TechnicalDetail
            label="Dataset fingerprint"
            value={
              deployment.dataset_bundle_sha256
                ? deployment.dataset_bundle_sha256.slice(
                    0,
                    12,
                  )
                : "Not reported"
            }
          />

          <TechnicalDetail
            label="API started"
            value={formatTimestamp(
              health.started_at,
            )}
          />
        </dl>
      </details>
    </div>
  );
}
