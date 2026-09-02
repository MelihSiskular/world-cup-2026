"use client";

import Image from "next/image";
import { useTranslations } from "next-intl";
import { type KeyboardEvent, useRef, useState } from "react";

import defenderData from "@/data/methodology/final-role-maps/d_role_map.json";
import forwardData from "@/data/methodology/final-role-maps/f_role_map.json";
import midfielderData from "@/data/methodology/final-role-maps/m_role_map.json";

type RoleIndexEntry = Readonly<{
  code: string;
  name: string;
  player_count: number;
  color: string;
  center_x_pct: number;
  center_y_pct: number;
}>;

type RoleMapData = Readonly<{
  position: string;
  player_count: number;
  role_count: number;
  minimum_role_size: number;
  roles: readonly RoleIndexEntry[];
}>;

const maps = [
  {
    key: "defender",
    source: "/methodology/final-role-maps/d_role_map.png",
    data: defenderData as RoleMapData,
  },
  {
    key: "midfielder",
    source: "/methodology/final-role-maps/m_role_map.png",
    data: midfielderData as RoleMapData,
  },
  {
    key: "forward",
    source: "/methodology/final-role-maps/f_role_map.png",
    data: forwardData as RoleMapData,
  },
] as const;

const lastIndex = maps.length - 1;

function clampIndex(index: number): number {
  return Math.min(Math.max(index, 0), lastIndex);
}

export function FinalRoleMapCarousel() {
  const t = useTranslations("Methodology.finalRoleMaps");
  const [activeIndex, setActiveIndex] = useState(0);
  const buttonRefs = useRef<Array<HTMLButtonElement | null>>([]);
  const activeMap = maps[activeIndex] ?? maps[0];

  const selectMap = (requestedIndex: number, focusButton = false) => {
    const nextIndex = clampIndex(requestedIndex);
    setActiveIndex(nextIndex);
    if (focusButton) buttonRefs.current[nextIndex]?.focus();
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

  return (
    <section aria-labelledby="final-role-maps-heading" className="mt-16">
      <p className="text-sm font-semibold tracking-[0.14em] text-brand uppercase">
        {t("eyebrow")}
      </p>
      <h2
        id="final-role-maps-heading"
        className="mt-3 text-3xl font-bold tracking-[-0.04em]"
      >
        {t("title")}
      </h2>
      <p className="mt-4 max-w-3xl text-sm leading-7 text-muted">
        {t("description")}
      </p>

      <div className="mt-7 overflow-hidden rounded-3xl border border-border bg-surface shadow-sm">
        <div
          role="tablist"
          aria-label={t("positionSelectorLabel")}
          className="flex gap-2 overflow-x-auto border-b border-border p-4 sm:p-5"
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
                id={`final-role-tab-${map.key}`}
                type="button"
                role="tab"
                aria-controls={`final-role-panel-${map.key}`}
                aria-selected={active}
                tabIndex={active ? 0 : -1}
                onClick={() => selectMap(index)}
                className={[
                  "shrink-0 rounded-full border px-4 py-2 text-sm font-semibold transition-colors",
                  active
                    ? "border-brand bg-brand text-white"
                    : "border-border bg-page text-muted hover:border-brand hover:text-foreground",
                ].join(" ")}
              >
                {t(`positions.${map.key}.label`)}
              </button>
            );
          })}
        </div>

        <article
          id={`final-role-panel-${activeMap.key}`}
          role="tabpanel"
          aria-labelledby={`final-role-tab-${activeMap.key}`}
        >
          <header className="flex flex-wrap items-start justify-between gap-4 border-b border-border px-5 py-5 sm:px-6">
            <div className="max-w-3xl">
              <h3 className="text-xl font-bold tracking-[-0.025em]">
                {t(`positions.${activeMap.key}.title`)}
              </h3>
              <p className="mt-2 text-sm leading-6 text-muted">
                {t(`positions.${activeMap.key}.description`)}
              </p>
            </div>

            <div className="flex flex-wrap gap-2">
              <span className="rounded-full border border-border bg-page px-3 py-1.5 text-xs font-semibold text-muted">
                {t("playerSummary", {
                  count: activeMap.data.player_count,
                })}
              </span>
              <span className="rounded-full border border-border bg-page px-3 py-1.5 text-xs font-semibold text-muted">
                {t("roleSummary", { count: activeMap.data.role_count })}
              </span>
            </div>
          </header>

          <div className="final-role-map-content grid min-w-0 lg:grid-cols-5">
            <figure className="final-role-map-visual min-w-0 border-b border-border p-4 sm:p-6 lg:col-span-3 lg:border-r lg:border-b-0">
              <div
                className="relative h-full w-full overflow-hidden rounded-2xl border border-white/15 shadow-inner"
                style={{
                  aspectRatio: "105 / 68",
                  backgroundColor: "#0b632d",
                }}
              >
                <Image
                  src={activeMap.source}
                  alt={t(`positions.${activeMap.key}.alt`)}
                  fill
                  sizes="(min-width: 1024px) 58vw, calc(100vw - 3rem)"
                  priority={activeIndex === 0}
                  className="object-contain p-2 sm:p-3"
                />
              </div>
            </figure>

            <aside className="final-role-map-index flex min-h-0 min-w-0 flex-col bg-surface-secondary p-4 sm:p-6 lg:col-span-2">
              <h3 className="text-lg font-bold tracking-[-0.02em]">
                {t("roleIndexTitle")}
              </h3>
              <p className="mt-2 max-w-lg text-xs leading-5 text-muted">
                {t("roleIndexDescription")}
              </p>

              <ul
                aria-label={t("roleIndexTitle")}
                tabIndex={0}
                className="final-role-map-index-list mt-4 grid min-h-0 flex-1 content-start gap-x-4 rounded-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-brand/30 focus-visible:ring-inset sm:grid-cols-2"
              >
                {activeMap.data.roles.map((role) => (
                  <li
                    key={role.code}
                    className="flex min-w-0 items-start gap-2.5 border-t border-border py-2"
                  >
                    <span
                      aria-hidden="true"
                      className="shrink-0 text-base font-black leading-5"
                      style={{ color: role.color }}
                    >
                      ×
                    </span>

                    <span className="min-w-0 flex-1">
                      <span className="flex items-baseline justify-between gap-2">
                        <span className="text-xs font-bold text-foreground">
                          {role.code}
                        </span>
                        <span className="shrink-0 text-[0.68rem] text-muted">
                          {t("rolePlayerCount", {
                            count: role.player_count,
                          })}
                        </span>
                      </span>
                      <span className="mt-0.5 block break-words text-[0.72rem] font-semibold leading-4 text-foreground">
                        {role.name}
                      </span>
                    </span>
                  </li>
                ))}
              </ul>
            </aside>
          </div>
        </article>

        <div className="flex items-center justify-between gap-4 border-t border-border px-4 py-3 sm:px-6">
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
            <h3 className="text-lg font-bold">{t("interpretation.title")}</h3>
            <p className="mt-3 text-sm leading-6 text-muted">
              {t("interpretation.description")}
            </p>
          </article>
        </div>
      </div>
    </section>
  );
}
