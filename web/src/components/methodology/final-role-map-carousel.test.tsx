import { fireEvent, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { FinalRoleMapCarousel } from "@/components/methodology/final-role-map-carousel";
import { renderWithQueryClient } from "@/test/render-with-query-client";

describe("FinalRoleMapCarousel", () => {
  it("renders the active role index and switches maps with the keyboard", () => {
    renderWithQueryClient(<FinalRoleMapCarousel />);

    const selector = screen.getByRole("tablist", {
      name: "Choose a final-role position map",
    });
    const defender = screen.getByRole("tab", { name: "Defenders" });
    const midfielder = screen.getByRole("tab", { name: "Midfielders" });

    expect(defender).toHaveAttribute("aria-selected", "true");
    expect(
      screen.getByRole("img", {
        name: "Pitch map showing defender final-role groups and their weighted centres",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Safe Ball-Playing Centre-Back"),
    ).toBeInTheDocument();
    expect(screen.getByText("D22")).toBeInTheDocument();
    expect(screen.getByText("193 players")).toBeInTheDocument();

    fireEvent.keyDown(selector, { key: "ArrowRight" });

    expect(midfielder).toHaveAttribute("aria-selected", "true");
    expect(document.activeElement).toBe(midfielder);
    expect(screen.getByText("Creative Central Midfielder")).toBeInTheDocument();
    expect(
      screen.queryByText("Safe Ball-Playing Centre-Back"),
    ).not.toBeInTheDocument();
    expect(screen.getByText("2 / 3")).toBeInTheDocument();
  });

  it("localizes the active role-map guidance in Turkish", () => {
    renderWithQueryClient(<FinalRoleMapCarousel />, "tr");

    expect(
      screen.getByRole("heading", {
        name: "Nihai roller sahada nasıl ayrışır?",
      }),
    ).toBeInTheDocument();
    expect(screen.getByText("Rol indeksi")).toBeInTheDocument();
    expect(screen.getByText("193 oyuncu")).toBeInTheDocument();
  });
});
