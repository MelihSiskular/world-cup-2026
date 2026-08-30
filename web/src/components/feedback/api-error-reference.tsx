"use client";

import {
  useTranslations,
} from "next-intl";

import {
  isBrowserApiError,
} from "@/lib/api/browser-client";

export function ApiErrorReference({
  error,
  label,
}: Readonly<{
  error: unknown;
  label?: string;
}>) {
  const t = useTranslations(
    "ApiErrorReference",
  );

  if (
    !isBrowserApiError(error) ||
    !error.requestId
  ) {
    return null;
  }

  return (
    <p className="mt-4 text-xs leading-5 text-muted">
      {label ??
        t("requestId")}
      :{" "}
      <code className="break-all font-mono text-foreground">
        {error.requestId}
      </code>
    </p>
  );
}
