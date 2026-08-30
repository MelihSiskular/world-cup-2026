import type {
  Metadata,
} from "next";
import {
  useTranslations,
} from "next-intl";
import {
  getTranslations,
  setRequestLocale,
} from "next-intl/server";

import {
  PageContainer,
} from "@/components/layout/page-container";
import {
  PageIntro,
} from "@/components/layout/page-intro";
type MethodologyPageProps =
  Readonly<{
    params: Promise<{
      locale: string;
    }>;
  }>;

export async function generateMetadata({
  params,
}: MethodologyPageProps): Promise<Metadata> {
  const { locale } = await params;

  const t = await getTranslations({
    locale,
    namespace: "Methodology",
  });

  return {
    title: t("metadataTitle"),
    description:
      t("metadataDescription"),
  };
}

type SignalKey =
  | "statistical_similarity_pct"
  | "role_fit_pct"
  | "spatial_similarity_pct"
  | "effective_heatmap_score_pct"
  | "player_quality_score"
  | "data_reliability_score"
  | "market_value_advantage_pct"
  | "age_suitability_pct";

type SignalLabels =
  Readonly<Record<SignalKey, string>>;

type ModeDetails =
  Readonly<{
    key:
      | "immediate"
      | "development"
      | "value"
      | "short_term";
    sameRoleBonus: number;
    sameArchetypeBonus: number;
    weights: readonly Readonly<{
      signal: SignalKey;
      weight: number;
    }>[];
  }>;

type ScenarioCopy =
  Readonly<{
    title: string;
    summary: string;
    eligibility: Readonly<
      Record<string, string>
    >;
  }>;

