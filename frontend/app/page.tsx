import type { Metadata } from "next";
import dynamic from "next/dynamic";
import { LandingPage } from "@/components/landing-page";

export const metadata: Metadata = {
  alternates: { canonical: "https://www.southasianfitness.com" },
};

/* Below-fold sections: dynamically imported to reduce initial JS bundle */
const LeadMagnetSection = dynamic(
  () =>
    import("@/components/sections/lead-magnet-section").then(
      (m) => m.LeadMagnetSection,
    ),
);

const TestimonialsSection = dynamic(
  () =>
    import("@/components/sections/testimonials-section").then(
      (m) => m.TestimonialsSection,
    ),
);

const FAQSection = dynamic(
  () =>
    import("@/components/sections/faq-section").then((m) => m.FAQSection),
);

const MobileStickyCTA = dynamic(
  () => import("@/components/ui/mobile-sticky-cta").then((m) => m.MobileStickyCTA),
  { ssr: false },
);

const BackToTop = dynamic(
  () => import("@/components/ui/back-to-top").then((m) => m.BackToTop),
  { ssr: false },
);

export default function Home() {
  return (
    <>
      <LandingPage />
      <LeadMagnetSection />
      <TestimonialsSection />
      <FAQSection />
      <MobileStickyCTA />
      <BackToTop />
    </>
  );
}
