"use client";

import {
  useTranslations,
} from "next-intl";
import {
  useEffect,
  useState,
} from "react";

import {
  fetchApiReadiness,
} from "@/lib/api/browser-status";

type ApiStatusState =
  | "checking"
  | "ready"
  | "not_ready"
  | "unavailable";

const containerClasses:
  Record<ApiStatusState, string> = {
    checking:
      "border-border bg-surface-secondary text-muted",
    ready:
      "border-success/25 bg-success/10 text-success",
    not_ready:
      "border-warning/25 bg-warning/10 text-warning",
    unavailable:
      "border-error/25 bg-error/10 text-error",
  };

const indicatorClasses:
  Record<ApiStatusState, string> = {
    checking: "bg-muted",
    ready: "bg-success",
    not_ready: "bg-warning",
    unavailable: "bg-error",
  };

export function ApiStatusBadge() {
  const t = useTranslations(
    "ApiStatusBadge",
  );

  const statusLabels:
    Record<ApiStatusState, string> = {
      checking: t("checking"),
      ready: t("ready"),
      not_ready:
        t("notReady"),
      unavailable:
        t("unavailable"),
    };

  const [
    status,
    setStatus,
  ] = useState<ApiStatusState>(
    "checking",
  );

  useEffect(() => {
    const controller =
      new AbortController();

    async function checkReadiness() {
      try {
        const readiness =
          await fetchApiReadiness(
            controller.signal,
          );

        setStatus(
          readiness.status === "ready"
            ? "ready"
            : "not_ready",
        );
      } catch (error) {
        if (
          error instanceof DOMException &&
          error.name === "AbortError"
        ) {
          return;
        }

        setStatus("unavailable");
      }
    }

    void checkReadiness();

    return () => {
      controller.abort();
    };
  }, []);

  return (
    <span
      className={[
        "inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-semibold whitespace-nowrap",
        containerClasses[status],
      ].join(" ")}
      role="status"
      aria-live="polite"
    >
      <span
        aria-hidden="true"
        className={[
          "size-2 rounded-full",
          indicatorClasses[status],
          status === "checking"
            ? "animate-pulse"
            : "",
        ].join(" ")}
      />

      {statusLabels[status]}
    </span>
  );
}
