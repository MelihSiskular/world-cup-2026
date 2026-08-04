import { mkdir, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const DEFAULT_API_BASE_URL =
  "https://world-cup-2026-production.up.railway.app";

const SCRIPT_DIRECTORY = dirname(fileURLToPath(import.meta.url));
const WEB_ROOT = resolve(SCRIPT_DIRECTORY, "..");
const OUTPUT_PATH = resolve(
  WEB_ROOT,
  "openapi",
  "wc26.openapi.json",
);

function normalizeBaseUrl(value) {
  return value.replace(/\/+$/, "");
}

function getSchemaUrl() {
  const explicitSchemaUrl = process.env.WC26_OPENAPI_URL?.trim();

  if (explicitSchemaUrl) {
    return explicitSchemaUrl;
  }

  const baseUrl = normalizeBaseUrl(
    process.env.WC26_API_BASE_URL?.trim() ||
      DEFAULT_API_BASE_URL,
  );

  return `${baseUrl}/openapi.json`;
}

function assertOpenApiDocument(document) {
  if (
    typeof document !== "object" ||
    document === null ||
    Array.isArray(document)
  ) {
    throw new Error("The downloaded schema is not a JSON object.");
  }

  if (
    typeof document.openapi !== "string" ||
    !document.openapi.startsWith("3.")
  ) {
    throw new Error(
      "The downloaded document is not an OpenAPI 3.x schema.",
    );
  }

  if (
    typeof document.paths !== "object" ||
    document.paths === null ||
    Array.isArray(document.paths)
  ) {
    throw new Error(
      "The OpenAPI document does not contain a valid paths object.",
    );
  }
}

async function main() {
  const schemaUrl = getSchemaUrl();

  console.log(`Fetching OpenAPI schema from ${schemaUrl}`);

  const response = await fetch(schemaUrl, {
    headers: {
      accept: "application/json",
      "user-agent": "wc26-web-contract-generator",
    },
    signal: AbortSignal.timeout(30_000),
  });

  if (!response.ok) {
    throw new Error(
      `OpenAPI request failed with HTTP ${response.status}.`,
    );
  }

  const document = await response.json();

  assertOpenApiDocument(document);

  await mkdir(dirname(OUTPUT_PATH), {
    recursive: true,
  });

  await writeFile(
    OUTPUT_PATH,
    `${JSON.stringify(document, null, 2)}\n`,
    "utf8",
  );

  const pathCount = Object.keys(document.paths).length;
  const schemaCount = Object.keys(
    document.components?.schemas ?? {},
  ).length;

  console.log(`Saved schema to ${OUTPUT_PATH}`);
  console.log(`OpenAPI version: ${document.openapi}`);
  console.log(`Paths: ${pathCount}`);
  console.log(`Component schemas: ${schemaCount}`);
}

main().catch((error) => {
  const message =
    error instanceof Error
      ? error.message
      : "Unknown OpenAPI download error.";

  console.error(`OpenAPI download failed: ${message}`);
  process.exitCode = 1;
});
