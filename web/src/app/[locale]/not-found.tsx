"use client";

import {
  useTranslations,
} from "next-intl";

import {
  Link,
} from "@/i18n/navigation";

import {
  PageContainer,
} from "@/components/layout/page-container";

export default function NotFoundPage() {
  const t = useTranslations(
    "NotFound",
  );

  return (
    <PageContainer className="flex min-h-[60vh] items-center py-16">
      <div className="max-w-2xl">
        <p className="font-mono text-sm font-semibold text-brand">
          404
        </p>

        <h1 className="mt-4 text-4xl font-bold tracking-[-0.04em]">
          {t("title")}
        </h1>

        <p className="mt-5 text-lg leading-8 text-muted">
          {t("description")}
        </p>

        <div className="mt-8 flex flex-wrap gap-3">
          <Link
            href="/"
            className="rounded-xl bg-brand px-5 py-3 text-sm font-semibold text-white"
          >
            {t("returnHome")}
          </Link>

          <Link
            href="/players"
            className="rounded-xl border border-border bg-surface px-5 py-3 text-sm font-semibold"
          >
            {t("openPlayers")}
          </Link>
        </div>
      </div>
    </PageContainer>
  );
}