const modes = [
  {
    key: "immediate",
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

function WeightList({
  weights,
  signalLabels,
}: Readonly<{
  weights: ModeDetails["weights"];
  signalLabels: SignalLabels;
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

export default async function MethodologyPage({
  params,
}: MethodologyPageProps) {
  const { locale } = await params;

  setRequestLocale(locale);

  return <MethodologyPageContent />;
}

export function MethodologyPageContent() {
  const t = useTranslations(
    "Methodology",
  );

  const pipelineSteps =
    Object.values(
      t.raw(
        "pipeline.steps",
      ) as Readonly<
        Record<
          string,
          Readonly<{
            number: string;
            title: string;
            description: string;
          }>
        >
      >,
    );

  const evidenceReadingCards =
    Object.values(
      t.raw(
        "evidence.cards",
      ) as Readonly<
        Record<
          string,
          Readonly<{
            label: string;
            title: string;
            description: string;
          }>
        >
      >,
    );

  const roleModelCards =
    Object.values(
      t.raw(
        "roleModel.cards",
      ) as Readonly<
        Record<
          string,
          Readonly<{
            title: string;
            description: string;
          }>
        >
      >,
    );

  const signalCards =
    Object.values(
      t.raw(
        "signals.cards",
      ) as Readonly<
        Record<
          string,
          Readonly<{
            title: string;
            description: string;
            detail: string;
          }>
        >
      >,
    );

  const comparisonEvidenceCards =
    Object.values(
      t.raw(
        "comparisonEvidence.cards",
      ) as Readonly<
        Record<
          string,
          Readonly<{
            title: string;
            description: string;
          }>
        >
      >,
    );

  const scenarioModes =
    t.raw(
      "scenarios.modes",
    ) as Readonly<
      Record<
        ModeDetails["key"],
        ScenarioCopy
      >
    >;

  const scenarioSignalLabels =
    t.raw(
      "scenarios.signalLabels",
    ) as SignalLabels;

  const rankingParagraphs =
    Object.values(
      t.raw(
        "ranking.paragraphs",
      ) as Readonly<
        Record<string, string>
      >,
    );

  const scoreBands =
    Object.values(
      t.raw(
        "scoreBands.bands",
      ) as Readonly<
        Record<
          string,
          Readonly<{
            label: string;
            range: string;
            meaning: string;
          }>
        >
      >,
    );

  const limitationParagraphs =
    Object.values(
      t.raw(
        "limitations.paragraphs",
      ) as Readonly<
        Record<string, string>
      >,
    );

  return (
    <PageContainer className="py-14 sm:py-20">
      <PageIntro
        eyebrow={t("eyebrow")}
        title={t("title")}
        description={t(
          "description",
        )}
      />

      <section className="mt-12 rounded-3xl border border-brand/20 bg-brand-dark p-6 text-white shadow-sm sm:p-8">
        <p className="text-sm font-semibold tracking-[0.14em] text-white/70 uppercase">
          {t("core.eyebrow")}
        </p>

        <p className="mt-4 max-w-4xl text-2xl font-bold leading-tight tracking-[-0.035em] sm:text-3xl">
          {t("core.title")}
        </p>

        <p className="mt-5 max-w-3xl text-sm leading-7 text-white/75">
          {t("core.description")}
        </p>
      </section>

      <section
        aria-labelledby="pipeline-heading"
        className="mt-16"
      >
        <p className="text-sm font-semibold tracking-[0.14em] text-brand uppercase">
          {t("pipeline.eyebrow")}
        </p>

        <h2
          id="pipeline-heading"
          className="mt-3 text-3xl font-bold tracking-[-0.04em]"
        >
          {t("pipeline.title")}
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
          {t("evidence.eyebrow")}
        </p>

        <h2
          id="evidence-reading-heading"
          className="mt-3 text-3xl font-bold tracking-[-0.04em]"
        >
          {t("evidence.title")}
        </h2>

        <p className="mt-4 max-w-3xl text-sm leading-7 text-muted">
          {t("evidence.description")}
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
            {t("roleModel.eyebrow")}
          </p>

          <h2
            id="role-model-heading"
            className="mt-3 text-3xl font-bold tracking-[-0.04em]"
          >
            {t("roleModel.title")}
          </h2>

          <p className="mt-4 max-w-3xl text-sm leading-7 text-muted">
            {t(
              "roleModel.description",
            )}
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
              {t(
                "roleModel.supportingLabel",
              )}:
            </strong>{" "}
            {t(
              "roleModel.supportingDescription",
            )}
          </p>
        </div>
      </section>

      <section
        aria-labelledby="signals-heading"
        className="mt-16"
      >
        <p className="text-sm font-semibold tracking-[0.14em] text-brand uppercase">
          {t("signals.eyebrow")}
        </p>

        <h2
          id="signals-heading"
          className="mt-3 text-3xl font-bold tracking-[-0.04em]"
        >
          {t("signals.title")}
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
                  {signal.description}
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
          {t(
            "comparisonEvidence.eyebrow",
          )}
        </p>

        <h2
          id="comparison-evidence-heading"
          className="mt-3 text-3xl font-bold tracking-[-0.04em]"
        >
          {t(
            "comparisonEvidence.title",
          )}
        </h2>

        <div className="mt-7 grid gap-4 lg:grid-cols-3">
          {comparisonEvidenceCards.map(
            (item) => (
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
            ),
          )}
        </div>

        <p className="mt-4 rounded-2xl border border-brand/20 bg-surface-secondary px-5 py-4 text-sm leading-6 text-brand-dark">
          {t(
            "comparisonEvidence.note",
          )}
        </p>
      </section>

      <section
        aria-labelledby="scenarios-heading"
        className="mt-16"
      >
        <p className="text-sm font-semibold tracking-[0.14em] text-brand uppercase">
          {t("scenarios.eyebrow")}
        </p>

        <h2
          id="scenarios-heading"
          className="mt-3 text-3xl font-bold tracking-[-0.04em]"
        >
          {t("scenarios.title")}
        </h2>

        <p className="mt-4 max-w-3xl text-sm leading-7 text-muted">
          {t("scenarios.description")}
        </p>

        <div className="mt-8 space-y-6">
          {modes.map((mode) => {
            const modeCopy =
              scenarioModes[mode.key];

            return (
              <article
                key={mode.key}
                className="overflow-hidden rounded-3xl border border-border bg-surface shadow-sm"
              >
                <div className="grid lg:grid-cols-[minmax(0,1fr)_22rem]">
                  <div className="p-6 sm:p-8">
                    <h3 className="text-2xl font-bold tracking-[-0.035em]">
                      {modeCopy.title}
                    </h3>

                    <p className="mt-3 max-w-2xl text-sm leading-7 text-muted">
                      {modeCopy.summary}
                    </p>

                    <div className="mt-7">
                      <p className="text-xs font-semibold tracking-[0.12em] text-brand uppercase">
                        {t(
                          "scenarios.eligibility",
                        )}
                      </p>

                      <ul className="mt-4 grid gap-2 sm:grid-cols-2">
                        {Object.values(
                          modeCopy.eligibility,
                        ).map((rule) => (
                          <li
                            key={rule}
                            className="rounded-xl border border-border bg-page px-4 py-3 text-sm font-medium"
                          >
                            {rule}
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div className="mt-7 flex flex-wrap gap-3">
                      <span className="rounded-full bg-surface-secondary px-3 py-2 text-xs font-semibold text-brand-dark">
                        {t(
                          "scenarios.sameFinalRoleBonus",
                          {
                            bonus:
                              mode.sameRoleBonus,
                          },
                        )}
                      </span>

                      <span className="rounded-full bg-surface-secondary px-3 py-2 text-xs font-semibold text-brand-dark">
                        {t(
                          "scenarios.sameArchetypeBonus",
                          {
                            bonus:
                              mode.sameArchetypeBonus,
                          },
                        )}
                      </span>
                    </div>
                  </div>

                  <aside className="border-t border-border bg-surface-secondary p-6 lg:border-t-0 lg:border-l">
                    <p className="text-xs font-semibold tracking-[0.12em] text-brand uppercase">
                      {t(
                        "scenarios.scoreWeights",
                      )}
                    </p>

                    <div className="mt-5">
                      <WeightList
                        weights={
                          mode.weights
                        }
                        signalLabels={
                          scenarioSignalLabels
                        }
                      />
                    </div>
                  </aside>
                </div>
              </article>
            );
          })}
        </div>
      </section>

      <section
        aria-labelledby="ranking-heading"
        className="mt-16 grid gap-6 lg:grid-cols-[minmax(0,1fr)_22rem]"
      >
        <article className="rounded-3xl border border-border bg-surface p-6 shadow-sm sm:p-8">
          <p className="text-sm font-semibold tracking-[0.14em] text-brand uppercase">
            {t("ranking.eyebrow")}
          </p>

          <h2
            id="ranking-heading"
            className="mt-3 text-3xl font-bold tracking-[-0.04em]"
          >
            {t("ranking.title")}
          </h2>

          <div className="mt-7 space-y-5 text-sm leading-7 text-muted">
            {rankingParagraphs.map(
              (paragraph) => (
                <p key={paragraph}>
                  {paragraph}
                </p>
              ),
            )}
          </div>
        </article>

        <aside className="rounded-3xl border border-border bg-surface-secondary p-6">
          <p className="text-sm font-semibold tracking-[0.14em] text-brand uppercase">
            {t(
              "ranking.heatmapFallback.eyebrow",
            )}
          </p>

          <h3 className="mt-3 text-xl font-bold tracking-[-0.025em]">
            {t(
              "ranking.heatmapFallback.title",
            )}
          </h3>

          <p className="mt-4 text-sm leading-7 text-muted">
            {t(
              "ranking.heatmapFallback.description",
            )}
          </p>
        </aside>
      </section>

      <section
        aria-labelledby="score-bands-heading"
        className="mt-16"
      >
        <p className="text-sm font-semibold tracking-[0.14em] text-brand uppercase">
          {t("scoreBands.eyebrow")}
        </p>

        <h2
          id="score-bands-heading"
          className="mt-3 text-3xl font-bold tracking-[-0.04em]"
        >
          {t("scoreBands.title")}
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
          {t("limitations.eyebrow")}
        </p>

        <h2
          id="limitations-heading"
          className="mt-3 text-3xl font-bold tracking-[-0.04em]"
        >
          {t("limitations.title")}
        </h2>

        <div className="mt-6 grid gap-5 text-sm leading-7 text-muted md:grid-cols-2">
          {limitationParagraphs.map(
            (paragraph) => (
              <p key={paragraph}>
                {paragraph}
              </p>
            ),
          )}
        </div>
      </section>

    </PageContainer>
  );
}
