import dynamic from "next/dynamic";
import { LandingPage } from "@/components/landing-page";

/* Below-fold sections: dynamically imported to reduce initial JS bundle */
const LeadMagnetSection = dynamic(
  () =>
    import("@/components/sections/lead-magnet-section").then(
      (m) => m.LeadMagnetSection,
    ),
  { ssr: false },
);

const TestimonialsSection = dynamic(
  () =>
    import("@/components/sections/testimonials-section").then(
      (m) => m.TestimonialsSection,
    ),
  { ssr: false },
);

const FAQSection = dynamic(
  () =>
    import("@/components/sections/faq-section").then((m) => m.FAQSection),
  { ssr: false },
);

export default function Home() {
  return (
    <>
      <LandingPage />
      <LeadMagnetSection />
      <TestimonialsSection />
      <FAQSection />
    </>
  );
}
