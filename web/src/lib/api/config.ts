import "server-only";

const API_BASE_URL_ENVIRONMENT_VARIABLE =
  "WC26_API_BASE_URL";

const ALLOWED_PROTOCOLS = new Set([
  "http:",
  "https:",
]);

export const DEFAULT_API_TIMEOUT_MS = 15_000;
export const ANALYSIS_API_TIMEOUT_MS = 60_000;

export function getWc26ApiBaseUrl(): string {
  const configuredValue =
    process.env[
      API_BASE_URL_ENVIRONMENT_VARIABLE
    ]?.trim();

  if (!configuredValue) {
    throw new Error(
      `${API_BASE_URL_ENVIRONMENT_VARIABLE} is not configured.`,
    );
  }

  let parsedUrl: URL;

  try {
    parsedUrl = new URL(configuredValue);
  } catch {
    throw new Error(
      `${API_BASE_URL_ENVIRONMENT_VARIABLE} must be a valid URL.`,
    );
  }

  if (!ALLOWED_PROTOCOLS.has(parsedUrl.protocol)) {
    throw new Error(
      `${API_BASE_URL_ENVIRONMENT_VARIABLE} must use HTTP or HTTPS.`,
    );
  }

  parsedUrl.search = "";
  parsedUrl.hash = "";

  return parsedUrl
    .toString()
    .replace(/\/+$/, "");
}
