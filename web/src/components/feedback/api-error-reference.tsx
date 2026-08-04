import {
  isBrowserApiError,
} from "@/lib/api/browser-client";

export function ApiErrorReference({
  error,
}: Readonly<{
  error: unknown;
}>) {
  if (
    !isBrowserApiError(error) ||
    !error.requestId
  ) {
    return null;
  }

  return (
    <p className="mt-4 text-xs leading-5 text-muted">
      Request ID:{" "}
      <code className="break-all font-mono text-foreground">
        {error.requestId}
      </code>
    </p>
  );
}
