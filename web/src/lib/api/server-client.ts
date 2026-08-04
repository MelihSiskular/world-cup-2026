import "server-only";

import createClient from "openapi-fetch";

import {
  DEFAULT_API_TIMEOUT_MS,
  getWc26ApiBaseUrl,
} from "@/lib/api/config";
import type { paths } from "@/lib/api/generated/schema";
import {
  REQUEST_ID_HEADER,
} from "@/lib/api/request-id";

type CreateWc26ServerClientOptions =
  Readonly<{
    requestId?: string;
    timeoutMs?: number;
  }>;

function createTimeoutFetch(
  timeoutMs: number,
): typeof fetch {
  return async (
    input: RequestInfo | URL,
    init?: RequestInit,
  ): Promise<Response> => {
    const controller =
      new AbortController();

    const timeoutId = setTimeout(() => {
      controller.abort(
        new DOMException(
          "The WC26 API request timed out.",
          "TimeoutError",
        ),
      );
    }, timeoutMs);

    const incomingSignal = init?.signal;

    const abortFromIncomingSignal = () => {
      controller.abort(
        incomingSignal?.reason,
      );
    };

    if (incomingSignal) {
      if (incomingSignal.aborted) {
        abortFromIncomingSignal();
      } else {
        incomingSignal.addEventListener(
          "abort",
          abortFromIncomingSignal,
          {
            once: true,
          },
        );
      }
    }

    try {
      return await fetch(input, {
        ...init,
        cache: "no-store",
        signal: controller.signal,
      });
    } finally {
      clearTimeout(timeoutId);

      incomingSignal?.removeEventListener(
        "abort",
        abortFromIncomingSignal,
      );
    }
  };
}

export function createWc26ServerClient(
  options: CreateWc26ServerClientOptions = {},
) {
  const timeoutMs =
    options.timeoutMs ??
    DEFAULT_API_TIMEOUT_MS;

  if (
    !Number.isFinite(timeoutMs) ||
    timeoutMs <= 0
  ) {
    throw new Error(
      "WC26 API timeout must be a positive number.",
    );
  }

  const headers = new Headers({
    accept: "application/json",
  });

  if (options.requestId) {
    headers.set(
      REQUEST_ID_HEADER,
      options.requestId,
    );
  }

  return createClient<paths>({
    baseUrl: getWc26ApiBaseUrl(),
    headers,
    fetch: createTimeoutFetch(timeoutMs),
  });
}

export type Wc26ServerClient =
  ReturnType<
    typeof createWc26ServerClient
  >;
