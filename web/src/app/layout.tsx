import type {
  Metadata,
} from "next";
import {
  Geist,
  Geist_Mono,
} from "next/font/google";

import {
  SiteFooter,
} from "@/components/layout/site-footer";
import {
  SiteHeader,
} from "@/components/layout/site-header";
import {
  QueryProvider,
} from "@/components/providers/query-provider";

import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: {
    default: "WC26 Transfer Intelligence",
    template: "%s | WC26 Transfer Intelligence",
  },
  description:
    "Football scouting and player replacement analysis powered by World Cup 2026 data.",
};

type RootLayoutProps =
  Readonly<{
    children: React.ReactNode;
  }>;

export default function RootLayout({
  children,
}: RootLayoutProps) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <QueryProvider>
          <a
            href="#main-content"
            className="fixed top-3 left-3 z-[100] -translate-y-24 rounded-lg bg-brand-dark px-4 py-2 text-sm font-semibold text-white transition-transform focus:translate-y-0"
          >
            Skip to content
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
      </body>
    </html>
  );
}
