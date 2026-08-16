import {
  afterEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

import {
  createWc26ServerClient,
} from "./server-client";

describe("createWc26ServerClient timeout handling", () => {
  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
    vi.unstubAllEnvs();
  });

  it("aborts an upstream request when the configured timeout expires", async () => {
    vi.useFakeTimers();

    vi.stubEnv(
      "WC26_API_BASE_URL",
      "https://api.example.test",
    );

    let observedSignal:
      | AbortSignal
      | null = null;

    vi.spyOn(
      globalThis,
      "fetch",
    ).mockImplementation(
      async (
        _input,
        init,
      ) => {
        observedSignal =
          init?.signal ?? null;

        return await new Promise<Response>(
          (_resolve, reject) => {
            if (!observedSignal) {
              reject(
                new Error(
                  "Expected an abort signal.",
                ),
              );

              return;
            }

            const handleAbort = () => {
              reject(
                observedSignal?.reason ??
                  new DOMException(
                    "Aborted",
                    "AbortError",
                  ),
              );
            };

            if (observedSignal.aborted) {
              handleAbort();
              return;
            }

            observedSignal.addEventListener(
              "abort",
              handleAbort,
              {
                once: true,
              },
            );
          },
        );
      },
    );

    const client =
      createWc26ServerClient({
        timeoutMs: 100,
      });

    const requestPromise =
      client.GET("/health");

    const rejectionExpectation =
      expect(
        requestPromise,
      ).rejects.toMatchObject({
        name: "TimeoutError",
      });

    await vi.advanceTimersByTimeAsync(
      100,
    );

    await rejectionExpectation;

   const finalSignal = observedSignal as AbortSignal | null;

    expect(
    finalSignal,
    ).not.toBeNull();

    expect(
    finalSignal?.aborted,
    ).toBe(true);

  });

  it("rejects invalid timeout configuration", () => {
    vi.stubEnv(
      "WC26_API_BASE_URL",
      "https://api.example.test",
    );

    expect(() =>
      createWc26ServerClient({
        timeoutMs: 0,
      }),
    ).toThrow(
      "WC26 API timeout must be a positive number.",
    );

    expect(() =>
      createWc26ServerClient({
        timeoutMs: -1,
      }),
    ).toThrow(
      "WC26 API timeout must be a positive number.",
    );
  });
});
