import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { PlayerImage, getPlayerImageSrc } from "./player-image";

describe("PlayerImage", () => {
  it("builds a deterministic player-image path", () => {
    expect(getPlayerImageSrc(978838)).toBe("/player-images/978838.png");
  });

  it("renders the player photo with accessible identity", () => {
    render(
      <PlayerImage
        playerId={978838}
        playerName="Michael Olise"
        size="profile"
      />,
    );

    const image = screen.getByRole("img", {
      name: "Michael Olise player photo",
    });

    expect(
      new URL(image.getAttribute("src") ?? "", "http://localhost").pathname,
    ).toBe("/player-images/978838.png");

    expect(image).toHaveAttribute("alt", "Michael Olise player photo");
  });

  it("falls back to initials when the image cannot load", () => {
    render(<PlayerImage playerId={978838} playerName="Michael Olise" />);

    fireEvent.error(
      screen.getByRole("img", {
        name: "Michael Olise player photo",
      }),
    );

    const fallback = screen.getByRole("img", {
      name: "Michael Olise player photo unavailable",
    });

    expect(fallback).toHaveTextContent("MO");
  });

  it("tries a new image when the player changes after a failure", () => {
    const { rerender } = render(
      <PlayerImage playerId={978838} playerName="Michael Olise" />,
    );

    fireEvent.error(
      screen.getByRole("img", {
        name: "Michael Olise player photo",
      }),
    );

    rerender(<PlayerImage playerId={12345} playerName="Another Player" />);

    const nextImage = screen.getByRole("img", {
      name: "Another Player player photo",
    });

    expect(
      new URL(nextImage.getAttribute("src") ?? "", "http://localhost").pathname,
    ).toBe("/player-images/12345.png");
  });
});
