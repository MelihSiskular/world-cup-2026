import {
  expect,
  test,
  type Locator,
  type Page,
} from "@playwright/test";

const TARGET_NAME =
  "AlexandreMaximilianoDeLaFuenteSantosVanDerWesthuizenConstantinopoulos";

const CANDIDATE_NAME =
  "ChristopherBartholomewMontgomeryAlexanderFernandezDeAlbuquerque";

const targetPlayer = {
  player_id: 990001,
  player_name: TARGET_NAME,
  national_team_name: "Synthetic Nation",
  country_name: "Synthetic Nation",
  position: "M",
  age: 24,
  height_cm: 184,
  appearances: 7,
  starts: 6,
  minutes: 620,
  weighted_rating: 7.45,
  market_value: 75_000_000,
  market_value_currency: "EUR",
  archetype: "Creative midfielder",
  spatial_role: "Right half-space creator",
  final_role: "Advanced Playmaker",
  lateral_profile: "Right",
  vertical_profile: "Advanced",
  mobility_profile: "Mobile",
  role_confidence_pct: 82,
  spatial_reliability: 0.75,
  data_reliability_score: 0.8,
  player_quality_score: 84,
  role_reason: "Synthetic regression fixture.",
};

const candidate = {
  player_id: 990002,
  player_name: CANDIDATE_NAME,
  national_team_name: "Candidate Nation",
  country_name: "Candidate Nation",
  position: "M",
  age: 23,
  appearances: 6,
  starts: 5,
  minutes: 540,
  weighted_rating: 7.2,
  market_value: 45_000_000,
  market_value_currency: "EUR",
  archetype: "Wide Creator",
  final_role: "Central Creator",
  role_confidence_pct: 79,
  player_quality_score: 80,

  statistical_similarity_pct: 74.5,
  spatial_similarity_pct: 68.2,
  heatmap_similarity_score_pct: 71.4,
  effective_heatmap_score_pct: 71.4,
  has_heatmap_similarity: true,
  role_fit_pct: 81.2,
  market_value_advantage_pct: 76.5,

  immediate_score: 77.3,
  immediate_rank: 1,
  development_score: 70.2,
  development_rank: 1,
  value_score: 75.4,
  value_rank: 1,
  short_term_score: 73.8,
  short_term_rank: 1,

  recommendation_type: "Strong tactical alternative",
  recommendation_strength: "Strong",
  why_recommended:
    "Synthetic recommendation used to verify extreme player-name wrapping.",
};

const analysisResponse = {
  target: targetPlayer,
  modes: {
    immediate: {
      mode: "immediate",
      recommendations: [candidate],
    },
    development: {
      mode: "development",
      recommendations: [],
    },
    value: {
      mode: "value",
      recommendations: [],
    },
    short_term: {
      mode: "short_term",
      recommendations: [],
    },
  },
};

async function expectNoHorizontalPageOverflow(
  page: Page,
): Promise<void> {
  const dimensions = await page.evaluate(
    () => ({
      scrollWidth:
        document.documentElement.scrollWidth,
      clientWidth:
        document.documentElement.clientWidth,
    }),
  );

  expect(
    dimensions.scrollWidth,
    `Expected no horizontal page overflow: scrollWidth=${dimensions.scrollWidth}, clientWidth=${dimensions.clientWidth}`,
  ).toBeLessThanOrEqual(
    dimensions.clientWidth,
  );
}

async function expectTextFits(
  locator: Locator,
): Promise<void> {
  const dimensions =
    await locator.evaluate(
      (element) => ({
        scrollWidth:
          element.scrollWidth,
        clientWidth:
          element.clientWidth,
      }),
    );

  const roundingTolerancePx = 2;

  expect(
    dimensions.scrollWidth,
    `Expected text to fit its element within ${roundingTolerancePx}px browser-rounding tolerance: scrollWidth=${dimensions.scrollWidth}, clientWidth=${dimensions.clientWidth}`,
  ).toBeLessThanOrEqual(
    dimensions.clientWidth +
      roundingTolerancePx,
  );
}

