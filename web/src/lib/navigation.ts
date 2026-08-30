export type PrimaryNavigationMessageKey =
  | "home"
  | "players"
  | "shortlists"
  | "methodology";

export type PrimaryNavigationItem = Readonly<{
  messageKey: PrimaryNavigationMessageKey;
  href: string;
  activePrefixes: readonly string[];
}>;

export const primaryNavigationItems =
  [
    {
      messageKey: "home",
      href: "/",
      activePrefixes: ["/"],
    },
    {
      messageKey: "players",
      href: "/players",
      activePrefixes: [
        "/players",
        "/analysis",
        "/compare",
      ],
    },
    {
      messageKey: "shortlists",
      href: "/shortlists",
      activePrefixes: [
        "/shortlists",
      ],
    },
    {
      messageKey: "methodology",
      href: "/methodology",
      activePrefixes: ["/methodology"],
    },
  ] as const satisfies readonly PrimaryNavigationItem[];

export function isNavigationItemActive(
  pathname: string,
  item: PrimaryNavigationItem,
): boolean {
  if (item.href === "/") {
    return pathname === "/";
  }

  return item.activePrefixes.some(
    (prefix) =>
      pathname === prefix ||
      pathname.startsWith(`${prefix}/`),
  );
}
