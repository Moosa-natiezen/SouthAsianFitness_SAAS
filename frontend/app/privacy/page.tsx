import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Privacy Policy",
  description:
    "Privacy Policy for South Asian Fitness. Learn how we collect, use, and protect your personal data.",
};

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-[#FCFBF7]">
      <div className="mx-auto max-w-3xl px-6 py-12">
        <Link
          href="/"
          className="text-sm font-medium text-stone-500 hover:text-stone-900 transition-colors"
        >
          ← Back to South Asian Fitness
        </Link>

        <h1 className="mt-8 text-4xl font-bold tracking-tight text-stone-900">
          Privacy Policy
        </h1>
        <p className="mt-2 text-sm text-stone-400">
          Effective date: August 1, 2026 · Last updated: September 4, 2026
        </p>

        <div className="mt-10 space-y-10 text-stone-600 leading-relaxed">
          {/* ── Introduction ────────────────────────────────────────── */}
          <section>
            <p>
              South Asian Fitness (&quot;we,&quot; &quot;us,&quot; or &quot;our&quot;) is committed to
              protecting your privacy. This Privacy Policy explains how we collect, use,
              disclose, and safeguard your information when you use our website and services
              at{" "}
              <span className="font-medium text-stone-900">
                southasianfitness.com
              </span>{" "}
              (the &quot;Service&quot;). By using the Service, you agree to the collection and
              use of information in accordance with this policy.
            </p>
          </section>

          {/* ── 1. Information We Collect ──────────────────────────── */}
          <section>
            <h2 className="text-xl font-semibold text-stone-900">
              1. Information We Collect
            </h2>
            <div className="mt-4 space-y-4">
              <div>
                <h3 className="text-base font-semibold text-stone-800">
                  Account Information
                </h3>
                <p className="mt-1">
                  When you create an account, we collect your email address and display
                  name. If you sign in via Google OAuth, we receive your Google profile
                  information (name, email, and profile photo) as authorized by you during
                  the sign-in process.
                </p>
              </div>
              <div>
                <h3 className="text-base font-semibold text-stone-800">
                  Profile &amp; Health Data
                </h3>
                <p className="mt-1">
                  During onboarding and through the Service, you may provide personal
                  information including age, sex, height, weight, activity level, fitness
                  goals, dietary preferences, food allergies, cuisine preferences, and
                  weekly budget. This data is used exclusively to calculate your
                  personalized nutrition targets and generate meal plans.
                </p>
              </div>
              <div>
                <h3 className="text-base font-semibold text-stone-800">
                  Usage Data
                </h3>
                <p className="mt-1">
                  We collect anonymous usage analytics (page views, feature interactions)
                  through PostHog, a third-party analytics provider. This data is aggregated
                  and does not personally identify you.
                </p>
              </div>
              <div>
                <h3 className="text-base font-semibold text-stone-800">
                  Cookies &amp; Sessions
                </h3>
                <p className="mt-1">
                  We use essential cookies for authentication sessions and CSRF protection.
                  These cookies are strictly necessary for the Service to function and are
                  not used for advertising or tracking purposes.
                </p>
              </div>
            </div>
          </section>

          {/* ── 2. How We Use Your Information ─────────────────────── */}
          <section>
            <h2 className="text-xl font-semibold text-stone-900">
              2. How We Use Your Information
            </h2>
            <ul className="mt-4 list-disc pl-5 space-y-2">
              <li>
                To calculate your personalized calorie targets, macronutrient goals, and
                daily budgets using the Mifflin-St Jeor equation.
              </li>
              <li>
                To generate AI-powered meal plans and workout routines tailored to your
                goals, dietary preferences, and cultural food preferences.
              </li>
              <li>
                To provide a searchable food library of 200+ South Asian dishes with
                accurate macro data.
              </li>
              <li>
                To track your progress over time and display visual analytics.
              </li>
              <li>
                To authenticate your account and maintain secure sessions.
              </li>
              <li>
                To communicate essential service updates (we will never send marketing
                emails without explicit consent).
              </li>
            </ul>
            <p className="mt-4 font-medium text-stone-800">
              We do not sell, rent, share, or monetize your personal data with third
              parties for advertising or marketing purposes.
            </p>
          </section>

          {/* ── 3. Data Security ───────────────────────────────────── */}
          <section>
            <h2 className="text-xl font-semibold text-stone-900">
              3. Data Security
            </h2>
            <p className="mt-4">
              We implement industry-standard security measures to protect your data:
            </p>
            <ul className="mt-3 list-disc pl-5 space-y-2">
              <li>
                Passwords are hashed using bcrypt with a high cost factor — we never
                store or can access your plain-text password.
              </li>
              <li>
                All authentication uses secure, HttpOnly session cookies with CSRF
                token protection.
              </li>
              <li>
                All communication is encrypted via TLS (HTTPS) in transit.
              </li>
              <li>
                Database access is restricted and credentials are never committed to
                source control.
              </li>
            </ul>
            <p className="mt-4">
              While we strive to use commercially acceptable means to protect your
              personal information, no method of electronic transmission or storage is
              100% secure. We cannot guarantee absolute security.
            </p>
          </section>

          {/* ── 4. Third-Party Services ────────────────────────────── */}
          <section>
            <h2 className="text-xl font-semibold text-stone-900">
              4. Third-Party Services
            </h2>
            <p className="mt-4">
              We use the following third-party services that may collect or process
              information on our behalf:
            </p>
            <div className="mt-4 space-y-4">
              <div className="rounded-xl border border-stone-200 bg-white p-4">
                <h3 className="font-semibold text-stone-900">
                  Google OAuth (Authentication)
                </h3>
                <p className="mt-1 text-sm">
                  When you choose &quot;Continue with Google,&quot; Google&apos;s authentication
                  service provides your name, email, and profile photo. We use this only
                  to create or log in to your account. See{" "}
                  <a
                    href="https://policies.google.com/privacy"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-emerald-600 underline underline-offset-2 hover:text-emerald-700"
                  >
                    Google&apos;s Privacy Policy
                  </a>
                  .
                </p>
              </div>
              <div className="rounded-xl border border-stone-200 bg-white p-4">
                <h3 className="font-semibold text-stone-900">
                  Lemon Squeezy (Payments)
                </h3>
                <p className="mt-1 text-sm">
                  Subscription billing and payment processing are handled by Lemon
                  Squeezy. We do not store your credit card information. Lemon Squeezy
                  processes payments in accordance with PCI-DSS standards. See{" "}
                  <a
                    href="https://www.lemonsqueezy.com/privacy"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-emerald-600 underline underline-offset-2 hover:text-emerald-700"
                  >
                    Lemon Squeezy&apos;s Privacy Policy
                  </a>
                  .
                </p>
              </div>
              <div className="rounded-xl border border-stone-200 bg-white p-4">
                <h3 className="font-semibold text-stone-900">
                  PostHog (Analytics)
                </h3>
                <p className="mt-1 text-sm">
                  We use PostHog for anonymous product analytics to improve the
                  Service. PostHog collects anonymized usage data (page views, feature
                  interactions) that does not directly identify you. See{" "}
                  <a
                    href="https://posthog.com/privacy"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-emerald-600 underline underline-offset-2 hover:text-emerald-700"
                  >
                    PostHog&apos;s Privacy Policy
                  </a>
                  .
                </p>
              </div>
              <div className="rounded-xl border border-stone-200 bg-white p-4">
                <h3 className="font-semibold text-stone-900">
                  OpenAI (AI Generation)
                </h3>
                <p className="mt-1 text-sm">
                  AI-generated meal plans and workout routines are powered by OpenAI.
                  Your profile data (calorie targets, dietary preferences) is sent to
                  OpenAI&apos;s API to generate personalized content. We do not send your
                  name, email, or any directly identifying information. OpenAI does not
                  use API inputs to train its models. See{" "}
                  <a
                    href="https://openai.com/policies/privacy-policy"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-emerald-600 underline underline-offset-2 hover:text-emerald-700"
                  >
                    OpenAI&apos;s Privacy Policy
                  </a>
                  .
                </p>
              </div>
            </div>
          </section>

          {/* ── 5. Data Retention ──────────────────────────────────── */}
          <section>
            <h2 className="text-xl font-semibold text-stone-900">
              5. Data Retention
            </h2>
            <p className="mt-4">
              We retain your account and profile data for as long as your account is
              active. If you delete your account, we will remove your personal data from
              our active databases within 30 days. Anonymized, aggregated analytics data
              (which cannot be traced back to you) may be retained indefinitely.
            </p>
          </section>

          {/* ── 6. Your Rights ─────────────────────────────────────── */}
          <section>
            <h2 className="text-xl font-semibold text-stone-900">
              6. Your Rights
            </h2>
            <p className="mt-4">
              Depending on your jurisdiction, you may have the right to:
            </p>
            <ul className="mt-3 list-disc pl-5 space-y-2">
              <li>
                <strong>Access</strong> the personal data we hold about you.
              </li>
              <li>
                <strong>Correct</strong> inaccurate or incomplete personal data.
              </li>
              <li>
                <strong>Delete</strong> your account and associated personal data.
              </li>
              <li>
                <strong>Export</strong> your data in a portable format.
              </li>
              <li>
                <strong>Object</strong> to processing of your personal data.
              </li>
            </ul>
            <p className="mt-4">
              To exercise any of these rights, please contact us at the email below.
            </p>
          </section>

          {/* ── 7. Children&apos;s Privacy ──────────────────────────────── */}
          <section>
            <h2 className="text-xl font-semibold text-stone-900">
              7. Children&apos;s Privacy
            </h2>
            <p className="mt-4">
              The Service is not intended for use by children under the age of 13. We
              do not knowingly collect personal information from children. If you are a
              parent or guardian and believe your child has provided us with personal
              information, please contact us immediately.
            </p>
          </section>

          {/* ── 8. Changes to This Policy ──────────────────────────── */}
          <section>
            <h2 className="text-xl font-semibold text-stone-900">
              8. Changes to This Policy
            </h2>
            <p className="mt-4">
              We may update this Privacy Policy from time to time. We will notify you
              of any material changes by posting the new policy on this page with an
              updated &quot;Last updated&quot; date. Your continued use of the Service after
              any changes constitutes acceptance of the updated policy.
            </p>
          </section>

          {/* ── 9. Contact ─────────────────────────────────────────── */}
          <section>
            <h2 className="text-xl font-semibold text-stone-900">9. Contact Us</h2>
            <p className="mt-4">
              If you have any questions about this Privacy Policy, please contact us:
            </p>
            <div className="mt-3 rounded-xl border border-stone-200 bg-white p-4">
              <p className="text-stone-900 font-medium">
                Email:{" "}
                <a
                  href="mailto:support@southasianfitness.com"
                  className="text-emerald-600 underline underline-offset-2 hover:text-emerald-700"
                >
                  support@southasianfitness.com
                </a>
              </p>
              <p className="mt-1 text-sm text-stone-500">
                Website: southasianfitness.com
              </p>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
