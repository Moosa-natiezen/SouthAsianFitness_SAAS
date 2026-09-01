import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Terms of Service",
  description: "Terms of Service for South Asian Fitness.",
};

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-[#09090b]">
      <div className="mx-auto max-w-3xl px-6 py-12">
        <Link href="/" className="text-sm font-medium text-emerald-700 hover:text-emerald-800">
          ← Back to South Asian Fitness
        </Link>

        <h1 className="mt-6 text-3xl font-bold text-white">Terms of Service</h1>
        <p className="mt-2 text-sm text-zinc-500">Last updated: August 2026</p>

        <div className="mt-8 space-y-6 text-zinc-300">
          <section>
            <h2 className="text-xl font-semibold text-white">Acceptance</h2>
            <p className="mt-2">
              By creating an account and using South Asian Fitness, you agree to these terms.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white">Service Description</h2>
            <p className="mt-2">
              South Asian Fitness provides personalized nutrition targets and meal plan
              suggestions based on your profile. Our recommendations are for general
              informational purposes only and are not medical or clinical advice.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white">Health Disclaimer</h2>
            <p className="mt-2">
              The nutrition information and meal plans provided are general in nature and
              are not a substitute for professional medical advice, diagnosis, or treatment.
              Consult a qualified healthcare provider before making significant changes
              to your diet or exercise routine.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white">Account Responsibility</h2>
            <p className="mt-2">
              You are responsible for maintaining the confidentiality of your account
              credentials and for all activity under your account.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white">Contact</h2>
            <p className="mt-2">
              For questions about these terms, contact us at{" "}
              <span className="font-medium text-white">[CONTACT EMAIL TO BE ADDED]</span>.
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
