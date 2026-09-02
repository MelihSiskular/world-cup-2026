import { render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";

import englishMessages from "../../../messages/en.json";
import turkishMessages from "../../../messages/tr.json";
import { describe, expect, it } from "vitest";

import { RecommendationExplainability } from "@/components/transfer-intelligence/recommendation-explainability";
import type { TransferRecommendationResponse } from "@/lib/api/types";

type Explainability = TransferRecommendationResponse["explainability"];

const explainability = {
  mode: "immediate",
  score: {
    weighted_signal_total: 68.3,
    bonus_total: 6,
    pre_clip_score: 74.3,
    final_score: 74.3,
    was_clipped: false,
  },
  signals: [
    {
      key: "effective_heatmap_score_pct",
      label: "Heatmap evidence",
      description: "Backend-provided signal description.",
      source_score: null,
      input_score: 70,
      weight: 0.12,
      weighted_contribution: 8.4,
      evidence_status: "fallback",
      note: "Backend-provided fallback note.",
    },
  ],
  bonuses: [
    {
      key: "same_final_role",
      label: "Same final role",
      configured_points: 6,
      applied: true,
      applied_points: 6,
    },
  ],
  reasons: [
    {
      key: "same_final_role",
      group: "role",
      text: "same final role",
    },
  ],
} as unknown as Explainability;

describe("RecommendationExplainability", () => {
  it("localizes structured recommendation evidence", () => {
    render(
      <NextIntlClientProvider locale="tr" messages={turkishMessages}>
        <RecommendationExplainability explainability={explainability} />
      </NextIntlClientProvider>,
    );

    expect(screen.getByText("Neden bu aday?")).toBeInTheDocument();

    expect(screen.getByText("Skor dökümünü görüntüle")).toBeInTheDocument();

    expect(screen.getByText("Yedek girdi")).toBeInTheDocument();

    expect(screen.getByText("Uygulandı")).toBeInTheDocument();

    expect(screen.getByText("Isı haritası kanıtı")).toBeInTheDocument();

    expect(screen.getByText("Aynı nihai rol")).toBeInTheDocument();

    expect(screen.getByText("aynı nihai rol")).toBeInTheDocument();

    expect(
      screen.getByText(
        "Oyuncu alım skorlama modelinde kullanılan ısı haritası yerleşim kanıtı.",
      ),
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        "Doğrudan ısı haritası kanıtı bulunmadığı için skorlamada yapılandırılmış nötr yedek değer kullanılıyor.",
      ),
    ).toBeInTheDocument();
  });

  it("retains the English presentation contract", () => {
    render(
      <NextIntlClientProvider locale="en" messages={englishMessages}>
        <RecommendationExplainability explainability={explainability} />
      </NextIntlClientProvider>,
    );

    expect(screen.getByText("Why this candidate")).toBeInTheDocument();

    expect(screen.getByText("Fallback input")).toBeInTheDocument();
  });
});
