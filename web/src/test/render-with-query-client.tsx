import {
  QueryClient,
  QueryClientProvider,
} from "@tanstack/react-query";
import {
  render,
} from "@testing-library/react";
import type {
  ReactElement,
  ReactNode,
} from "react";

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

function TestQueryProvider({
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
  );
}

export function renderWithQueryClient(
  element: ReactElement,
) {
  return render(
    element,
    {
      wrapper:
        TestQueryProvider,
    },
  );
}
