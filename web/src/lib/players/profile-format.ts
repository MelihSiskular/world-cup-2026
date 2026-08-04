const positionLabels:
  Readonly<Record<string, string>> = {
    G: "Goalkeeper",
    D: "Defender",
    M: "Midfielder",
    F: "Forward",
  };

export function formatPlayerPosition(
  position: string | null | undefined,
): string {
  if (!position) {
    return "Position unavailable";
  }

  return (
    positionLabels[position] ??
    position
  );
}

export function formatProfileNumber(
  value: number | null | undefined,
  options: Intl.NumberFormatOptions = {},
): string {
  if (value === null || value === undefined) {
    return "Not reported";
  }

  return new Intl.NumberFormat(
    "en",
    options,
  ).format(value);
}

export function formatProfilePercentage(
  value: number | null | undefined,
): string {
  if (value === null || value === undefined) {
    return "Not reported";
  }

  return `${formatProfileNumber(value, {
    maximumFractionDigits: 1,
  })}%`;
}

export function formatUnitIntervalPercentage(
  value: number | null | undefined,
): string {
  if (value === null || value === undefined) {
    return "Not reported";
  }

  return formatProfilePercentage(
    value * 100,
  );
}

export function formatMarketValue(
  value: number | null | undefined,
  currency: string | null | undefined,
): string {
  if (
    value === null ||
    value === undefined ||
    !currency
  ) {
    return "Not reported";
  }

  try {
    return new Intl.NumberFormat(
      "en",
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
    )} ${currency}`;
  }
}
