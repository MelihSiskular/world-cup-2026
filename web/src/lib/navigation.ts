export type PrimaryNavigationItem = Readonly<{
  label: string;
  href: string;
  activePrefixes: readonly string[];
}>;

export const primaryNavigationItems =
  [
    {
      label: "Home",
      href: "/",
      activePrefixes: ["/"],
    },
    {
      label: "Players",
      href: "/players",
      activePrefixes: [
        "/players",
        "/analysis",
        "/compare",
      ],
    },
    {
      label: "Methodology",
      href: "/methodology",
      activePrefixes: ["/methodology"],
    },
    {
      label: "API Status",
      href: "/status",
      activePrefixes: ["/status"],
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
