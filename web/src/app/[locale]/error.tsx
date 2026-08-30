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
  const t = useTranslations(
    "ApplicationError",
  );

  return (
    <PageContainer className="flex min-h-[60vh] items-center py-16">
      <section
        role="alert"
        className="w-full max-w-3xl rounded-3xl border border-error/25 bg-error/10 p-7 shadow-sm sm:p-10"
      >
        <p className="text-sm font-semibold tracking-[0.14em] text-error uppercase">
          {t("eyebrow")}
        </p>

        <h1 className="mt-4 text-4xl font-bold tracking-[-0.04em]">
          {t("title")}
        </h1>

        <p className="mt-5 max-w-2xl text-sm leading-7 text-muted">
          {t("description")}
        </p>

        {error.digest ? (
          <p className="mt-4 text-xs leading-5 text-muted">
            {t("errorReference")}:{" "}
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
            {t("tryAgain")}
          </button>

          <Link
            href="/players"
            className="rounded-xl border border-border bg-surface px-5 py-3 text-sm font-semibold hover:bg-surface-secondary"
          >
            {t("openPlayers")}
          </Link>

          <Link
            href="/"
            className="rounded-xl border border-border bg-surface px-5 py-3 text-sm font-semibold hover:bg-surface-secondary"
          >
            {t("returnHome")}
          </Link>
        </div>
      </section>
    </PageContainer>
  );
}