async function installSyntheticApi(
  page: Page,
): Promise<void> {
  await page.route(
    "**/api/players/search**",
    async (route) => {
      await route.fulfill({
        status: 200,
        contentType:
          "application/json",
        body: JSON.stringify({
          query: "Alexandre",
          count: 1,
          players: [
            {
              player_id:
                targetPlayer.player_id,
              player_name:
                targetPlayer.player_name,
              national_team_name:
                targetPlayer
                  .national_team_name,
              position:
                targetPlayer.position,
              final_role:
                targetPlayer.final_role,
              archetype:
                targetPlayer.archetype,
              market_value:
                targetPlayer.market_value,
              market_value_currency:
                targetPlayer
                  .market_value_currency,
            },
          ],
        }),
      });
    },
  );

  await page.route(
    `**/api/players/${targetPlayer.player_id}`,
    async (route) => {
      await route.fulfill({
        status: 200,
        contentType:
          "application/json",
        body: JSON.stringify(
          targetPlayer,
        ),
      });
    },
  );

  await page.route(
    "**/api/transfer-intelligence/analyze",
    async (route) => {
      await route.fulfill({
        status: 200,
        contentType:
          "application/json",
        body: JSON.stringify(
          analysisResponse,
        ),
      });
    },
  );
}

test.describe(
  "WC26 extreme player-name reliability",
  () => {
    test(
      "keeps extreme target and candidate names contained across the transfer journey",
      async ({ page }) => {
        test.setTimeout(60_000);

        await installSyntheticApi(
          page,
        );

        await page.goto("/players");

        const search =
          page.getByRole(
            "searchbox",
            {
              name:
                "Search player catalogue",
            },
          );

        await search.fill(
          "Alexandre",
        );

        const searchHeading =
          page.getByRole(
            "heading",
            {
              name: TARGET_NAME,
              exact: true,
            },
          );

        await expect(
          searchHeading,
        ).toBeVisible();

        await expectTextFits(
          searchHeading,
        );

        await expectNoHorizontalPageOverflow(
          page,
        );

        await page
          .getByRole("link", {
            name: new RegExp(
              TARGET_NAME,
            ),
          })
          .click();

        await expect(page).toHaveURL(
          `/players/${targetPlayer.player_id}`,
        );

        const profileHeading =
          page.getByRole(
            "heading",
            {
              name: TARGET_NAME,
              exact: true,
            },
          );

        await expect(
          profileHeading,
        ).toBeVisible();

        await expectTextFits(
          profileHeading,
        );

        await expectNoHorizontalPageOverflow(
          page,
        );

        await page
          .getByRole("link", {
            name:
              "Run transfer analysis",
          })
          .click();

        await expect(page).toHaveURL(
          new RegExp(
            `/analysis/${targetPlayer.player_id}`,
          ),
        );

        const analysisHeading =
          page.getByRole(
            "heading",
            {
              name: TARGET_NAME,
              exact: true,
            },
          );

        await expect(
          analysisHeading,
        ).toBeVisible();

        await expectTextFits(
          analysisHeading,
        );

        await expectNoHorizontalPageOverflow(
          page,
        );

        await page
          .getByRole("button", {
            name:
              "Continue to results",
          })
          .click();

        await expect(page).toHaveURL(
          new RegExp(
            `/analysis/${targetPlayer.player_id}/results`,
          ),
        );

        const resultsTargetHeading =
          page.getByRole(
            "heading",
            {
              name: TARGET_NAME,
              exact: true,
            },
          );

        await expect(
          resultsTargetHeading,
        ).toBeVisible();

        await expectTextFits(
          resultsTargetHeading,
        );

        const recommendationHeading =
          page.getByRole(
            "heading",
            {
              name: CANDIDATE_NAME,
              exact: true,
            },
          );

        await expect(
          recommendationHeading,
        ).toBeVisible();

        await expectTextFits(
          recommendationHeading,
        );

        await expectNoHorizontalPageOverflow(
          page,
        );

        await page
          .getByRole("link", {
            name:
              "Compare with target",
          })
          .first()
          .click();

        await expect(page).toHaveURL(
          new RegExp(
            `/compare/${targetPlayer.player_id}/${candidate.player_id}`,
          ),
        );

        const comparisonTarget =
          page.getByRole(
            "heading",
            {
              name: TARGET_NAME,
              exact: true,
            },
          );

        const comparisonCandidate =
          page.getByRole(
            "heading",
            {
              name: CANDIDATE_NAME,
              exact: true,
            },
          );

        await expect(
          comparisonTarget,
        ).toBeVisible();

        await expect(
          comparisonCandidate,
        ).toBeVisible();

        await expectTextFits(
          comparisonTarget,
        );

        await expectTextFits(
          comparisonCandidate,
        );

        await expectNoHorizontalPageOverflow(
          page,
        );
      },
    );
  },
);
