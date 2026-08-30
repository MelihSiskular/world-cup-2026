export type ProfileFormatContext =
  Readonly<{
    locale?: string;
    missingValue?: string;
  }>;

type PlayerPositionFormatOptions =
  Readonly<{
    labels?: Readonly<
      Record<string, string>
    >;
    unavailable?: string;
  }>;

const positionLabels:
  Readonly<Record<string, string>> = {
    G: "Goalkeeper",
    D: "Defender",
    M: "Midfielder",
    F: "Forward",
  };

export function formatPlayerPosition(
  position: string | null | undefined,
  options:
    PlayerPositionFormatOptions = {},
): string {
  if (!position) {
    return (
      options.unavailable ??
      "Position unavailable"
    );
  }

  return (
    options.labels?.[position] ??
    positionLabels[position] ??
    position
  );
}

export function formatProfileNumber(
  value: number | null | undefined,
  options: Intl.NumberFormatOptions = {},
  context: ProfileFormatContext = {},
): string {
  if (value === null || value === undefined) {
    return (
      context.missingValue ??
      "Not reported"
    );
  }

  return new Intl.NumberFormat(
    context.locale ?? "en",
    options,
  ).format(value);
}

export function formatProfilePercentage(
  value: number | null | undefined,
  context: ProfileFormatContext = {},
): string {
  if (value === null || value === undefined) {
    return (
      context.missingValue ??
      "Not reported"
    );
  }

  return `${formatProfileNumber(
    value,
    {
      maximumFractionDigits: 1,
    },
    context,
  )}%`;
}

export function formatUnitIntervalPercentage(
  value: number | null | undefined,
  context: ProfileFormatContext = {},
): string {
  if (value === null || value === undefined) {
    return (
      context.missingValue ??
      "Not reported"
    );
  }

  return formatProfilePercentage(
    value * 100,
    context,
  );
}

export function formatMarketValue(
  value: number | null | undefined,
  currency: string | null | undefined,
  context: ProfileFormatContext = {},
): string {
  if (
    value === null ||
    value === undefined ||
    !currency
  ) {
    return (
      context.missingValue ??
      "Not reported"
    );
  }

  try {
    return new Intl.NumberFormat(
      context.locale ?? "en",
      {
        style: "currency",
        currency,
        notation: "compact",
        maximumFractionDigits: 1,
      },
    ).format(value);
  } catch {
    return `${formatProfileNumber(
      value,
      {},
      context,
    )} ${currency}`;
  }
}
