import {
  render,
  screen,
} from "@testing-library/react";
import {
  describe,
  expect,
  it,
  vi,
} from "vitest";

import MultiPlayerComparisonPage, {
  metadata,
} from "@/app/compare/multi/[targetId]/page";

vi.mock(
  "next/navigation",
  () => ({
    notFound: () => {
      throw new Error(
        "NEXT_NOT_FOUND",
      );
    },
  }),
);

vi.mock(
  "@/components/transfer-intelligence/multi-player-comparison",
  () => ({
    MultiPlayerComparison: ({
      identifiers,
    }: Readonly<{
      identifiers: Readonly<{
        targetPlayerId: number;
        candidatePlayerIds:
          readonly number[];
      }>;
    }>) => (
      <div data-testid="multi-player-comparison">
        Target{" "}
        {
          identifiers
            .targetPlayerId
        }
        ; candidates{" "}
        {
          identifiers
            .candidatePlayerIds
            .join(",")
        }
      </div>
    ),
  }),
);

describe(
  "MultiPlayerComparisonPage",
  () => {
    it(
      "publishes comparison-specific metadata",
      () => {
        expect(
          metadata.title,
        ).toBe(
          "Multi-player comparison",
        );

        expect(
          metadata.description,
        ).toContain(
          "same-position",
        );
      },
    );

    it(
      "hydrates the canonical ordered comparison selection",
      async () => {
        render(
          await MultiPlayerComparisonPage({
            params:
              Promise.resolve({
                targetId:
                  "978838",
              }),
            searchParams:
              Promise.resolve({
                candidates:
                  "789071,805078,123456",
              }),
          }),
        );

        expect(
          screen.getByTestId(
            "multi-player-comparison",
          ),
        ).toHaveTextContent(
          "Target 978838; candidates 789071,805078,123456",
        );

        expect(
          screen.getByRole(
            "link",
            {
              name:
                "Back to shortlists",
            },
          ),
        ).toHaveAttribute(
          "href",
          "/shortlists",
        );
      },
    );

    it(
      "rejects a non-canonical comparison URL",
      async () => {
        await expect(
          MultiPlayerComparisonPage({
            params:
              Promise.resolve({
                targetId:
                  "978838",
              }),
            searchParams:
              Promise.resolve({
                candidates: [
                  "789071",
                  "805078",
                ],
              }),
          }),
        ).rejects.toThrow(
          "NEXT_NOT_FOUND",
        );
      },
    );
  },
);
