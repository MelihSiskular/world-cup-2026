import type {
  Metadata,
} from "next";

import {
  PageContainer,
} from "@/components/layout/page-container";
import {
  PageIntro,
} from "@/components/layout/page-intro";
import {
  ApiStatusOverview,
} from "@/components/status/api-status-overview";

export const metadata: Metadata = {
  title: "System Status",
  description:
    "Current availability of WC26 player data and scouting services.",
};

export default function StatusPage() {
  return (
    <PageContainer className="py-14 sm:py-20">
      <PageIntro
        eyebrow="System status"
        title="Scouting services at a glance"
        description="Check whether player data and transfer analysis services are ready to use."
      />

      <section className="mt-12">
        <ApiStatusOverview />
      </section>
    </PageContainer>
  );
}
