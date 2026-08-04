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
      {children}
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
