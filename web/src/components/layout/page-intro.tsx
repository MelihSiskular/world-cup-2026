import type {
  ReactNode,
} from "react";

type PageIntroProps =
  Readonly<{
    eyebrow: string;
    title: string;
    description: string;
    actions?: ReactNode;
  }>;

export function PageIntro({
  eyebrow,
  title,
  description,
  actions,
}: PageIntroProps) {
  return (
    <header className="max-w-4xl">
      <p className="text-sm font-semibold tracking-[0.18em] text-brand uppercase">
        {eyebrow}
      </p>

      <h1 className="mt-4 text-4xl font-bold tracking-[-0.04em] text-balance sm:text-5xl lg:text-6xl">
        {title}
      </h1>

      <p className="mt-6 max-w-3xl text-lg leading-8 text-muted">
        {description}
      </p>

      {actions ? (
        <div className="mt-8 flex flex-wrap items-center gap-3">
          {actions}
        </div>
      ) : null}
    </header>
  );
}
