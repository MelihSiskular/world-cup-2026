import AxeBuilder from "@axe-core/playwright";
import {
  expect,
  test,
  type Page,
  type TestInfo,
} from "@playwright/test";

const TARGET_PLAYER_ID =
  978838;

const CANDIDATES = [
  {
    playerId: 789071,
    playerName: "Dani Olmo",
  },
  {
    playerId: 805078,
    playerName:
      "Candidate Without Pair Evidence",
  },
  {
    playerId: 123456,
    playerName: "Florian Wirtz",
  },
] as const;

const COMPARISON_PATH =
  (
    `/compare/multi/${TARGET_PLAYER_ID}`
    + "?candidates=789071%2C805078%2C123456"
  );

const WCAG_TAGS = [
  "wcag2a",
  "wcag2aa",
  "wcag21a",
  "wcag21aa",
];

async function waitForApplicationReady(
  page: Page,
): Promise<void> {
  await page.waitForFunction(
    () =>
      document.documentElement
        .dataset.wc26Hydrated ===
      "true",
  );
}

async function expectNoHorizontalPageOverflow(
  page: Page,
): Promise<void> {
  const dimensions =
    await page.evaluate(
      () => ({
        scrollWidth:
          document.documentElement
            .scrollWidth,
        clientWidth:
          document.documentElement
            .clientWidth,
      }),
    );

  expect(
    dimensions.scrollWidth,
    (
      "Expected no horizontal page overflow: "
      + `scrollWidth=${dimensions.scrollWidth}, `
      + `clientWidth=${dimensions.clientWidth}`
    ),
  ).toBeLessThanOrEqual(
    dimensions.clientWidth,
  );
}

function resolveCandidate(
  requestUrl: string,
) {
  const segments =
    new URL(requestUrl)
      .pathname
      .split("/");

  const candidateId =
    Number(
      segments[
        segments.length - 1
      ],
    );

  const candidate =
    CANDIDATES.find(
      ({ playerId }) =>
        playerId ===
        candidateId,
    );

  if (!candidate) {
    throw new Error(
      `Unexpected candidate ID: ${candidateId}`,
    );
  }

  return candidate;
}

function createRadarPlayer(
  playerId: number,
  playerName: string,
  percentileOffset: number,
) {
  return {
    player_id: playerId,
    player_name: playerName,
    position: "M",
    available: true,
    peer_count: 216,
    dimensions: [
      {
        key: "creativity",
        label: "Creativity",
        raw_score: 4.5,
        percentile:
          95 - percentileOffset,
        peer_count: 216,
      },
      {
        key: "progression",
        label: "Progression",
        raw_score: 3.8,
        percentile:
          88 - percentileOffset,
        peer_count: 216,
      },
      {
        key: "ball_security",
        label: "Ball Security",
        raw_score: 3.2,
        percentile:
          81 - percentileOffset,
        peer_count: 216,
      },
    ],
  };
}

function createHeatmapPlayer(
  playerId: number,
  playerName: string,
  offset: number,
) {
  return {
    player_id: playerId,
    player_name: playerName,
    available: true,
    grid_width: 2,
    grid_height: 2,
    grid: [
      [
        0.1 + offset,
        0.4 + offset,
      ],
      [
        0.7 - offset,
        1 - offset,
      ],
    ],
    matches_with_heatmap: 6,
    heatmap_point_count: 509,
  };
}

