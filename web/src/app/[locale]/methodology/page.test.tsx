import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { MethodologyPageContent as MethodologyPage } from "@/app/[locale]/methodology/page";
import { renderWithQueryClient } from "@/test/render-with-query-client";

describe("MethodologyPage", () => {
  it("explains the current player and comparison evidence", () => {
    renderWithQueryClient(<MethodologyPage />);

    expect(
      screen.getByRole("heading", {
        name: "How to read player evidence",
      }),
    ).toBeInTheDocument();

    expect(screen.getByText("Raw and per-90 values")).toBeInTheDocument();

    expect(screen.getByText("Same-position percentile")).toBeInTheDocument();

    expect(
      screen.getByText("From performance profile to tactical role"),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("heading", {
        name: "How final roles separate on the pitch",
      }),
    ).toBeInTheDocument();

    expect(screen.getByText("Measured heatmap")).toBeInTheDocument();

    expect(
      screen.queryByText("Dataset and application identity"),
    ).not.toBeInTheDocument();

    expect(
      screen.queryByText("Analytics ownership boundary"),
    ).not.toBeInTheDocument();
  });
  it("localizes the methodology foundation in Turkish", () => {
    renderWithQueryClient(<MethodologyPage />, "tr");

    expect(
      screen.getByRole("heading", {
        name: "Oyuncu kanıtları nasıl okunur?",
      }),
    ).toBeInTheDocument();

    expect(
      screen.getByText("Ham ve 90 dakika başına değerler"),
    ).toBeInTheDocument();

    expect(
      screen.getByText("Aynı pozisyon yüzdelik dilimi"),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("heading", {
        name: "Performans profilinden taktik role",
      }),
    ).toBeInTheDocument();

    expect(screen.getByText("Ölçülen veri sıfır değildir")).toBeInTheDocument();

    expect(
      screen.getByRole("heading", {
        name: "Nihai roller sahada nasıl ayrışır?",
      }),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("heading", {
        name: "Karar motoru neyi değerlendirir?",
      }),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("heading", {
        name: "İstatistiksel benzerlik",
      }),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("heading", {
        name: "Farklı görünümler farklı soruları yanıtlar",
      }),
    ).toBeInTheDocument();

    expect(screen.getByText("Ölçülen ısı haritası")).toBeInTheDocument();

    expect(
      screen.getByRole("heading", {
        name: "Tek aday havuzu, dört farklı karar",
      }),
    ).toBeInTheDocument();

    expect(screen.getByText("Hazır katkı")).toBeInTheDocument();

    expect(screen.getAllByText("Puan ağırlıkları")).toHaveLength(4);

    expect(
      screen.getByRole("heading", {
        name: "Puan, sıralama ve açıklama nasıl üretilir?",
      }),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("heading", {
        name: "Öneri gücü bantları",
      }),
    ).toBeInTheDocument();

    expect(screen.getByText("Üst düzey")).toBeInTheDocument();

    expect(
      screen.getByRole("heading", {
        name: "Analizin kanıtlamadığı noktalar",
      }),
    ).toBeInTheDocument();
  });
});
