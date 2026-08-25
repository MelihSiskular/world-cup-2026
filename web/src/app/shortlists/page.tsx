import type {
  Metadata,
} from "next";

import {
  PageContainer,
} from "@/components/layout/page-container";
import {
  ShortlistManager,
} from "@/components/shortlists/shortlist-manager";

export const metadata: Metadata = {
  title: "Shortlists",
  description:
    "Create and manage browser-saved World Cup 2026 recruitment shortlists.",
};

export default function ShortlistsPage() {
  return (
    <PageContainer className="py-14 sm:py-20">
      <ShortlistManager />
    </PageContainer>
  );
}
