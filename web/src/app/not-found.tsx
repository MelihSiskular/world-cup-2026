import Link from "next/link";

import {
  PageContainer,
} from "@/components/layout/page-container";

export default function NotFoundPage() {
  return (
    <PageContainer className="flex min-h-[60vh] items-center py-16">
      <div className="max-w-2xl">
        <p className="font-mono text-sm font-semibold text-brand">
          404
        </p>

        <h1 className="mt-4 text-4xl font-bold tracking-[-0.04em]">
          This page is outside the analysis zone.
        </h1>

        <p className="mt-5 text-lg leading-8 text-muted">
          The requested WC26 resource could not be found or may
          not exist yet.
        </p>

        <div className="mt-8 flex flex-wrap gap-3">
          <Link
            href="/"
            className="rounded-xl bg-brand px-5 py-3 text-sm font-semibold text-white"
          >
            Return home
          </Link>

          <Link
            href="/players"
            className="rounded-xl border border-border bg-surface px-5 py-3 text-sm font-semibold"
          >
            Open players
          </Link>
        </div>
      </div>
    </PageContainer>
  );
}
