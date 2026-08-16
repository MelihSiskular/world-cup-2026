import {
  afterEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

vi.mock("server-only", () => ({}));

import {
  handleOpenApiRequest,
} from "./route-handler";

describe("handleOpenApiRequest failure handling", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("maps upstream timeouts to a 504 response and preserves the request ID", async () => {
    vi.spyOn(
      console,
      "error",
    ).mockImplementation(() => {});

    const response =
      await handleOpenApiRequest(
        "request-timeout",
        async () => {
          throw new DOMException(
            "The WC26 API request timed out.",
            "TimeoutError",
          );
        },
      );

    expect(response.status).toBe(504);

    expect(
      response.headers.get(
        "x-request-id",
      ),
    ).toBe("request-timeout");

    await expect(
      response.json(),
    ).resolves.toEqual({
      error: {
        code: "upstream_timeout",
        message:
          "The analytics API did not respond in time.",
      },
    });
  });

  it("maps generic upstream failures to a 503 response and preserves the request ID", async () => {
    vi.spyOn(
      console,
      "error",
    ).mockImplementation(() => {});

    const response =
      await handleOpenApiRequest(
        "request-unavailable",
        async () => {
          throw new Error(
            "Connection refused",
          );
        },
      );

    expect(response.status).toBe(503);

    expect(
      response.headers.get(
        "x-request-id",
      ),
    ).toBe("request-unavailable");

    await expect(
      response.json(),
    ).resolves.toEqual({
      error: {
        code: "upstream_unavailable",
        message:
          "The analytics API is temporarily unavailable.",
      },
    });
  });
});
