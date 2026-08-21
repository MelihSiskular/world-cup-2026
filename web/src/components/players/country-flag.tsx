type CountryFlagProps = Readonly<{
  countryAlpha3: string | null;
  className?: string;
}>;

function normalizeCountryAlpha3(
  value: string | null,
): string | null {
  if (value === null) {
    return null;
  }

  const normalized = value.trim().toUpperCase();

  if (!/^[A-Z]{3}$/.test(normalized)) {
    return null;
  }

  return normalized;
}

export function CountryFlag({
  countryAlpha3,
  className = "",
}: CountryFlagProps) {
  const normalized =
    normalizeCountryAlpha3(countryAlpha3);

  if (normalized === null) {
    return null;
  }

  return (
    <span
      aria-hidden="true"
      data-country-code={normalized}
      className={[
        "inline-block aspect-[4/3] w-5 shrink-0 rounded-[0.18rem] border border-black/10 bg-cover bg-center bg-no-repeat shadow-sm",
        className,
      ].join(" ")}
      style={{
        backgroundImage: `url("/country-flags/${normalized.toLowerCase()}.svg")`,
      }}
    />
  );
}
