"use client";

import {
  useQuery,
} from "@tanstack/react-query";

type DeploymentIdentity =
  Readonly<{
    service: string;
    version: string;
    environment: string;
    provider: string;
    commit_sha: string | null;
    branch: string | null;
    deployment_id: string | null;
    dataset_bundle_sha256:
      | string
      | null;
  }>;

async function fetchDeploymentIdentity(
  signal: AbortSignal,
): Promise<DeploymentIdentity> {
  const response = await fetch(
    "/api/status/deployment",
    {
      headers: {
        accept: "application/json",
      },
      cache: "no-store",
      signal,
    },
  );

  if (!response.ok) {
    throw new Error(
      `Deployment identity request failed with HTTP ${response.status}.`,
    );
  }

  return response.json() as Promise<DeploymentIdentity>;
}

function IdentityField({
  label,
  value,
  code = false,
}: Readonly<{
  label: string;
  value: string;
  code?: boolean;
}>) {
  return (
    <div className="rounded-xl border border-border bg-page p-4">
      <dt className="text-xs font-semibold tracking-[0.1em] text-muted uppercase">
        {label}
      </dt>

      <dd className="mt-2 text-sm font-semibold">
        {code ? (
          <code className="break-all font-mono text-xs leading-5 text-brand-dark">
            {value}
          </code>
        ) : (
          value
        )}
      </dd>
    </div>
  );
}

export function DatasetReleaseIdentity() {
  const identity = useQuery({
    queryKey: [
      "status",
      "deployment",
    ],
    queryFn: ({
      signal,
    }) =>
      fetchDeploymentIdentity(
        signal,
      ),
    staleTime:
      5 * 60 * 1000,
    retry: 1,
  });

  if (identity.isPending) {
    return (
      <section
        aria-labelledby="dataset-release-heading"
        className="animate-pulse rounded-3xl border border-border bg-surface p-6 shadow-sm sm:p-8"
      >
        <div className="h-4 w-40 rounded bg-surface-secondary" />
        <div className="mt-4 h-8 w-72 max-w-full rounded bg-surface-secondary" />

        <div className="mt-7 grid gap-3 sm:grid-cols-2">
          {Array.from({
            length: 4,
          }).map((_, index) => (
            <div
              key={index}
              className="h-20 rounded-xl bg-surface-secondary"
            />
          ))}
        </div>
      </section>
    );
  }

  if (identity.isError) {
    return (
      <section
        aria-labelledby="dataset-release-heading"
        className="rounded-3xl border border-warning/30 bg-warning/10 p-6 sm:p-8"
      >
        <p className="text-sm font-semibold tracking-[0.14em] text-warning uppercase">
          Dataset release
        </p>

        <h2
          id="dataset-release-heading"
          className="mt-3 text-2xl font-bold tracking-[-0.03em]"
        >
          Release identity unavailable
        </h2>

        <p className="mt-3 max-w-2xl text-sm leading-6 text-muted">
          The methodology remains valid, but
          the active backend dataset identity
          could not be retrieved.
        </p>
      </section>
    );
  }

  const {
    environment,
    provider,
    version,
    commit_sha: commitSha,
    dataset_bundle_sha256:
      datasetBundleSha,
  } = identity.data;

  return (
    <section
      aria-labelledby="dataset-release-heading"
      className="rounded-3xl border border-brand/20 bg-surface p-6 shadow-sm sm:p-8"
    >
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold tracking-[0.14em] text-brand uppercase">
            Active release
          </p>

          <h2
            id="dataset-release-heading"
            className="mt-3 text-3xl font-bold tracking-[-0.04em]"
          >
            Dataset and application identity
          </h2>

          <p className="mt-3 max-w-3xl text-sm leading-6 text-muted">
            Recommendation results are tied
            to a specific application release
            and immutable runtime dataset
            manifest.
          </p>
        </div>

        <span className="rounded-full bg-surface-secondary px-3 py-1.5 text-xs font-semibold text-brand-dark">
          Live backend identity
        </span>
      </div>

      <dl className="mt-7 grid gap-3 sm:grid-cols-2">
        <IdentityField
          label="Environment"
          value={environment}
        />

        <IdentityField
          label="Provider"
          value={provider}
        />

        <IdentityField
          label="API version"
          value={version}
        />

        <IdentityField
          label="Application commit"
          value={
            commitSha ??
            "Not reported"
          }
          code={commitSha !== null}
        />

        <div className="sm:col-span-2">
          <IdentityField
            label="Dataset bundle SHA-256"
            value={
              datasetBundleSha ??
              "Not reported"
            }
            code={
              datasetBundleSha !==
              null
            }
          />
        </div>
      </dl>
    </section>
  );
}
