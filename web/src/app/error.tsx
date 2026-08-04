"use client";

import Link from "next/link";

import {
  PageContainer,
} from "@/components/layout/page-container";

type ApplicationErrorPageProps =
  Readonly<{
    error: Error & {
      digest?: string;
    };
    reset: () => void;
  }>;

export default function ApplicationErrorPage({
  error,
  reset,
}: ApplicationErrorPageProps) {
  return (
    <PageContainer className="flex min-h-[60vh] items-center py-16">
      <section
        role="alert"
        className="w-full max-w-3xl rounded-3xl border border-error/25 bg-error/10 p-7 shadow-sm sm:p-10"
      >
        <p className="text-sm font-semibold tracking-[0.14em] text-error uppercase">
          Application error
        </p>

        <h1 className="mt-4 text-4xl font-bold tracking-[-0.04em]">
          This analysis view could not be displayed
        </h1>

        <p className="mt-5 max-w-2xl text-sm leading-7 text-muted">
          An unexpected error interrupted the
          current page. Retry the view or
          return to a stable part of the
          application.
        </p>

        {error.digest ? (
          <p className="mt-4 text-xs leading-5 text-muted">
            Error reference:{" "}
            <code className="break-all font-mono text-foreground">
              {error.digest}
            </code>
          </p>
        ) : null}

        <div className="mt-8 flex flex-wrap gap-3">
          <button
            type="button"
            onClick={reset}
            className="rounded-xl bg-brand px-5 py-3 text-sm font-semibold text-white hover:bg-brand-dark"
          >
            Try again
          </button>

          <Link
            href="/players"
            className="rounded-xl border border-border bg-surface px-5 py-3 text-sm font-semibold hover:bg-surface-secondary"
          >
            Open players
          </Link>

          <Link
            href="/"
            className="rounded-xl border border-border bg-surface px-5 py-3 text-sm font-semibold hover:bg-surface-secondary"
          >
            Return home
          </Link>
        </div>
      </section>
    </PageContainer>
  );
}
