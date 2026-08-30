import {
  screen,
  waitFor,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

import {
  TransferAnalysisForm,
} from "@/components/transfer-intelligence/transfer-analysis-form";
import {
  fetchPlayerProfile,
} from "@/lib/api/browser-players";
import {
  runTransferAnalysis,
} from "@/lib/api/browser-transfer-intelligence";
import type {
  PlayerProfileResponse,
  TransferAnalysisResponse,
} from "@/lib/api/types";
import {
  DEFAULT_TRANSFER_ANALYSIS_VALUES,
} from "@/lib/transfer-intelligence/analysis-form";
import {
  renderWithQueryClient,
} from "@/test/render-with-query-client";

const {
  pushMock,
} = vi.hoisted(
  () => ({
    pushMock: vi.fn(),
  }),
);

vi.mock(
  "@/i18n/navigation",
  () => ({
    useRouter: () => ({
      push: pushMock,
    }),
  }),
);

vi.mock(
  "@/lib/api/browser-players",
  () => ({
    fetchPlayerProfile:
      vi.fn(),
  }),
);

vi.mock(
  "@/lib/api/browser-transfer-intelligence",
  () => ({
    runTransferAnalysis:
      vi.fn(),
  }),
);

const fetchPlayerProfileMock =
  vi.mocked(
    fetchPlayerProfile,
  );

const runTransferAnalysisMock =
  vi.mocked(
    runTransferAnalysis,
  );

const playerProfile = {
  player_id: 978838,
  player_name:
    "Michael Olise",
  country_alpha3: "FRA",
  country_name: "France",
  national_team_name:
    "France",
  final_role:
    "Central Half-Space Creator",
  minutes: 650,
  role_confidence_pct: 87.2,
  player_quality_score: 85.5,
} as unknown as PlayerProfileResponse;

describe(
  "TransferAnalysisForm",
  () => {
    beforeEach(() => {
      pushMock.mockReset();

      fetchPlayerProfileMock
        .mockReset();

      runTransferAnalysisMock
        .mockReset();

      fetchPlayerProfileMock
        .mockResolvedValue(
          playerProfile,
        );

      runTransferAnalysisMock
        .mockResolvedValue(
          {} as TransferAnalysisResponse,
        );
    });

    it(
      "localizes the form and validation feedback in Turkish",
      async () => {
        const user =
          userEvent.setup();

        renderWithQueryClient(
          <TransferAnalysisForm
            playerId={978838}
            initialValues={{
              ...DEFAULT_TRANSFER_ANALYSIS_VALUES,
            }}
          />,
          "tr",
        );

        expect(
          await screen.findByText(
            "Michael Olise",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByRole(
            "heading",
            {
              name:
                "Aday havuzu",
            },
          ),
        ).toBeInTheDocument();

        const minutesInput =
          screen.getByRole(
            "textbox",
            {
              name:
                /Turnuva deneyimi/,
            },
          );

        await user.clear(
          minutesInput,
        );

        await user.type(
          minutesInput,
          "-1",
        );

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Transfer alternatiflerini bul",
            },
          ),
        );

        expect(
          await screen.findByRole(
            "alert",
          ),
        ).toHaveTextContent(
          "Sıfır veya daha yüksek bir turnuva dakikası girin.",
        );

        expect(
          pushMock,
        ).not.toHaveBeenCalled();
      },
    );

    it(
      "renders unavailable target metrics without inventing zero values",
      async () => {
        fetchPlayerProfileMock
          .mockResolvedValue({
            ...playerProfile,
            minutes: null,
            role_confidence_pct:
              null,
            player_quality_score:
              null,
          } as unknown as PlayerProfileResponse);

        renderWithQueryClient(
          <TransferAnalysisForm
            playerId={978838}
            initialValues={{
              ...DEFAULT_TRANSFER_ANALYSIS_VALUES,
            }}
          />,
          "tr",
        );

        expect(
          await screen.findByText(
            "Michael Olise",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getAllByText(
            "Mevcut değil",
          ),
        ).toHaveLength(3);
      },
    );

    it(
      "prefetches analysis data while navigating to results",
      async () => {
        const user =
          userEvent.setup();

        renderWithQueryClient(
          <TransferAnalysisForm
            playerId={978838}
            initialValues={{
              ...DEFAULT_TRANSFER_ANALYSIS_VALUES,
            }}
          />,
        );

        expect(
          await screen.findByText(
            "Michael Olise",
          ),
        ).toBeInTheDocument();

        await user.click(
          screen.getByRole(
            "button",
            {
              name:
                "Find transfer alternatives",
            },
          ),
        );

        await waitFor(() => {
          expect(
            runTransferAnalysisMock,
          ).toHaveBeenCalledTimes(
            1,
          );
        });

        expect(
          runTransferAnalysisMock,
        ).toHaveBeenCalledWith(
          {
            player_id: 978838,
            minimum_minutes: 150,
            minimum_role_confidence: 50,
            maximum_market_value: null,
            neutral_heatmap_score: 70,
          },
          expect.any(AbortSignal),
        );

        expect(
          pushMock,
        ).toHaveBeenCalledWith(
          "/analysis/978838/results?minimum_minutes=150&minimum_role_confidence=50&neutral_heatmap_score=70",
        );
      },
    );
  },
);
