type CountryFlagProps = Readonly<{
  countryAlpha3?: string | null;
  countryName?: string | null;
  className?: string;
}>;

const COUNTRY_ALPHA3_BY_NAME: Readonly<Record<string, string>> = {
  algeria: "DZA",
  argentina: "ARG",
  australia: "AUS",
  austria: "AUT",
  belgium: "BEL",
  "bosnia and herzegovina": "BIH",
  "bosnia & herzegovina": "BIH",
  "bosnia-herzegovina": "BIH",
  brazil: "BRA",
  canada: "CAN",
  "cape verde": "CPV",
  "cape verde islands": "CPV",
  colombia: "COL",
  "congo dr": "COD",
  croatia: "HRV",
  curacao: "CUW",
  czechia: "CZE",
  "czech republic": "CZE",
  "democratic republic of the congo": "COD",
  "dr congo": "COD",
  ecuador: "ECU",
  egypt: "EGY",
  england: "ENG",
  france: "FRA",
  germany: "DEU",
  ghana: "GHA",
  haiti: "HTI",
  iran: "IRN",
  "ir iran": "IRN",
  iraq: "IRQ",
  "ivory coast": "CIV",
  japan: "JPN",
  jordan: "JOR",
  "korea republic": "KOR",
  mexico: "MEX",
  morocco: "MAR",
  netherlands: "NLD",
  "new zealand": "NZL",
  norway: "NOR",
  panama: "PAN",
  paraguay: "PRY",
  portugal: "PRT",
  qatar: "QAT",
  "republic of korea": "KOR",
  "saudi arabia": "SAU",
  scotland: "SCO",
  senegal: "SEN",
  "south africa": "ZAF",
  "south korea": "KOR",
  spain: "ESP",
  sweden: "SWE",
  switzerland: "CHE",
  tunisia: "TUN",
  turkey: "TUR",
  turkiye: "TUR",
  "united kingdom": "GBR",
  "united states": "USA",
  "united states of america": "USA",
  uruguay: "URY",
  usa: "USA",
  uzbekistan: "UZB",
};

function normalizeCountryName(value: string | null | undefined): string | null {
  if (value == null) {
    return null;
  }

  const normalized = value
    .trim()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[’‘]/g, "'")
    .replace(/\s+/g, " ")
    .toLowerCase();

  return normalized.length > 0 ? normalized : null;
}

function normalizeCountryAlpha3(
  value: string | null | undefined,
): string | null {
  if (value == null) {
    return null;
  }

  const normalized = value.trim().toUpperCase();

  if (!/^[A-Z]{3}$/.test(normalized)) {
    return null;
  }

  return normalized;
}

export function countryAlpha3FromName(
  value: string | null | undefined,
): string | null {
  const normalized = normalizeCountryName(value);

  if (normalized === null) {
    return null;
  }

  return COUNTRY_ALPHA3_BY_NAME[normalized] ?? null;
}

export function CountryFlag({
  countryAlpha3,
  countryName,
  className = "",
}: CountryFlagProps) {
  const normalized =
    normalizeCountryAlpha3(countryAlpha3) ?? countryAlpha3FromName(countryName);

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
