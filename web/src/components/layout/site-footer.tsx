import {
  useTranslations,
} from "next-intl";

import {
  PageContainer,
} from "@/components/layout/page-container";
import {
  Link,
} from "@/i18n/navigation";

export function SiteFooter() {
  const commonTranslations =
    useTranslations("Common");
  const footerTranslations =
    useTranslations("Footer");
  const navigationTranslations =
    useTranslations("Navigation");

  const currentYear =
    new Date().getFullYear();

  return (
    <footer className="border-t border-border bg-surface">
      <PageContainer className="flex flex-col gap-6 py-8 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm font-semibold text-foreground">
            {commonTranslations(
              "brandName",
            )}
          </p>

          <p className="mt-1 max-w-xl text-sm leading-6 text-muted">
            {footerTranslations(
              "description",
            )}
          </p>
        </div>

        <div className="flex flex-col gap-3 text-sm text-muted sm:items-end">
          <nav
            aria-label={footerTranslations(
              "navigationLabel",
            )}
            className="flex items-center gap-5"
          >
            <Link
              href="/methodology"
              className="transition-colors hover:text-brand"
            >
              {navigationTranslations(
                "methodology",
              )}
            </Link>

            <Link
              href="/status"
              className="transition-colors hover:text-brand"
            >
              {navigationTranslations(
                "systemStatus",
              )}
            </Link>
          </nav>

          <p>
            {footerTranslations(
              "copyright",
              {
                year: currentYear,
              },
            )}
          </p>
        </div>
      </PageContainer>
    </footer>
  );
}
