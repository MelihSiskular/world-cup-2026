"use client";

import Image from "next/image";
import { useTranslations } from "next-intl";
import { type KeyboardEvent, useRef, useState } from "react";

const maps = [
  {
    key: "goalkeeper",
    source: "/methodology/archetype-maps/goalkeeper_archetype_map.png",
    width: 3650,
    height: 2979,
  },
  {
    key: "defender",
    source: "/methodology/archetype-maps/defender_archetype_map.png",
    width: 3651,
    height: 2979,
  },
  {
    key: "midfielder",
    source: "/methodology/archetype-maps/midfielder_archetype_map.png",
    width: 3651,
    height: 2979,
  },
  {
    key: "forward",
    source: "/methodology/archetype-maps/forward_archetype_map.png",
    width: 3653,
    height: 2979,
  },
] as const;

const lastIndex = maps.length - 1;

function clampIndex(index: number): number {
  return Math.min(Math.max(index, 0), lastIndex);
}

export function ArchetypeMapCarousel() {
  const t = useTranslations("Methodology.archetypeMaps");
  const [activeIndex, setActiveIndex] = useState(0);
  const viewportRef = useRef<HTMLDivElement>(null);
  const buttonRefs = useRef<Array<HTMLButtonElement | null>>([]);

  const selectMap = (requestedIndex: number, focusButton = false) => {
    const nextIndex = clampIndex(requestedIndex);
    setActiveIndex(nextIndex);

    const slide = viewportRef.current?.children.item(nextIndex);
    if (slide instanceof HTMLElement) {
      slide.scrollIntoView({
        behavior: "smooth",
        block: "nearest",
        inline: "start",
      });
    }

    if (focusButton) {
      buttonRefs.current[nextIndex]?.focus();
    }
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLElement>) => {
    let nextIndex: number | null = null;

    if (event.key === "ArrowLeft") nextIndex = activeIndex - 1;
    if (event.key === "ArrowRight") nextIndex = activeIndex + 1;
    if (event.key === "Home") nextIndex = 0;
    if (event.key === "End") nextIndex = lastIndex;

    if (nextIndex === null) return;

    event.preventDefault();
    selectMap(nextIndex, true);
  };

  const handleScroll = () => {
    const viewport = viewportRef.current;
    if (!viewport || viewport.clientWidth === 0) return;

    setActiveIndex(
      clampIndex(Math.round(viewport.scrollLeft / viewport.clientWidth)),
    );
  };

  return (
    <section aria-labelledby="archetype-maps-heading" className="mt-16">
      <p className="text-sm font-semibold tracking-[0.14em] text-brand uppercase">
        {t("eyebrow")}
      </p>
      <h2
        id="archetype-maps-heading"
        className="mt-3 text-3xl font-bold tracking-[-0.04em]"
      >
        {t("title")}
      </h2>
      <p className="mt-4 max-w-3xl text-sm leading-7 text-muted">
        {t("description")}
      </p>

      <div className="mt-7 overflow-hidden rounded-3xl border border-border bg-surface shadow-sm">
        <div
          role="group"
          aria-label={t("positionSelectorLabel")}
          className="flex gap-2 overflow-x-auto border-b border-border p-4 [scrollbar-width:none] sm:p-5 [&::-webkit-scrollbar]:hidden"
          onKeyDown={handleKeyDown}
        >
          {maps.map((map, index) => {
            const active = index === activeIndex;
            return (
              <button
                key={map.key}
                ref={(element) => {
                  buttonRefs.current[index] = element;
                }}
                type="button"
                aria-controls={`archetype-map-${map.key}`}
                aria-pressed={active}
                onClick={() => selectMap(index)}
                className={[
                  "shrink-0 rounded-full border px-4 py-2 text-sm font-semibold transition-colors",
                  active
                    ? "border-brand bg-brand text-white"
                    : "border-border bg-page text-muted hover:border-brand/30 hover:text-foreground",
                ].join(" ")}
              >
                {t(`positions.${map.key}.label`)}
              </button>
            );
          })}
        </div>

        <div
          ref={viewportRef}
          role="region"
          aria-label={t("carouselLabel")}
          tabIndex={0}
          className="flex snap-x snap-mandatory overflow-x-auto overscroll-x-contain scroll-smooth [scrollbar-width:none] focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-brand [&::-webkit-scrollbar]:hidden"
          onKeyDown={handleKeyDown}
          onScroll={handleScroll}
        >
          {maps.map((map, index) => {
            const active = index === activeIndex;
            return (
              <figure
                key={map.key}
                id={`archetype-map-${map.key}`}
                aria-hidden={!active}
                className="min-w-full snap-start p-4 sm:p-6"
              >
                <div className="overflow-hidden rounded-2xl border border-border bg-white">
                  <Image
                    src={map.source}
                    alt={t(`positions.${map.key}.alt`)}
                    width={map.width}
                    height={map.height}
                    sizes="(min-width: 1280px) 1180px, (min-width: 768px) calc(100vw - 8rem), calc(100vw - 3rem)"
                    priority={index === 0}
                    className="h-auto max-h-[48rem] w-full object-contain"
                  />
                </div>

                <figcaption className="mt-5">
                  <div className="max-w-3xl">
                    <h3 className="text-xl font-bold tracking-[-0.025em]">
                      {t(`positions.${map.key}.title`)}
                    </h3>
                    <p className="mt-2 text-sm leading-6 text-muted">
                      {t(`positions.${map.key}.description`)}
                    </p>
                  </div>
                </figcaption>
              </figure>
            );
          })}
        </div>

        <div className="flex items-center justify-between gap-4 border-t border-border px-4 py-4 sm:px-6">
          <button
            type="button"
            disabled={activeIndex === 0}
            onClick={() => selectMap(activeIndex - 1)}
            className="rounded-xl border border-border bg-page px-3.5 py-2 text-sm font-semibold disabled:cursor-not-allowed disabled:opacity-40"
          >
            ← {t("previous")}
          </button>
          <p aria-live="polite" className="text-sm font-semibold text-muted">
            {t("positionCount", {
              current: activeIndex + 1,
              total: maps.length,
            })}
          </p>
          <button
            type="button"
            disabled={activeIndex === lastIndex}
            onClick={() => selectMap(activeIndex + 1)}
            className="rounded-xl border border-border bg-page px-3.5 py-2 text-sm font-semibold disabled:cursor-not-allowed disabled:opacity-40"
          >
            {t("next")} →
          </button>
        </div>

        <div className="grid gap-4 border-t border-border bg-surface-secondary p-5 sm:p-6 md:grid-cols-2">
          <article className="rounded-2xl border border-border bg-surface p-5">
            <h3 className="text-lg font-bold">{t("reading.title")}</h3>
            <p className="mt-3 text-sm leading-6 text-muted">
              {t("reading.description")}
            </p>
          </article>
          <article className="rounded-2xl border border-border bg-surface p-5">
            <h3 className="text-lg font-bold">{t("axes.title")}</h3>
            <p className="mt-3 text-sm leading-6 text-muted">
              {t("axes.description")}
            </p>
          </article>
        </div>

        <p className="border-t border-brand/15 bg-brand/5 px-5 py-4 text-sm leading-6 text-brand-dark sm:px-6">
          <strong>{t("roleConnection.title")}:</strong>{" "}
          {t("roleConnection.description")}
        </p>
      </div>
    </section>
  );
}
