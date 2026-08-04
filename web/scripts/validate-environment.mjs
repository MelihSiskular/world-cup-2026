const variableName =
  "WC26_API_BASE_URL";

const configuredValue =
  process.env[
    variableName
  ]?.trim();

function fail(
  message,
) {
  console.error(
    `Environment validation failed: ${message}`,
  );

  process.exit(1);
}

if (!configuredValue) {
  fail(
    `${variableName} is not configured.`,
  );
}

let parsedUrl;

try {
  parsedUrl =
    new URL(
      configuredValue,
    );
} catch {
  fail(
    `${variableName} must be a valid URL.`,
  );
}

if (
  parsedUrl.protocol !== "http:" &&
  parsedUrl.protocol !== "https:"
) {
  fail(
    `${variableName} must use HTTP or HTTPS.`,
  );
}

if (
  parsedUrl.username ||
  parsedUrl.password
) {
  fail(
    `${variableName} must not contain credentials.`,
  );
}

if (
  parsedUrl.pathname !== "/" ||
  parsedUrl.search ||
  parsedUrl.hash
) {
  fail(
    `${variableName} must contain only the API origin, without a path, query string or fragment.`,
  );
}

const vercelEnvironment =
  process.env.VERCEL_ENV
    ?.trim()
    .toLowerCase();

const requiresHttps =
  process.env.CI === "true" ||
  vercelEnvironment ===
    "preview" ||
  vercelEnvironment ===
    "production";

if (
  requiresHttps &&
  parsedUrl.protocol !== "https:"
) {
  fail(
    `${variableName} must use HTTPS in CI, Vercel Preview and Vercel Production.`,
  );
}

console.log(
  [
    "Frontend environment validated.",
    `${variableName}=${parsedUrl.origin}`,
  ].join("\n"),
);
