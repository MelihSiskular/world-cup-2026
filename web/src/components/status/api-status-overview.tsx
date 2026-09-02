"use client";

import {
  useLocale,
  useTranslations,
} from "next-intl";
import {
  useEffect,
  useState,
} from "react";

import {
  fetchApiHealth,
  fetchApiReadiness,
} from "@/lib/api/browser-status";
import type {
  HealthResponse,
  ReadinessResponse,
} from "@/lib/api/types";

type StatusSnapshot = Readonly<{
  health: HealthResponse;
  readiness: ReadinessResponse;
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
  ] = await Promise.all([
    fetchApiHealth(signal),
    fetchApiReadiness(signal),
  ]);

  return {
    health,
    readiness,
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
  fallback: string,
): string {
  return error instanceof Error
    ? error.message
    : fallback;
}

function formatTimestamp(
  value: string | null,
  locale: string,
  notReported: string,
): string {
  if (!value) {
    return notReported;
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat(
    locale,
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

export function ApiStatusOverview() {
  const locale = useLocale();
  const t = useTranslations(
    "ApiStatusOverview",
  );

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
            getStatusErrorMessage(
              error,
              t("loadFailed"),
            ),
        });
      },
    );

    return () => {
      controller.abort();
    };
  }, [t]);

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
            getStatusErrorMessage(
              error,
              t("loadFailed"),
            ),
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
        {t("checking")}
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
          {t("unavailable")}
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
          {t("retry")}
        </button>
      </div>
    );
  }

  const {
    health,
    readiness,
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
              {t("currentAvailability")}
            </p>

            <h2
              id="overall-system-status-title"
              className="mt-2 text-xl font-bold tracking-[-0.025em]"
            >
              {allServicesReady
                ? t("allOperational")
                : t(
                    "playerDataAttention",
                  )}
            </h2>

            <p className="mt-2 text-sm leading-6 text-muted">
              {allServicesReady
                ? t(
                    "allOperationalDescription",
                  )
                : t(
                    "playerDataAttentionDescription",
                  )}
            </p>
          </div>
        </div>
      </section>

      <div className="grid gap-5 md:grid-cols-2">
        <StatusCard
          label={t(
            "analysisService",
          )}
          value={t("operational")}
          description={t(
            "analysisServiceDescription",
          )}
        />

        <StatusCard
          label={t("playerData")}
          value={
            readiness.status === "ready"
              ? t("ready")
              : t("notReady")
          }
          description={
            readiness.catalog_loaded_at
              ? t("lastLoaded", {
                  timestamp:
                    formatTimestamp(
                      readiness
                        .catalog_loaded_at,
                      locale,
                      t("notReported"),
                    ),
                })
              : t(
                  "loadTimeNotReported",
                )
          }
        />
      </div>

      <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-border bg-surface-secondary px-5 py-4 text-sm text-muted">
        <span>
          {t("lastChecked", {
            timestamp:
              formatTimestamp(
                checkedAt,
                locale,
                t("notReported"),
              ),
          })}
        </span>

        <button
          type="button"
          className="min-h-11 rounded-lg border border-border bg-surface px-4 py-2 font-semibold text-foreground transition-colors hover:bg-page"
          onClick={() => {
            void refreshStatus();
          }}
        >
          {t("refresh")}
        </button>
      </div>
    </div>
  );
}