async function installSyntheticApi(
  page: Page,
): Promise<void> {
  await page.route(
    (
      "**/api/transfer-intelligence/"
      + "multi-comparison/978838**"
    ),
    async (route) => {
      await route.fulfill({
        status: 200,
        contentType:
          "application/json",
        body: JSON.stringify({
          target: {
            player_id:
              TARGET_PLAYER_ID,
            player_name:
              "Michael Olise",
            national_team_name:
              "France",
            position: "M",
            age: 24,
            minutes: 540,
            market_value:
              100_000_000,
            market_value_currency:
              "EUR",
            final_role:
              "Advanced Playmaker",
            player_quality_score:
              91,
            data_reliability_score:
              0.92,
          },
          candidates: [
            {
              player: {
                player_id: 789071,
                player_name:
                  "Dani Olmo",
                national_team_name:
                  "Spain",
                position: "M",
                age: 28,
                minutes: 480,
                market_value:
                  60_000_000,
                market_value_currency:
                  "EUR",
                final_role:
                  "Advanced Playmaker",
                player_quality_score:
                  87,
                data_reliability_score:
                  0.9,
              },
              evidence: {
                statistical_similarity_pct:
                  91,
                spatial_similarity_pct:
                  84,
                heatmap_similarity_score_pct:
                  88,
                role_fit_pct: 86,
                market_value_advantage_pct:
                  60,
              },
            },
            {
              player: {
                player_id: 805078,
                player_name:
                  "Candidate Without Pair Evidence",
                national_team_name:
                  "Germany",
                position: "M",
                age: 23,
                minutes: 310,
                market_value:
                  35_000_000,
                market_value_currency:
                  "EUR",
                final_role:
                  "Wide Creator",
                player_quality_score:
                  79,
                data_reliability_score:
                  0.78,
              },
              evidence: {
                statistical_similarity_pct:
                  null,
                spatial_similarity_pct:
                  72,
                heatmap_similarity_score_pct:
                  null,
                role_fit_pct: 78,
                market_value_advantage_pct:
                  70,
              },
            },
            {
              player: {
                player_id: 123456,
                player_name:
                  "Florian Wirtz",
                national_team_name:
                  "Germany",
                position: "M",
                age: 23,
                minutes: 510,
                market_value:
                  120_000_000,
                market_value_currency:
                  "EUR",
                final_role:
                  "Advanced Playmaker",
                player_quality_score:
                  93,
                data_reliability_score:
                  0.94,
              },
              evidence: {
                statistical_similarity_pct:
                  89,
                spatial_similarity_pct:
                  87,
                heatmap_similarity_score_pct:
                  90,
                role_fit_pct: 92,
                market_value_advantage_pct:
                  40,
              },
            },
          ],
        }),
      });
    },
  );

  await page.route(
    (
      "**/api/transfer-intelligence/"
      + "radar-comparison/978838/*"
    ),
    async (route) => {
      const candidate =
        resolveCandidate(
          route.request().url(),
        );

      await route.fulfill({
        status: 200,
        contentType:
          "application/json",
        body: JSON.stringify({
          target:
            createRadarPlayer(
              TARGET_PLAYER_ID,
              "Michael Olise",
              0,
            ),
          candidate:
            createRadarPlayer(
              candidate.playerId,
              candidate.playerName,
              10,
            ),
          comparison: {
            same_position: true,
            overlay_available:
              true,
            reason: null,
          },
        }),
      });
    },
  );

  await page.route(
    (
      "**/api/transfer-intelligence/"
      + "heatmap-comparison/978838/*"
    ),
    async (route) => {
      const candidate =
        resolveCandidate(
          route.request().url(),
        );

      const evidenceAvailable =
        candidate.playerId !==
        805078;

      await route.fulfill({
        status: 200,
        contentType:
          "application/json",
        body: JSON.stringify({
          target:
            createHeatmapPlayer(
              TARGET_PLAYER_ID,
              "Michael Olise",
              0,
            ),
          candidate:
            createHeatmapPlayer(
              candidate.playerId,
              candidate.playerName,
              0.05,
            ),
          similarity:
            evidenceAvailable
              ? {
                  available: true,
                  heatmap_similarity_score_pct:
                    88,
                  heatmap_cosine_similarity_pct:
                    90,
                  occupation_overlap_pct:
                    82,
                  peak_zone_similarity_pct:
                    79,
                  peak_zone_distance:
                    8.5,
                  entropy_similarity_pct:
                    84,
                }
              : {
                  available: false,
                  heatmap_similarity_score_pct:
                    null,
                  heatmap_cosine_similarity_pct:
                    null,
                  occupation_overlap_pct:
                    null,
                  peak_zone_similarity_pct:
                    null,
                  peak_zone_distance:
                    null,
                  entropy_similarity_pct:
                    null,
                },
        }),
      });
    },
  );
}

async function openComparison(
  page: Page,
): Promise<void> {
  await installSyntheticApi(
    page,
  );

  await page.goto(
    COMPARISON_PATH,
  );

  await waitForApplicationReady(
    page,
  );

  await expect(
    page.getByRole(
      "heading",
      {
        name:
          "Multi-player comparison",
        exact: true,
      },
    ),
  ).toBeVisible();
}

