"use client";

import {
  useLocale,
  useTranslations,
} from "next-intl";
import {
  useTransition,
} from "react";

import {
  CountryFlag,
} from "@/components/players/country-flag";
import {
  usePathname,
  useRouter,
} from "@/i18n/navigation";
import type {
  AppLocale,
} from "@/i18n/routing";

const localeOptions = [
  {
    locale: "en",
    messageKey: "english",
    shortLabel: "EN",
    countryAlpha3: "GBR",
  },
  {
    locale: "tr",
    messageKey: "turkish",
    shortLabel: "TR",
    countryAlpha3: "TUR",
  },
] as const satisfies ReadonlyArray<{
  locale: AppLocale;
  messageKey:
    | "english"
    | "turkish";
  shortLabel: string;
  countryAlpha3: string;
}>;

export function LocaleSwitcher() {
  const locale = useLocale();
  const translations =
    useTranslations(
      "LocaleSwitcher",
    );
  const pathname = usePathname();
  const router = useRouter();

  const [
    pending,
    startTransition,
  ] = useTransition();

  return (
    <div
      role="group"
      aria-label={translations(
        "label",
      )}
      className="inline-flex shrink-0 rounded-xl border border-border bg-surface-secondary p-1"
    >
      {localeOptions.map(
        (option) => {
          const active =
            locale ===
            option.locale;

          return (
            <button
              key={option.locale}
              type="button"
              aria-pressed={active}
              aria-label={translations(
                "changeTo",
                {
                  language:
                    translations(
                      option.messageKey,
                    ),
                },
              )}
              disabled={
                active ||
                pending
              }
              className={[
                "inline-flex min-h-9 min-w-9 items-center justify-center gap-1.5 rounded-lg px-2 text-xs font-bold transition-colors sm:min-w-14",
                active
                  ? "bg-brand-dark text-white"
                  : "text-muted hover:bg-surface hover:text-foreground",
                pending
                  ? "cursor-wait"
                  : "",
              ].join(" ")}
              onClick={() => {
                const destination =
                  `${pathname}${window.location.search}`;

                startTransition(
                  () => {
                    router.replace(
                      destination,
                      {
                        locale:
                          option.locale,
                      },
                    );
                  },
                );
              }}
            >
              <CountryFlag
                countryAlpha3={
                  option.countryAlpha3
                }
              />

              <span className="hidden sm:inline">
                {option.shortLabel}
              </span>
            </button>
          );
        },
      )}
    </div>
  );
}
