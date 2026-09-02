import { fireEvent, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ArchetypeMapCarousel } from "@/components/methodology/archetype-map-carousel";
import { renderWithQueryClient } from "@/test/render-with-query-client";

const scrollIntoViewMock = vi.fn();

Object.defineProperty(HTMLElement.prototype, "scrollIntoView", {
  configurable: true,
  value: scrollIntoViewMock,
});

describe("ArchetypeMapCarousel", () => {
  beforeEach(() => scrollIntoViewMock.mockClear());

  it("switches position maps with buttons and keyboard controls", () => {
    renderWithQueryClient(<ArchetypeMapCarousel />);

    const selector = screen.getByRole("group", {
      name: "Choose a position map",
    });
    const goalkeeper = screen.getByRole("button", {
      name: "Goalkeepers",
    });
    const defender = screen.getByRole("button", { name: "Defenders" });
    const forward = screen.getByRole("button", { name: "Forwards" });

    expect(goalkeeper).toHaveAttribute("aria-pressed", "true");

    fireEvent.keyDown(selector, { key: "ArrowRight" });
    expect(defender).toHaveAttribute("aria-pressed", "true");
    expect(document.activeElement).toBe(defender);

    fireEvent.click(forward);
    expect(forward).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByText("4 / 4")).toBeInTheDocument();
    expect(scrollIntoViewMock).toHaveBeenCalled();
  });

  it("localizes its guidance in Turkish", () => {
    renderWithQueryClient(<ArchetypeMapCarousel />, "tr");

    expect(
      screen.getByRole("heading", {
        name: "Oyun tarzı kümeleri nasıl oluşur?",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Kaleciler" }),
    ).toBeInTheDocument();
  });
});
