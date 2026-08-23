import {
  render,
  screen,
} from "@testing-library/react";
import {
  describe,
  expect,
  it,
} from "vitest";

import MethodologyPage from "@/app/methodology/page";

describe(
  "MethodologyPage",
  () => {
    it(
      "explains the current player and comparison evidence",
      () => {
        render(
          <MethodologyPage />,
        );

        expect(
          screen.getByRole(
            "heading",
            {
              name:
                "How to read player evidence",
            },
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Raw and per-90 values",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Same-position percentile",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "From performance profile to tactical role",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Measured heatmap",
          ),
        ).toBeInTheDocument();

        expect(
          screen.queryByText(
            "Dataset and application identity",
          ),
        ).not.toBeInTheDocument();

        expect(
          screen.queryByText(
            "Analytics ownership boundary",
          ),
        ).not.toBeInTheDocument();
      },
    );
  },
);
