import Link from "next/link";

import {
  PageContainer,
} from "@/components/layout/page-container";

export function SiteFooter() {
  const currentYear =
    new Date().getFullYear();

  return (
    <footer className="border-t border-border bg-surface">
      <PageContainer className="flex flex-col gap-6 py-8 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm font-semibold text-foreground">
            WC26 Transfer Intelligence
          </p>

          <p className="mt-1 max-w-xl text-sm leading-6 text-muted">
            Football scouting and replacement analysis
              <br />
              powered by World Cup 2026 tournament data.
          </p>
        </div>

        <div className="flex flex-col gap-3 text-sm text-muted sm:items-end">
          <nav
            aria-label="Footer navigation"
            className="flex items-center gap-5"
          >
            <Link
              href="/methodology"
              className="transition-colors hover:text-brand"
            >
              Methodology
            </Link>

            <Link
              href="/status"
              className="transition-colors hover:text-brand"
            >
              System Status
            </Link>
          </nav>

          <p>
            © {currentYear} WC26 Analytics
          </p>
        </div>
      </PageContainer>
    </footer>
  );
}
