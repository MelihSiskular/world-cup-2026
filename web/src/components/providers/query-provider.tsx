"use client";

import {
  QueryClient,
  QueryClientProvider,
} from "@tanstack/react-query";
import {
  useEffect,
  useState,
} from "react";
import type {
  ReactNode,
} from "react";

import {
  ShortlistProvider,
} from "@/components/providers/shortlist-provider";

type QueryProviderProps =
  Readonly<{
    children: ReactNode;
  }>;

export function QueryProvider({
  children,
}: QueryProviderProps) {
  const [
    queryClient,
  ] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30_000,
            retry: 1,
            refetchOnWindowFocus: false,
          },
        },
      }),
  );

  useEffect(() => {
    document.documentElement.dataset.wc26Hydrated =
      "true";

    return () => {
      delete document.documentElement.dataset
        .wc26Hydrated;
    };
  }, []);

  return (
    <QueryClientProvider
      client={queryClient}
    >
      <ShortlistProvider>
        {children}
      </ShortlistProvider>
    </QueryClientProvider>
  );
}
