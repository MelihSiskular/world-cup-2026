import type {
  Metadata,
} from "next";

import {
  PageContainer,
} from "@/components/layout/page-container";
import {
  PageIntro,
} from "@/components/layout/page-intro";
export const metadata: Metadata = {
  title: "Methodology",
  description:
    "How WC26 Transfer Intelligence interprets player evidence and ranks replacement candidates.",
};

const pipelineSteps = [
  {
    number: "01",
    title: "Select the target",
    description:
      "The analysis starts from one stable player identity and its tournament, role, spatial and market profile.",
  },
  {
    number: "02",
    title: "Build the candidate pool",
    description:
      "Candidates are filtered by playing time, role confidence, optional budget and the availability of statistical similarity evidence.",
  },
  {
    number: "03",
    title: "Calculate decision signals",
    description:
      "The engine adds tactical role fit, spatial similarity, heatmap evidence, market advantage and age suitability.",
  },
  {
    number: "04",
    title: "Apply scenario eligibility",
    description:
      "Each recruitment scenario applies its own minimum similarity, quality, reliability, role and age requirements.",
  },
  {
    number: "05",
    title: "Score and explain",
    description:
      "Eligible candidates receive a scenario-specific score, rank, recommendation type and human-readable evidence.",
  },
] as const;

const evidenceReadingCards = [
  {
    label: "Output",
    title: "Raw and per-90 values",
    description:
      "The reported output is the player's measured tournament value. Per-90 values normalize volume for playing time; they are not percentile scores.",
  },
  {
    label: "Position context",
    title: "Same-position percentile",
    description:
      "Percentiles compare the player with eligible peers in the same position group. A higher percentile means stronger expression of that metric.",
  },
  {
    label: "Peer sample",
    title: "What n represents",
    description:
      "The n value is the number of eligible same-position peers. Peer cohorts require at least 180 tournament minutes and 10 usable players.",
  },
  {
    label: "Evidence state",
    title: "Missing is not zero",
    description:
      "Unavailable evidence remains missing. A measured zero is preserved as a real value and is never replaced with a neutral or invented result.",
  },
] as const;

const roleModelCards = [
  {
    title: "Statistical archetype",
    description:
      "Describes how the player's tournament actions and performance metrics cluster statistically.",
  },
  {
    title: "Spatial role",
    description:
      "Describes where the player operated using average location, lane occupation, vertical zone and spatial spread.",
  },
  {
    title: "Final role",
    description:
      "Combines the statistical archetype with the measured spatial profile to produce the tactical role used by the recommendation engine.",
  },
] as const;

const comparisonEvidenceCards = [
  {
    title: "Measured heatmap",
    description:
      "The pitch shows observed tournament occupation. Heatmap density and average position are independent evidence sources displayed on the same coordinate system.",
  },
  {
    title: "Heatmap comparison",
    description:
      "Cosine similarity, occupation overlap, lateral and vertical structure, peak zones and entropy describe different aspects of spatial resemblance.",
  },
  {
    title: "Radar comparison",
    description:
      "Radar dimensions use position-relative percentiles. Same-position players can share one scale; cross-position players retain separate positional contexts.",
  },
] as const;

const signalCards = [
  {
    title:
      "Statistical similarity",
    description:
      "A position-relevant comparison from the precomputed player similarity model. Candidates without a measured statistical similarity are excluded.",
    detail:
      "This signal describes similarity, not whether the candidate is automatically the better player.",
  },
  {
    title: "Role fit",
    description:
      "Role fit awards 45 points for the same final role, 25 for the same archetype, 12 for the same spatial role, then 7, 6 and 5 points for matching lateral, vertical and mobility profiles.",
    detail:
      "The raw match score is moderated by the candidate's role-confidence level.",
  },
  {
    title:
      "Spatial similarity",
    description:
      "Average position, spatial spread, third occupation and lane occupation are standardized before calculating distance from the target profile.",
    detail:
      "When fewer than three usable spatial fields exist, the engine uses a neutral score of 50.",
  },
  {
    title:
      "Heatmap similarity",
    description:
      "Measured heatmap evidence includes cosine similarity, shared-zone occupation, lateral and vertical structure, peak zones and entropy.",
    detail:
      "Missing heatmap evidence remains explicitly missing; only the decision score receives the configured neutral fallback.",
  },
  {
    title:
      "Market advantage",
    description:
      "The candidate's market value is evaluated relative to the target. Less expensive candidates generally receive a stronger financial-advantage signal.",
    detail:
      "When the target has no usable market value, the candidate pool's market-value percentile is used instead.",
  },
  {
    title:
      "Age suitability",
    description:
      "Age suitability combines a general age curve with an adjustment based on the candidate's age difference from the target.",
    detail:
      "Its importance changes substantially by recruitment scenario.",
  },
  {
    title:
      "Player quality",
    description:
      "A tournament-derived quality signal helps prevent similarity alone from promoting candidates without sufficient performance level.",
    detail:
      "Minimum quality requirements vary between immediate, development, value and short-term analysis.",
  },
  {
    title:
      "Data reliability",
    description:
      "Reliability represents how strongly the available tournament sample supports the player's calculated profile.",
    detail:
      "Higher-risk scenarios can accept lower reliability, while immediate and short-term recommendations demand stronger evidence.",
  },
] as const;

