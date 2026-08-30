"use client";

import Image from "next/image";
import {
  useTranslations,
} from "next-intl";
import {
  useState,
} from "react";

type PlayerImageSize =
  | "compact"
  | "card"
  | "target"
  | "profile";

type PlayerImageProps =
  Readonly<{
    playerId: number;
    playerName: string;
    size?: PlayerImageSize;
    priority?: boolean;
    className?: string;
  }>;

type PlayerImageSizeConfig =
  Readonly<{
    container: string;
    initials: string;
    sizes: string;
  }>;

const SIZE_CONFIG: Record<
  PlayerImageSize,
  PlayerImageSizeConfig
> = {
  compact: {
    container:
      "size-12 rounded-xl",
    initials:
      "text-sm",
    sizes:
      "48px",
  },
  card: {
    container:
      "size-18 rounded-2xl",
    initials:
      "text-xl",
    sizes:
      "72px",
  },
  target: {
    container:
      "h-20 w-20 rounded-2xl",
    initials:
      "text-xl",
    sizes:
      "80px",
  },
  profile: {
    container:
      "size-42 rounded-3xl sm:size-44",
    initials:
      "text-2xl sm:text-3xl",
    sizes:
      "(min-width: 640px) 128px, 112px",
  },
};

function getPlayerInitials(
  playerName: string,
): string {
  const initials = playerName
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map(
      (part) =>
        part[0],
    )
    .join("")
    .toUpperCase();

  return initials || "?";
}

export function getPlayerImageSrc(
  playerId: number,
): string {
  return `/player-images/${playerId}.png`;
}

export function PlayerImage({
  playerId,
  playerName,
  size = "card",
  priority = false,
  className = "",
}: PlayerImageProps) {
  const translations =
    useTranslations("PlayerImage");

  const source =
    getPlayerImageSrc(
      playerId,
    );

  const [
    failedSource,
    setFailedSource,
  ] = useState<string | null>(
    null,
  );

  const config =
    SIZE_CONFIG[size];

  const showFallback =
    failedSource === source;

  const containerClassName = [
    "relative shrink-0 overflow-hidden",
    "border border-border",
    "bg-surface-secondary",
    config.container,
    className,
  ]
    .filter(Boolean)
    .join(" ");

  if (showFallback) {
    return (
      <div
        role="img"
        aria-label={translations(
          "photoUnavailable",
          {
            player:
              playerName,
          },
        )}
        className={[
          containerClassName,
          "flex items-center justify-center",
          "bg-brand-dark font-bold text-white",
          config.initials,
        ].join(" ")}
      >
        {getPlayerInitials(
          playerName,
        )}
      </div>
    );
  }

  return (
    <div
      className={
        containerClassName
      }
    >
      <Image
        src={source}
        alt={translations(
          "photoAlt",
          {
            player:
              playerName,
          },
        )}
        fill
        sizes={config.sizes}
        priority={priority}
        unoptimized
        className="object-cover object-bottom"
        onError={() => {
          setFailedSource(
            source,
          );
        }}
      />
    </div>
  );
}
