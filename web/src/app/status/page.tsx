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
  title: "API Status",
  description:
    "Live health, readiness and deployment information for the WC26 analytics API.",
};

export default function StatusPage() {
  return (
    <PageContainer className="py-14 sm:py-20">
      <PageIntro
        eyebrow="System status"
        title="Analytics API and dataset readiness"
        description="Live status information is retrieved through the Next.js server layer without exposing the backend configuration to the browser."
      />

      <section className="mt-12">
        <ApiStatusOverview />
      </section>
    </PageContainer>
  );
}
