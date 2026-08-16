import {
  render,
  screen,
} from "@testing-library/react";
import {
  describe,
  expect,
  it,
} from "vitest";

import {
  SpatialPositionPitch,
} from "@/components/transfer-intelligence/spatial-position-pitch";

describe(
  "SpatialPositionPitch",
  () => {
    it(
      "renders target and candidate positions",
      () => {
        render(
          <SpatialPositionPitch
            target={{
              playerId: 978838,
              playerName:
                "Michael Olise",
              meanX: 58,
              meanY: 50,
              xStd: 7,
              yStd: 5,
            }}
            candidate={{
              playerId: 12345,
              playerName:
                "Test Candidate",
              meanX: 62,
              meanY: 43,
              xStd: 6,
              yStd: 8,
            }}
          />,
        );

        expect(
          screen.getByRole(
            "img",
            {
              name:
                "Spatial position comparison for Michael Olise and Test Candidate",
            },
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByTestId(
            "target-spatial-position",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByTestId(
            "candidate-spatial-position",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Attacking direction →",
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "keeps zero coordinates as valid evidence",
      () => {
        render(
          <SpatialPositionPitch
            target={{
              playerId: 1,
              playerName: "Target",
              meanX: 0,
              meanY: 0,
            }}
            candidate={{
              playerId: 2,
              playerName: "Candidate",
              meanX: 100,
              meanY: 100,
            }}
          />,
        );

        expect(
          screen.getByTestId(
            "target-spatial-position",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByTestId(
            "candidate-spatial-position",
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "renders an explicit unavailable state",
      () => {
        render(
          <SpatialPositionPitch
            target={{
              playerId: 1,
              playerName: "Target",
              meanX: null,
              meanY: null,
            }}
            candidate={{
              playerId: 2,
              playerName: "Candidate",
              meanX: null,
              meanY: null,
            }}
          />,
        );

        expect(
          screen.getByText(
            /Positional coordinates are not available/,
          ),
        ).toBeInTheDocument();
      },
    );
  },
);