const signalLabels = {
  statistical_similarity_pct:
    "Statistical similarity",
  role_fit_pct: "Role fit",
  spatial_similarity_pct:
    "Spatial similarity",
  effective_heatmap_score_pct:
    "Heatmap score",
  player_quality_score:
    "Player quality",
  data_reliability_score:
    "Data reliability",
  market_value_advantage_pct:
    "Market advantage",
  age_suitability_pct:
    "Age suitability",
} as const;

type SignalKey =
  keyof typeof signalLabels;

type ModeDetails =
  Readonly<{
    key: string;
    title: string;
    summary: string;
    eligibility:
      readonly string[];
    sameRoleBonus: number;
    sameArchetypeBonus: number;
    weights: readonly Readonly<{
      signal: SignalKey;
      weight: number;
    }>[];
  }>;

const modes = [
  {
    key: "immediate",
    title: "Immediate impact",
    summary:
      "Prioritizes tactical continuity, current quality and reliable evidence for first-team contribution now.",
    eligibility: [
      "Statistical similarity ≥ 30",
      "Role fit ≥ 35",
      "Player quality ≥ 55",
      "Data reliability ≥ 55",
      "Maximum age: 31",
    ],
    sameRoleBonus: 6,
    sameArchetypeBonus: 2,
    weights: [
      {
        signal:
          "statistical_similarity_pct",
        weight: 20,
      },
      {
        signal: "role_fit_pct",
        weight: 23,
      },
      {
        signal:
          "spatial_similarity_pct",
        weight: 12,
      },
      {
        signal:
          "effective_heatmap_score_pct",
        weight: 12,
      },
      {
        signal:
          "player_quality_score",
        weight: 15,
      },
      {
        signal:
          "data_reliability_score",
        weight: 10,
      },
      {
        signal:
          "market_value_advantage_pct",
        weight: 4,
      },
      {
        signal:
          "age_suitability_pct",
        weight: 4,
      },
    ],
  },
  {
    key: "development",
    title:
      "Development investment",
    summary:
      "Accepts more tactical adaptation and places the strongest emphasis on age upside and future market potential.",
    eligibility: [
      "Statistical similarity ≥ 25",
      "Role fit ≥ 5",
      "Player quality ≥ 30",
      "Data reliability ≥ 35",
      "Maximum age: 23",
    ],
    sameRoleBonus: 4,
    sameArchetypeBonus: 4,
    weights: [
      {
        signal:
          "statistical_similarity_pct",
        weight: 19,
      },
      {
        signal: "role_fit_pct",
        weight: 11,
      },
      {
        signal:
          "spatial_similarity_pct",
        weight: 8,
      },
      {
        signal:
          "effective_heatmap_score_pct",
        weight: 10,
      },
      {
        signal:
          "player_quality_score",
        weight: 9,
      },
      {
        signal:
          "data_reliability_score",
        weight: 5,
      },
      {
        signal:
          "market_value_advantage_pct",
        weight: 14,
      },
      {
        signal:
          "age_suitability_pct",
        weight: 24,
      },
    ],
  },
  {
    key: "value",
    title:
      "Market value opportunity",
    summary:
      "Balances tactical suitability with financial efficiency and places the largest weight on price advantage.",
    eligibility: [
      "Statistical similarity ≥ 25",
      "Role fit ≥ 25",
      "Player quality ≥ 35",
      "Data reliability ≥ 35",
      "No scenario age limit",
    ],
    sameRoleBonus: 7,
    sameArchetypeBonus: 2,
    weights: [
      {
        signal:
          "statistical_similarity_pct",
        weight: 16,
      },
      {
        signal: "role_fit_pct",
        weight: 18,
      },
      {
        signal:
          "spatial_similarity_pct",
        weight: 8,
      },
      {
        signal:
          "effective_heatmap_score_pct",
        weight: 10,
      },
      {
        signal:
          "player_quality_score",
        weight: 9,
      },
      {
        signal:
          "data_reliability_score",
        weight: 8,
      },
      {
        signal:
          "market_value_advantage_pct",
        weight: 26,
      },
      {
        signal:
          "age_suitability_pct",
        weight: 5,
      },
    ],
  },
  {
    key: "short_term",
    title:
      "Short-term solution",
    summary:
      "Targets experienced candidates and emphasizes role continuity, tournament quality and data reliability.",
    eligibility: [
      "Statistical similarity ≥ 20",
      "Role fit ≥ 30",
      "Player quality ≥ 45",
      "Data reliability ≥ 50",
      "Minimum age: 29",
    ],
    sameRoleBonus: 8,
    sameArchetypeBonus: 3,
    weights: [
      {
        signal:
          "statistical_similarity_pct",
        weight: 16,
      },
      {
        signal: "role_fit_pct",
        weight: 22,
      },
      {
        signal:
          "spatial_similarity_pct",
        weight: 8,
      },
      {
        signal:
          "effective_heatmap_score_pct",
        weight: 10,
      },
      {
        signal:
          "player_quality_score",
        weight: 14,
      },
      {
        signal:
          "data_reliability_score",
        weight: 19,
      },
      {
        signal:
          "market_value_advantage_pct",
        weight: 11,
      },
      {
        signal:
          "age_suitability_pct",
        weight: 0,
      },
    ],
  },
] as const satisfies readonly ModeDetails[];

