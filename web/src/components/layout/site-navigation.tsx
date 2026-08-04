"use client";

import Link from "next/link";
import {
  usePathname,
} from "next/navigation";
import {
  useState,
} from "react";

import {
  isNavigationItemActive,
  primaryNavigationItems,
} from "@/lib/navigation";

function navigationLinkClasses(
  active: boolean,
): string {
  return [
    "rounded-lg px-3 py-2 text-sm font-medium transition-colors",
    active
      ? "bg-surface-secondary text-brand-dark"
      : "text-muted hover:bg-surface-secondary hover:text-foreground",
  ].join(" ");
}

export function SiteNavigation() {
  const pathname = usePathname();

  const [
    menuOpen,
    setMenuOpen,
  ] = useState(false);

  return (
    <>
      <nav
        aria-label="Primary navigation"
        className="hidden md:block"
      >
        <ul className="flex items-center gap-1">
          {primaryNavigationItems.map(
            (item) => {
              const active =
                isNavigationItemActive(
                  pathname,
                  item,
                );

              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    className={navigationLinkClasses(
                      active,
                    )}
                    aria-current={
                      active
                        ? "page"
                        : undefined
                    }
                  >
                    {item.label}
                  </Link>
                </li>
              );
            },
          )}
        </ul>
      </nav>

      <div className="md:hidden">
        <button
          type="button"
          className="inline-flex size-10 items-center justify-center rounded-lg border border-border bg-surface text-foreground"
          aria-expanded={menuOpen}
          aria-controls="mobile-navigation"
          aria-label={
            menuOpen
              ? "Close navigation"
              : "Open navigation"
          }
          onClick={() => {
            setMenuOpen(
              (current) => !current,
            );
          }}
        >
          {menuOpen ? (
            <svg
              aria-hidden="true"
              viewBox="0 0 24 24"
              className="size-5"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M6 6l12 12M18 6L6 18" />
            </svg>
          ) : (
            <svg
              aria-hidden="true"
              viewBox="0 0 24 24"
              className="size-5"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M4 7h16M4 12h16M4 17h16" />
            </svg>
          )}
        </button>

        {menuOpen ? (
          <nav
            id="mobile-navigation"
            aria-label="Mobile navigation"
            className="absolute inset-x-0 top-full border-b border-border bg-surface shadow-lg"
          >
            <ul className="mx-auto flex max-w-7xl flex-col gap-1 px-5 py-4 sm:px-8">
              {primaryNavigationItems.map(
                (item) => {
                  const active =
                    isNavigationItemActive(
                      pathname,
                      item,
                    );

                  return (
                    <li key={item.href}>
                      <Link
                        href={item.href}
                        className={[
                          navigationLinkClasses(
                            active,
                          ),
                          "block",
                        ].join(" ")}
                        onClick={() => {
                          setMenuOpen(false);
                        }}
                        aria-current={
                          active
                            ? "page"
                            : undefined
                        }
                      >
                        {item.label}
                      </Link>
                    </li>
                  );
                },
              )}
            </ul>
          </nav>
        ) : null}
      </div>
    </>
  );
}
