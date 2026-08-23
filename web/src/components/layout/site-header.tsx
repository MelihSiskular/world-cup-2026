import Image from "next/image";
import Link from "next/link";

import {
  PageContainer,
} from "@/components/layout/page-container";
import {
  SiteNavigation,
} from "@/components/layout/site-navigation";
import {
  ApiStatusBadge,
} from "@/components/status/api-status-badge";

export function SiteHeader() {
  return (
    <header className="relative z-50 border-b border-border bg-surface">
      <PageContainer className="flex min-h-18 items-center justify-between gap-3 sm:gap-6">
        <Link
          href="/"
          className="flex min-w-0 items-center gap-3 rounded-lg"
          aria-label="WC26 Transfer Intelligence home"
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
              WC26 Transfer Intelligence
            </span>

            <span className="hidden text-xs text-muted sm:block">
              Recruitment decision support
            </span>
          </span>
        </Link>

        <div className="flex shrink-0 items-center gap-2 sm:gap-4">
          <SiteNavigation />

          <Link
            href="/status"
            className="hidden rounded-full lg:block"
            aria-label="Open system status page"
          >
            <ApiStatusBadge />
          </Link>
        </div>
      </PageContainer>
    </header>
  );
}