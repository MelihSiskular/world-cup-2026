import {
  getOrCreateRequestId,
} from "@/lib/api/request-id";
import {
  handleOpenApiRequest,
} from "@/lib/api/route-handler";
import {
  createWc26ServerClient,
} from "@/lib/api/server-client";

export async function GET(
  request: Request,
): Promise<Response> {
  const requestId =
    getOrCreateRequestId(
      request.headers,
    );

  return handleOpenApiRequest(
    requestId,
    async () => {
      const client =
        createWc26ServerClient({
          requestId,
        });

      return client.GET("/ready");
    },
    {
      preserveNonSuccessBody: true,
    },
  );
}