const scoreBands = [
  {
    label: "Elite",
    range: "80–100",
    meaning:
      "Exceptionally strong scenario fit across the weighted decision signals.",
  },
  {
    label: "Strong",
    range: "72–79.99",
    meaning:
      "Convincing candidate with substantial evidence for the selected scenario.",
  },
  {
    label: "Good",
    range: "64–71.99",
    meaning:
      "Useful recommendation with a credible, but less complete, overall case.",
  },
  {
    label: "Moderate",
    range: "56–63.99",
    meaning:
      "Potentially relevant candidate requiring closer contextual scouting.",
  },
  {
    label: "Low",
    range: "Below 56",
    meaning:
      "Eligible for the scenario, but supported by comparatively weaker combined evidence.",
  },
] as const;

function WeightList({
  weights,
}: Readonly<{
  weights: ModeDetails["weights"];
}>) {
  return (
    <div className="space-y-3">
      {weights.map(
        ({
          signal,
          weight,
        }) => (
          <div key={signal}>
            <div className="flex items-center justify-between gap-4 text-xs">
              <span className="font-medium text-muted">
                {
                  signalLabels[
                    signal
                  ]
                }
              </span>

              <span className="font-bold text-brand-dark">
                {weight}%
              </span>
            </div>

            <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-border">
              <div
                className="h-full rounded-full bg-brand"
                style={{
                  width: `${weight}%`,
                }}
              />
            </div>
          </div>
        ),
      )}
    </div>
  );
}

