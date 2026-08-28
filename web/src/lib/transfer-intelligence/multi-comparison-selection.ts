export const MAX_MULTI_COMPARISON_CANDIDATES =
  3;

export type MultiComparisonIdentifiers =
  Readonly<{
    targetPlayerId: number;
    candidatePlayerIds:
      readonly number[];
  }>;

export type MultiComparisonIdentifierIssueCode =
  | "invalid_target"
  | "invalid_candidate"
  | "invalid_candidate_count"
  | "duplicate_player";

export type MultiComparisonIdentifierResult =
  | Readonly<{
      success: true;
      values:
        MultiComparisonIdentifiers;
    }>
  | Readonly<{
      success: false;
      code:
        MultiComparisonIdentifierIssueCode;
      message: string;
    }>;

type CandidateSearchParameter =
  | string
  | readonly string[]
  | undefined;

function parsePositiveInteger(
  value: string | number,
): number | null {
  if (
    typeof value === "number"
  ) {
    return (
      Number.isSafeInteger(value)
      && value > 0
    )
      ? value
      : null;
  }

  const normalized =
    value.trim();

  if (
    !/^\d+$/u.test(
      normalized,
    )
  ) {
    return null;
  }

  const parsed =
    Number(normalized);

  return (
    Number.isSafeInteger(parsed)
    && parsed > 0
  )
    ? parsed
    : null;
}

function readCandidateParameter(
  value:
    CandidateSearchParameter,
): string | null {
  if (value === undefined) {
    return null;
  }

  if (
    typeof value === "string"
  ) {
    return value;
  }

  return value.length === 1
    ? value[0] ?? null
    : null;
}

export function parseMultiComparisonIdentifiers(
  targetPlayerId:
    string | number,
  candidateParameter:
    CandidateSearchParameter,
): MultiComparisonIdentifierResult {
  const parsedTarget =
    parsePositiveInteger(
      targetPlayerId,
    );

  if (parsedTarget === null) {
    return {
      success: false,
      code: "invalid_target",
      message:
        "Target player ID must be a positive integer.",
    };
  }

  const rawCandidates =
    readCandidateParameter(
      candidateParameter,
    );

  if (rawCandidates === null) {
    return {
      success: false,
      code:
        "invalid_candidate",
      message:
        "Candidate player IDs must use one canonical parameter.",
    };
  }

  const tokens =
    rawCandidates
      .split(",")
      .map(
        (value) =>
          value.trim(),
      );

  if (
    tokens.length < 1
    || tokens.length >
      MAX_MULTI_COMPARISON_CANDIDATES
  ) {
    return {
      success: false,
      code:
        "invalid_candidate_count",
      message:
        `Select between 1 and ${MAX_MULTI_COMPARISON_CANDIDATES} candidates.`,
    };
  }

  const parsedCandidates =
    tokens.map(
      parsePositiveInteger,
    );

  if (
    parsedCandidates.some(
      (value) =>
        value === null,
    )
  ) {
    return {
      success: false,
      code:
        "invalid_candidate",
      message:
        "Every candidate player ID must be a positive integer.",
    };
  }

  const candidatePlayerIds =
    parsedCandidates as number[];

  if (
    candidatePlayerIds.includes(
      parsedTarget,
    )
    || new Set(
      candidatePlayerIds,
    ).size !==
      candidatePlayerIds.length
  ) {
    return {
      success: false,
      code:
        "duplicate_player",
      message:
        "Target and candidate player IDs must be unique.",
    };
  }

  return {
    success: true,
    values: {
      targetPlayerId:
        parsedTarget,
      candidatePlayerIds,
    },
  };
}

export function createMultiComparisonHref(
  identifiers:
    MultiComparisonIdentifiers,
): string {
  const validation =
    parseMultiComparisonIdentifiers(
      identifiers.targetPlayerId,
      identifiers
        .candidatePlayerIds
        .join(","),
    );

  if (!validation.success) {
    throw new TypeError(
      validation.message,
    );
  }

  const parameters =
    new URLSearchParams({
      candidates:
        validation.values
          .candidatePlayerIds
          .join(","),
    });

  return (
    `/compare/multi/${validation.values.targetPlayerId}`
    + `?${parameters.toString()}`
  );
}
