import {
  afterEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

import {
  BrowserApiError,
  requestBrowserJson,
} from "@/lib/api/browser-client";

const fetchMock =
  vi.fn<typeof fetch>();

afterEach(() => {
  fetchMock.mockReset();
});

describe(
  "requestBrowserJson",
  () => {
    it(
      "sends JSON request bodies and returns parsed data",
      async () => {
        fetchMock.mockResolvedValue(
          new Response(
            JSON.stringify({
              ok: true,
            }),
            {
              status: 200,
              headers: {
                "content-type":
                  "application/json",
              },
            },
          ),
        );

        vi.stubGlobal(
          "fetch",
          fetchMock,
        );

        const result =
          await requestBrowserJson<{
            ok: boolean;
          }>(
            "/api/example",
            {
              method: "POST",
              body: {
                player_id: 978838,
              },
            },
          );

        expect(result).toEqual({
          ok: true,
        });

        expect(fetchMock).toHaveBeenCalledTimes(
          1,
        );

        const [
          path,
          options,
        ] =
          fetchMock.mock.calls[0] ??
          [];

        expect(path).toBe(
          "/api/example",
        );

        expect(options).toMatchObject({
          method: "POST",
          cache: "no-store",
          body: JSON.stringify({
            player_id: 978838,
          }),
        });

        expect(
          new Headers(
            options?.headers,
          ).get(
            "content-type",
          ),
        ).toBe(
          "application/json",
        );
      },
    );

    it(
      "maps structured API failures to BrowserApiError",
      async () => {
        fetchMock.mockResolvedValue(
          new Response(
            JSON.stringify({
              error: {
                code:
                  "dataset_unavailable",
                message:
                  "The analytics datasets are unavailable.",
              },
            }),
            {
              status: 503,
              headers: {
                "content-type":
                  "application/json",
                "x-request-id":
                  "request-503",
              },
            },
          ),
        );

        vi.stubGlobal(
          "fetch",
          fetchMock,
        );

        let thrownError:
          unknown;

        try {
          await requestBrowserJson(
            "/api/example",
          );
        } catch (error) {
          thrownError = error;
        }

        expect(
          thrownError,
        ).toBeInstanceOf(
          BrowserApiError,
        );

        expect(
          thrownError,
        ).toMatchObject({
          status: 503,
          code:
            "dataset_unavailable",
          message:
            "The analytics datasets are unavailable.",
          requestId:
            "request-503",
        });
      },
    );

    it(
      "uses a fallback message for non-JSON failures",
      async () => {
        fetchMock.mockResolvedValue(
          new Response(
            "Internal error",
            {
              status: 500,
            },
          ),
        );

        vi.stubGlobal(
          "fetch",
          fetchMock,
        );

        await expect(
          requestBrowserJson(
            "/api/example",
          ),
        ).rejects.toMatchObject({
          status: 500,
          code: null,
          message:
            "The API request failed with HTTP 500.",
        });
      },
    );

    it(
      "returns accepted non-success responses",
      async () => {
        fetchMock.mockResolvedValue(
          new Response(
            JSON.stringify({
              status:
                "not_ready",
            }),
            {
              status: 503,
              headers: {
                "content-type":
                  "application/json",
              },
            },
          ),
        );

        vi.stubGlobal(
          "fetch",
          fetchMock,
        );

        const result =
          await requestBrowserJson<{
            status: string;
          }>(
            "/api/status/ready",
            {
              acceptedStatuses: [
                503,
              ],
            },
          );

        expect(result).toEqual({
          status:
            "not_ready",
        });
      },
    );
  },
);