export default function MethodologyPage() {
  return (
    <PageContainer className="py-14 sm:py-20">
      <PageIntro
        eyebrow="Methodology"
        title="Similarity is evidence, not the final decision"
        description="WC26 Transfer Intelligence combines statistical, tactical, spatial, heatmap, quality, reliability, age and market evidence to rank replacements for a specific recruitment objective."
      />

      <section className="mt-12 rounded-3xl border border-brand/20 bg-brand-dark p-6 text-white shadow-sm sm:p-8">
        <p className="text-sm font-semibold tracking-[0.14em] text-white/70 uppercase">
          Core principle
        </p>

        <p className="mt-4 max-w-4xl text-2xl font-bold leading-tight tracking-[-0.035em] sm:text-3xl">
          The objective is not to find the
          most similar player. It is to find
          the most suitable replacement for
          the selected recruitment context.
        </p>

        <p className="mt-5 max-w-3xl text-sm leading-7 text-white/75">
          Statistical similarity describes
          profile resemblance. The final
          recommendation also considers
          tactical fit, occupied areas,
          tournament quality, evidence
          reliability, age and market value.
        </p>
      </section>

      <section
        aria-labelledby="pipeline-heading"
        className="mt-16"
      >
        <p className="text-sm font-semibold tracking-[0.14em] text-brand uppercase">
          Decision pipeline
        </p>

        <h2
          id="pipeline-heading"
          className="mt-3 text-3xl font-bold tracking-[-0.04em]"
        >
          From target player to ranked candidates
        </h2>

        <div className="mt-7 grid gap-4 md:grid-cols-2 xl:grid-cols-5">
          {pipelineSteps.map(
            (step) => (
              <article
                key={step.number}
                className="rounded-2xl border border-border bg-surface p-5 shadow-sm"
              >
                <span className="text-sm font-bold text-brand">
                  {step.number}
                </span>

                <h3 className="mt-5 text-lg font-bold tracking-[-0.025em]">
                  {step.title}
                </h3>

                <p className="mt-3 text-sm leading-6 text-muted">
                  {
                    step.description
                  }
                </p>
              </article>
            ),
          )}
        </div>
      </section>

      <section
        aria-labelledby="evidence-reading-heading"
        className="mt-16"
      >
        <p className="text-sm font-semibold tracking-[0.14em] text-brand uppercase">
          Evidence interpretation
        </p>

        <h2
          id="evidence-reading-heading"
          className="mt-3 text-3xl font-bold tracking-[-0.04em]"
        >
          How to read player evidence
        </h2>

        <p className="mt-4 max-w-3xl text-sm leading-7 text-muted">
          Player values, percentiles and sample sizes answer different
          questions. They should be read together without treating missing
          evidence as measured performance.
        </p>

        <div className="mt-7 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {evidenceReadingCards.map((item) => (
            <article
              key={item.title}
              className="rounded-2xl border border-border bg-surface p-5 shadow-sm"
            >
              <p className="text-xs font-semibold tracking-[0.12em] text-brand uppercase">
                {item.label}
              </p>

              <h3 className="mt-3 text-lg font-bold tracking-[-0.025em]">
                {item.title}
              </h3>

              <p className="mt-3 text-sm leading-6 text-muted">
                {item.description}
              </p>
            </article>
          ))}
        </div>
      </section>

      <section
        aria-labelledby="role-model-heading"
        className="mt-16 overflow-hidden rounded-3xl border border-border bg-surface shadow-sm"
      >
        <div className="p-6 sm:p-8">
          <p className="text-sm font-semibold tracking-[0.14em] text-brand uppercase">
            Role model
          </p>

          <h2
            id="role-model-heading"
            className="mt-3 text-3xl font-bold tracking-[-0.04em]"
          >
            From performance profile to tactical role
          </h2>

          <p className="mt-4 max-w-3xl text-sm leading-7 text-muted">
            The platform keeps statistical style, measured occupation and the
            final tactical interpretation distinct so each layer can be
            inspected independently.
          </p>

          <div className="mt-7 grid gap-4 lg:grid-cols-3">
            {roleModelCards.map((item, index) => (
              <article
                key={item.title}
                className="rounded-2xl border border-border bg-page p-5"
              >
                <span className="text-xs font-bold text-brand">
                  0{index + 1}
                </span>

                <h3 className="mt-4 text-lg font-bold tracking-[-0.025em]">
                  {item.title}
                </h3>

                <p className="mt-3 text-sm leading-6 text-muted">
                  {item.description}
                </p>
              </article>
            ))}
          </div>
        </div>

        <div className="border-t border-border bg-surface-secondary px-6 py-5 sm:px-8">
          <p className="text-sm leading-6 text-muted">
            <strong className="font-semibold text-brand-dark">
              Supporting role evidence:
            </strong>{" "}
            lateral profile, vertical profile and mobility profile describe how
            the player occupied and moved through the pitch. Role confidence
            expresses how strongly the available evidence supports the assigned
            role.
          </p>
        </div>
      </section>

      <section
        aria-labelledby="signals-heading"
        className="mt-16"
      >
        <p className="text-sm font-semibold tracking-[0.14em] text-brand uppercase">
          Decision signals
        </p>

        <h2
          id="signals-heading"
          className="mt-3 text-3xl font-bold tracking-[-0.04em]"
        >
          What the engine evaluates
        </h2>

        <div className="mt-7 grid gap-4 md:grid-cols-2">
          {signalCards.map(
            (signal) => (
              <article
                key={signal.title}
                className="rounded-2xl border border-border bg-surface p-6 shadow-sm"
              >
                <h3 className="text-xl font-bold tracking-[-0.025em]">
                  {signal.title}
                </h3>

                <p className="mt-3 text-sm leading-6 text-muted">
                  {
                    signal.description
                  }
                </p>

                <p className="mt-4 rounded-xl bg-surface-secondary p-4 text-xs leading-5 text-brand-dark">
                  {signal.detail}
                </p>
              </article>
            ),
          )}
        </div>
      </section>

      <section
        aria-labelledby="comparison-evidence-heading"
        className="mt-16"
      >
        <p className="text-sm font-semibold tracking-[0.14em] text-brand uppercase">
          Spatial and comparison evidence
        </p>

        <h2
          id="comparison-evidence-heading"
          className="mt-3 text-3xl font-bold tracking-[-0.04em]"
        >
          Different views answer different questions
        </h2>

        <div className="mt-7 grid gap-4 lg:grid-cols-3">
          {comparisonEvidenceCards.map((item) => (
            <article
              key={item.title}
              className="rounded-2xl border border-border bg-surface p-6 shadow-sm"
            >
              <h3 className="text-xl font-bold tracking-[-0.025em]">
                {item.title}
              </h3>

              <p className="mt-3 text-sm leading-7 text-muted">
                {item.description}
              </p>
            </article>
          ))}
        </div>

        <p className="mt-4 rounded-2xl border border-brand/20 bg-surface-secondary px-5 py-4 text-sm leading-6 text-brand-dark">
          Statistical similarity, spatial similarity and heatmap similarity are
          complementary signals. None of them replaces the others or proves
          that one player is superior.
        </p>
      </section>

      <section
        aria-labelledby="scenarios-heading"
        className="mt-16"
      >
        <p className="text-sm font-semibold tracking-[0.14em] text-brand uppercase">
          Recruitment scenarios
        </p>

        <h2
          id="scenarios-heading"
          className="mt-3 text-3xl font-bold tracking-[-0.04em]"
        >
          One candidate pool, four different decisions
        </h2>

        <p className="mt-4 max-w-3xl text-sm leading-7 text-muted">
          Every scenario filters candidates
          using its own eligibility rules and
          then applies a different weighting
          model. The weights below represent
          the current engine configuration.
        </p>

        <div className="mt-8 space-y-6">
          {modes.map((mode) => (
            <article
              key={mode.key}
              className="overflow-hidden rounded-3xl border border-border bg-surface shadow-sm"
            >
              <div className="grid lg:grid-cols-[minmax(0,1fr)_22rem]">
                <div className="p-6 sm:p-8">
                  <h3 className="text-2xl font-bold tracking-[-0.035em]">
                    {mode.title}
                  </h3>

                  <p className="mt-3 max-w-2xl text-sm leading-7 text-muted">
                    {mode.summary}
                  </p>

                  <div className="mt-7">
                    <p className="text-xs font-semibold tracking-[0.12em] text-brand uppercase">
                      Eligibility
                    </p>

                    <ul className="mt-4 grid gap-2 sm:grid-cols-2">
                      {mode.eligibility.map(
                        (rule) => (
                          <li
                            key={rule}
                            className="rounded-xl border border-border bg-page px-4 py-3 text-sm font-medium"
                          >
                            {rule}
                          </li>
                        ),
                      )}
                    </ul>
                  </div>

                  <div className="mt-7 flex flex-wrap gap-3">
                    <span className="rounded-full bg-surface-secondary px-3 py-2 text-xs font-semibold text-brand-dark">
                      Same final role bonus: +
                      {mode.sameRoleBonus}
                    </span>

                    <span className="rounded-full bg-surface-secondary px-3 py-2 text-xs font-semibold text-brand-dark">
                      Same archetype bonus: +
                      {
                        mode.sameArchetypeBonus
                      }
                    </span>
                  </div>
                </div>

                <aside className="border-t border-border bg-surface-secondary p-6 lg:border-t-0 lg:border-l">
                  <p className="text-xs font-semibold tracking-[0.12em] text-brand uppercase">
                    Score weights
                  </p>

                  <div className="mt-5">
                    <WeightList
                      weights={
                        mode.weights
                      }
                    />
                  </div>
                </aside>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section
        aria-labelledby="ranking-heading"
        className="mt-16 grid gap-6 lg:grid-cols-[minmax(0,1fr)_22rem]"
      >
        <article className="rounded-3xl border border-border bg-surface p-6 shadow-sm sm:p-8">
          <p className="text-sm font-semibold tracking-[0.14em] text-brand uppercase">
            Ranking logic
          </p>

          <h2
            id="ranking-heading"
            className="mt-3 text-3xl font-bold tracking-[-0.04em]"
          >
            How score, rank and explanation are produced
          </h2>

          <div className="mt-7 space-y-5 text-sm leading-7 text-muted">
            <p>
              The engine first calculates a
              weighted scenario score. A
              matching final role and
              statistical archetype can add
              scenario-specific bonuses. The
              result is then restricted to
              the 0–100 range.
            </p>

            <p>
              Candidates are ordered first
              by scenario score. Ties and
              close results are resolved
              using role fit, effective
              heatmap score, statistical
              similarity and player quality,
              in that order.
            </p>

            <p>
              The explanation engine ranks
              available evidence and selects
              up to four distinct evidence
              groups. This prevents one type
              of evidence from dominating
              the complete explanation.
            </p>
          </div>
        </article>

        <aside className="rounded-3xl border border-border bg-surface-secondary p-6">
          <p className="text-sm font-semibold tracking-[0.14em] text-brand uppercase">
            Heatmap fallback
          </p>

          <h3 className="mt-3 text-xl font-bold tracking-[-0.025em]">
            Neutral is not measured similarity
          </h3>

          <p className="mt-4 text-sm leading-7 text-muted">
            When direct heatmap evidence is
            unavailable, the measured
            heatmap fields remain missing.
            The configurable neutral score
            is used only inside the weighted
            decision model.
          </p>
        </aside>
      </section>

      <section
        aria-labelledby="score-bands-heading"
        className="mt-16"
      >
        <p className="text-sm font-semibold tracking-[0.14em] text-brand uppercase">
          Score interpretation
        </p>

        <h2
          id="score-bands-heading"
          className="mt-3 text-3xl font-bold tracking-[-0.04em]"
        >
          Recommendation strength bands
        </h2>

        <div className="mt-7 grid gap-4 md:grid-cols-2 xl:grid-cols-5">
          {scoreBands.map(
            (band) => (
              <article
                key={band.label}
                className="rounded-2xl border border-border bg-surface p-5 shadow-sm"
              >
                <div className="flex items-center justify-between gap-3">
                  <h3 className="font-bold">
                    {band.label}
                  </h3>

                  <span className="rounded-full bg-surface-secondary px-2.5 py-1 text-xs font-semibold text-brand-dark">
                    {band.range}
                  </span>
                </div>

                <p className="mt-4 text-xs leading-5 text-muted">
                  {band.meaning}
                </p>
              </article>
            ),
          )}
        </div>
      </section>

      <section
        aria-labelledby="limitations-heading"
        className="mt-16 rounded-3xl border border-warning/25 bg-warning/10 p-6 sm:p-8"
      >
        <p className="text-sm font-semibold tracking-[0.14em] text-warning uppercase">
          Responsible use
        </p>

        <h2
          id="limitations-heading"
          className="mt-3 text-3xl font-bold tracking-[-0.04em]"
        >
          What the analysis does not prove
        </h2>

        <div className="mt-6 grid gap-5 text-sm leading-7 text-muted md:grid-cols-2">
          <p>
            Tournament data represents a
            limited competitive sample. A
            strong tournament profile does
            not guarantee the same output
            across a full domestic season,
            another tactical system or a
            different physical environment.
          </p>

          <p>
            Market values are contextual
            estimates rather than transfer
            fees. Contract length, wages,
            registration rules, injury
            history, personality and club
            strategy are outside the current
            scoring model.
          </p>

          <p>
            Similarity is not superiority.
            A candidate can resemble the
            target while being less
            productive, less reliable or
            unsuitable for the intended
            recruitment timescale.
          </p>

          <p>
            The platform is a
            decision-support system. Final
            recruitment decisions should
            combine this evidence with video,
            live scouting, medical review and
            broader club context.
          </p>
        </div>
      </section>

    </PageContainer>
  );
}
