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
  RoleCompatibilityPanel,
} from "@/components/transfer-intelligence/role-compatibility-panel";
import type {
  TransferRecommendationResponse,
  TransferTargetResponse,
} from "@/lib/api/types";

const target = {
  player_id: 978838,
  player_name: "Michael Olise",
  final_role:
    "Central Half-Space Creator",
  archetype: "Wide Creator",
  spatial_role:
    "Advanced Central Zone",
  lateral_profile:
    "Central Lane",
  vertical_profile:
    "Advanced Middle Third",
  mobility_profile:
    "Positionally Stable",
  role_confidence_pct: 87.2,
} as TransferTargetResponse;

const candidate = {
  player_id: 12345,
  player_name: "Test Candidate",
  final_role:
    "Central Half-Space Creator",
  archetype: "Wide Creator",
  spatial_role:
    "Advanced Central Zone",
  lateral_profile:
    "Right Half-Space",
  vertical_profile:
    "Advanced Middle Third",
  mobility_profile: "Mobile",
  role_confidence_pct: 81.4,

  role_fit_pct: 84.6,
  same_final_role: true,
  same_archetype: true,
} as TransferRecommendationResponse;

describe(
  "RoleCompatibilityPanel",
  () => {
    it(
      "renders backend tactical profile and role confidence",
      () => {
        render(
          <RoleCompatibilityPanel
            target={target}
            candidate={candidate}
          />,
        );

        expect(
          screen.getAllByText(
            "Target",
          ),
        ).toHaveLength(7);

        expect(
          screen.getAllByText(
            "Candidate",
          ),
        ).toHaveLength(7);

        expect(
          screen.getAllByText(
            "Central Half-Space Creator",
          ),
        ).toHaveLength(2);

        expect(
          screen.getByText(
            "Right Half-Space",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Positionally Stable",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Mobile",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Role confidence",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "87.2%",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "81.4%",
          ),
        ).toBeInTheDocument();
      },
    );

    it(
      "does not duplicate equality evidence in the tactical profile",
      () => {
        render(
          <RoleCompatibilityPanel
            target={target}
            candidate={{
              ...candidate,
              same_final_role: false,
              same_archetype: true,
            }}
          />,
        );

        expect(
          screen.queryByText(
            "Same final role",
          ),
        ).not.toBeInTheDocument();

        expect(
          screen.queryByText(
            "Same archetype",
          ),
        ).not.toBeInTheDocument();

        expect(
          screen.getAllByText(
            "Central Half-Space Creator",
          ),
        ).toHaveLength(2);

        expect(
          screen.getAllByText(
            "Wide Creator",
          ),
        ).toHaveLength(2);
      },
    );

    it(
      "keeps missing tactical evidence explicit",
      () => {
        render(
          <RoleCompatibilityPanel
            target={{
              ...target,
              mobility_profile: null,
            }}
            candidate={{
              ...candidate,
              final_role: null,
              same_final_role: null,
            }}
          />,
        );

        expect(
          screen.getAllByText(
            "Not reported",
          ),
        ).toHaveLength(2);

        expect(
          screen.queryByText(
            "Same final role unavailable",
          ),
        ).not.toBeInTheDocument();

        expect(
          screen.getByText(
            "Role confidence",
          ),
        ).toBeInTheDocument();
      },
    );
  },
);