async function expectNoWcagViolations(
  page: Page,
  testInfo: TestInfo,
): Promise<void> {
  const results =
    await new AxeBuilder({
      page,
    })
      .withTags(
        WCAG_TAGS,
      )
      .analyze();

  await testInfo.attach(
    "multi-player-comparison-axe-violations",
    {
      body: JSON.stringify(
        results.violations,
        null,
        2,
      ),
      contentType:
        "application/json",
    },
  );

  expect(
    results.violations,
  ).toEqual([]);
}

test.describe(
  "multi-player comparison",
  () => {
    test(
      "restores the canonical overview and changes focused pair evidence",
      async ({ page }) => {
        test.setTimeout(
          60_000,
        );

        await openComparison(
          page,
        );

        const table =
          page.getByRole(
            "table",
            {
              name:
                "Target-relative comparison overview",
            },
          );

        await expect(
          table,
        ).toBeVisible();

        const headers =
          table.getByRole(
            "columnheader",
          );

        await expect(
          headers,
        ).toHaveCount(5);

        await expect(
          headers.nth(1),
        ).toContainText(
          "Michael Olise",
        );

        await expect(
          headers.nth(2),
        ).toContainText(
          "Dani Olmo",
        );

        await expect(
          headers.nth(3),
        ).toContainText(
          "Candidate Without Pair Evidence",
        );

        await expect(
          headers.nth(4),
        ).toContainText(
          "Florian Wirtz",
        );

        await expect(
          table.getByRole(
            "row",
            {
              name:
                /Statistical similarity/i,
            },
          ),
        ).toContainText(
          "Unavailable",
        );

        const initialCandidate =
          page.getByRole(
            "button",
            {
              name: "Dani Olmo",
            },
          );

        await expect(
          initialCandidate,
        ).toHaveAttribute(
          "aria-pressed",
          "true",
        );

        await expect(
          page.getByRole(
            "img",
            {
              name:
                "Playing style radar comparison for Michael Olise and Dani Olmo",
            },
          ),
        ).toBeVisible();

        const missingEvidenceCandidate =
          page.getByRole(
            "button",
            {
              name:
                "Candidate Without Pair Evidence",
            },
          );

        await missingEvidenceCandidate
          .click();

        await expect(
          missingEvidenceCandidate,
        ).toHaveAttribute(
          "aria-pressed",
          "true",
        );

        await expect(
          page.getByRole(
            "img",
            {
              name:
                "Playing style radar comparison for Michael Olise and Candidate Without Pair Evidence",
            },
          ),
        ).toBeVisible();

        await expect(
          page.getByText(
            "Pair evidence unavailable",
            {
              exact: true,
            },
          ),
        ).toBeVisible();

        const parameters =
          new URL(
            page.url(),
          ).searchParams;

        expect(
          parameters.get(
            "candidates",
          ),
        ).toBe(
          "789071,805078,123456",
        );

        await expectNoHorizontalPageOverflow(
          page,
        );
      },
    );

    test(
      "supports keyboard focus selection and remains WCAG compliant",
      async ({
        page,
      }, testInfo) => {
        test.setTimeout(
          60_000,
        );

        await openComparison(
          page,
        );

        const candidate =
          page.getByRole(
            "button",
            {
              name:
                "Florian Wirtz",
            },
          );

        await candidate.focus();

        await expect(
          candidate,
        ).toBeFocused();

        await page.keyboard.press(
          "Enter",
        );

        await expect(
          candidate,
        ).toHaveAttribute(
          "aria-pressed",
          "true",
        );

        await expect(
          page.getByRole(
            "img",
            {
              name:
                "Playing style radar comparison for Michael Olise and Florian Wirtz",
            },
          ),
        ).toBeVisible();

        await expect(
          page.getByRole(
            "status",
            {
              name:
                "Loading focused radar comparison",
            },
          ),
        ).toHaveCount(0);

        await expect(
          page.getByRole(
            "status",
            {
              name:
                "Loading focused heatmap comparison",
            },
          ),
        ).toHaveCount(0);

        await expectNoHorizontalPageOverflow(
          page,
        );

        await expectNoWcagViolations(
          page,
          testInfo,
        );
      },
    );
  },
);
