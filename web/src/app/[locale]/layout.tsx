import type {
  Metadata,
} from "next";
import {
  hasLocale,
  NextIntlClientProvider,
} from "next-intl";
import {
  getMessages,
  getTranslations,
  setRequestLocale,
} from "next-intl/server";
import {
  Geist,
  Geist_Mono,
} from "next/font/google";
import {
  notFound,
} from "next/navigation";

import {
  SiteFooter,
} from "@/components/layout/site-footer";
import {
  SiteHeader,
} from "@/components/layout/site-header";
import {
  QueryProvider,
} from "@/components/providers/query-provider";
import {
  routing,
} from "@/i18n/routing";

import "../globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

type LocaleLayoutProps =
  Readonly<{
    children: React.ReactNode;
    params: Promise<{
      locale: string;
    }>;
  }>;

export async function generateMetadata({
  params,
}: Pick<
  LocaleLayoutProps,
  "params"
>): Promise<Metadata> {
  const {
    locale,
  } = await params;

  const resolvedLocale =
    hasLocale(
      routing.locales,
      locale,
    )
      ? locale
      : routing.defaultLocale;

  const translations =
    await getTranslations({
      locale: resolvedLocale,
      namespace: "Metadata",
    });

  return {
    title: {
      default:
        "WC26 Transfer Intelligence",
      template:
        "%s | WC26 Transfer Intelligence",
    },
    description:
      translations("description"),
  };
}

export function generateStaticParams() {
  return routing.locales.map(
    (locale) => ({
      locale,
    }),
  );
}

export default async function LocaleLayout({
  children,
  params,
}: LocaleLayoutProps) {
  const {
    locale,
  } = await params;

  if (
    !hasLocale(
      routing.locales,
      locale,
    )
  ) {
    notFound();
  }

  setRequestLocale(locale);

  const [
    messages,
    commonTranslations,
  ] = await Promise.all([
    getMessages(),
    getTranslations("Common"),
  ]);

  return (
    <html lang={locale}>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <NextIntlClientProvider
          messages={messages}
        >
          <QueryProvider>
            <a
              href="#main-content"
              className="fixed top-3 left-3 z-[100] -translate-y-24 rounded-lg bg-brand-dark px-4 py-2 text-sm font-semibold text-white transition-transform focus:translate-y-0"
            >
              {commonTranslations(
                "skipToContent",
              )}
            </a>

            <div className="flex min-h-screen flex-col">
              <SiteHeader />

              <main
                id="main-content"
                tabIndex={-1}
                className="flex-1"
              >
                {children}
              </main>

              <SiteFooter />
            </div>
          </QueryProvider>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
