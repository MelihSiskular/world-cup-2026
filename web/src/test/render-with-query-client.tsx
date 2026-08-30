import {
  QueryClient,
  QueryClientProvider,
} from "@tanstack/react-query";
import {
  render,
} from "@testing-library/react";
import {
  NextIntlClientProvider,
} from "next-intl";
import type {
  ReactElement,
  ReactNode,
} from "react";

import englishMessages from "../../messages/en.json";
import turkishMessages from "../../messages/tr.json";

import {
  ShortlistProvider,
} from "@/components/providers/shortlist-provider";
import type {
  ShortlistStorageAdapter,
} from "@/lib/shortlists/storage";

const testShortlistStorage:
  ShortlistStorageAdapter = {
    getItem() {
      return null;
    },
    setItem() {
      // Persistence behavior is covered
      // by shortlist provider tests.
    },
  };

type TestLocale =
  "en" | "tr";

function createTestQueryProvider(
  locale: TestLocale,
) {
  const messages =
    locale === "tr"
      ? turkishMessages
      : englishMessages;

  return function TestQueryProvider({
    children,
  }: Readonly<{
    children: ReactNode;
  }>) {
    const queryClient =
      new QueryClient({
        defaultOptions: {
          queries: {
            retry: false,
            gcTime: Infinity,
          },
          mutations: {
            retry: false,
          },
        },
      });

    return (
      <NextIntlClientProvider
        locale={locale}
        messages={messages}
      >
        <QueryClientProvider
          client={queryClient}
        >
          <ShortlistProvider
            storage={
              testShortlistStorage
            }
          >
            {children}
          </ShortlistProvider>
        </QueryClientProvider>
      </NextIntlClientProvider>
    );
  };
}

export function renderWithQueryClient(
  element: ReactElement,
  locale: TestLocale = "en",
) {
  return render(
    element,
    {
      wrapper:
        createTestQueryProvider(
          locale,
        ),
    },
  );
}
