import Image from "next/image";
import {
  useTranslations,
} from "next-intl";

import {
  LocaleSwitcher,
} from "@/components/layout/locale-switcher";
import {
  PageContainer,
} from "@/components/layout/page-container";
import {
  SiteNavigation,
} from "@/components/layout/site-navigation";
import {
  ApiStatusBadge,
} from "@/components/status/api-status-badge";
import {
  Link,
} from "@/i18n/navigation";

export function SiteHeader() {
  const commonTranslations =
    useTranslations("Common");
  const headerTranslations =
    useTranslations("Header");

  return (
    <header className="relative z-50 border-b border-border bg-surface">
      <PageContainer className="flex min-h-18 items-center justify-between gap-3 sm:gap-6">
        <Link
          href="/"
          className="flex min-w-0 items-center gap-3 rounded-lg"
          aria-label={headerTranslations(
            "homeLabel",
          )}
        >
          <span className="relative flex size-11 shrink-0 items-center justify-center overflow-visible">
            <Image
              src="/brand/world-cup-trophy.png"
              alt=""
              fill
              sizes="44px"
              priority
              className="scale-[1.75] object-contain"
            />
          </span>

          <span className="min-w-0">
            <span className="block truncate text-sm font-bold tracking-[-0.02em] text-foreground">
              {commonTranslations(
                "brandName",
              )}
            </span>

            <span className="hidden text-xs text-muted sm:block">
              {headerTranslations(
                "tagline",
              )}
            </span>
          </span>
        </Link>

        <div className="flex shrink-0 items-center gap-2 sm:gap-3">
          <SiteNavigation />

          <LocaleSwitcher />

          <Link
            href="/status"
            className="hidden rounded-full lg:block"
            aria-label={headerTranslations(
              "statusLabel",
            )}
          >
            <ApiStatusBadge />
          </Link>
        </div>
      </PageContainer>
    </header>
  );
}
