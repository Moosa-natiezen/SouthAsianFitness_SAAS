import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Terms of Service",
  description:
    "Terms of Service for South Asian Fitness. Read the terms governing your use of our platform.",
};

export default function TermsPage() {
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
          Terms of Service
        </h1>
        <p className="mt-2 text-sm text-stone-400">
          Effective date: August 1, 2026 · Last updated: September 4, 2026
        </p>

        <div className="mt-10 space-y-10 text-stone-600 leading-relaxed">
          {/* ── Introduction ────────────────────────────────────────── */}
          <section>
            <p>
              Welcome to South Asian Fitness (&quot;we,&quot; &quot;us,&quot; or &quot;our&quot;).
              These Terms of Service (&quot;Terms&quot;) govern your access to and use of our
              website, services, and applications at{" "}
              <span className="font-medium text-stone-900">
                southasianfitness.com
              </span>{" "}
              (the &quot;Service&quot;). Please read these Terms carefully before using the
              Service.
            </p>
          </section>

          {/* ── 1. Acceptance of Terms ─────────────────────────────── */}
          <section>
            <h2 className="text-xl font-semibold text-stone-900">
              1. Acceptance of Terms
            </h2>
            <p className="mt-4">
              By creating an account, accessing, or using the Service, you acknowledge
              that you have read, understood, and agree to be bound by these Terms and
              our{" "}
              <Link
                href="/privacy"
                className="text-emerald-600 underline underline-offset-2 hover:text-emerald-700"
              >
                Privacy Policy
              </Link>
              . If you do not agree to these Terms, you must not use the Service.
            </p>
            <p className="mt-3">
              You must be at least 13 years of age to use the Service. By using the
              Service, you represent and warrant that you meet this age requirement.
            </p>
          </section>

          {/* ── 2. Description of Service ──────────────────────────── */}
          <section>
            <h2 className="text-xl font-semibold text-stone-900">
              2. Description of Service
            </h2>
            <p className="mt-4">
              South Asian Fitness provides AI-powered nutrition tracking and meal
              planning tools tailored for South Asian cuisine. The Service includes:
            </p>
            <ul className="mt-3 list-disc pl-5 space-y-2">
              <li>
                Personalized calorie and macronutrient calculations using the
                Mifflin-St Jeor equation.
              </li>
              <li>
                AI-generated meal plans and workout routines.
              </li>
              <li>
                A searchable food library of 200+ South Asian dishes with macro data.
              </li>
              <li>
                Progress tracking and visual analytics.
              </li>
              <li>
                Saved meal plans and workout archives.
              </li>
            </ul>
            <p className="mt-4 font-medium text-stone-800">
              Health Disclaimer: The nutrition information, meal plans, and workout
              routines provided through the Service are for general informational and
              educational purposes only. They are not intended as medical advice,
              diagnosis, or treatment. Always consult a qualified healthcare provider
              or registered dietitian before making significant changes to your diet
              or exercise routine.
            </p>
          </section>

          {/* ── 3. User Accounts & Security ────────────────────────── */}
          <section>
            <h2 className="text-xl font-semibold text-stone-900">
              3. User Accounts &amp; Security
            </h2>
            <div className="mt-4 space-y-3">
              <p>
                To use certain features, you must create an account. You may register
                using your email and password or via Google OAuth authentication.
              </p>
              <p>
                <strong className="text-stone-900">Account responsibilities:</strong>{" "}
                You are responsible for maintaining the confidentiality of your account
                credentials and for all activity that occurs under your account. You
                agree to:
              </p>
              <ul className="list-disc pl-5 space-y-2">
                <li>
                  Provide accurate, current, and complete information during
                  registration.
                </li>
                <li>
                  Maintain and update your information to keep it accurate.
                </li>
                <li>
                  Notify us immediately of any unauthorized use of your account.
                </li>
                <li>
                  Not share your account credentials with any third party.
                </li>
                <li>
                  Not create more than one account per person.
                </li>
              </ul>
              <p>
                We reserve the right to suspend or terminate accounts that violate
                these Terms.
              </p>
            </div>
          </section>

          {/* ── 4. Subscriptions & Billing ─────────────────────────── */}
          <section>
            <h2 className="text-xl font-semibold text-stone-900">
              4. Subscriptions &amp; Billing
            </h2>
            <div className="mt-4 space-y-3">
              <p>
                The Service offers both free and paid (&quot;Pro&quot;) subscription tiers.
              </p>
              <p>
                <strong className="text-stone-900">Free Tier:</strong> Includes access
                to the food library, basic macro calculations, and limited AI
                generations.
              </p>
              <p>
                <strong className="text-stone-900">Pro Tier:</strong> Includes
                unlimited AI meal plan and workout generation, advanced customization,
                and priority features. Pro subscriptions are billed through{" "}
                <a
                  href="https://www.lemonsqueezy.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-emerald-600 underline underline-offset-2 hover:text-emerald-700"
                >
                  Lemon Squeezy
                </a>
                .
              </p>
              <p>
                <strong className="text-stone-900">Payment terms:</strong>
              </p>
              <ul className="list-disc pl-5 space-y-2">
                <li>
                  All payments are processed securely by Lemon Squeezy. We do not
                  store your credit card information.
                </li>
                <li>
                  Subscription fees are charged on a recurring basis (monthly or
                  annually, depending on your selected plan).
                </li>
                <li>
                  You may cancel your subscription at any time through the Lemon
                  Squeezy customer portal. Cancellation takes effect at the end of
                  your current billing period — we do not provide partial refunds for
                  unused time.
                </li>
                <li>
                  We reserve the right to change subscription pricing with 30 days&apos;
                  advance notice. Price changes will apply at your next billing cycle.
                </li>
              </ul>
              <p>
                All subscription terms are also subject to{" "}
                <a
                  href="https://www.lemonsqueezy.com/terms"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-emerald-600 underline underline-offset-2 hover:text-emerald-700"
                >
                  Lemon Squeezy&apos;s Terms of Service
                </a>
                .
              </p>
            </div>
          </section>

          {/* ── 5. Acceptable Use ──────────────────────────────────── */}
          <section>
            <h2 className="text-xl font-semibold text-stone-900">
              5. Acceptable Use
            </h2>
            <p className="mt-4">You agree not to:</p>
            <ul className="mt-3 list-disc pl-5 space-y-2">
              <li>
                Use the Service for any unlawful purpose or in violation of any
                applicable laws.
              </li>
              <li>
                Attempt to gain unauthorized access to any part of the Service,
                other accounts, or connected systems.
              </li>
              <li>
                Use automated tools (bots, scrapers) to access or interact with
                the Service, except for standard search engine crawlers.
              </li>
              <li>
                Reverse engineer, decompile, or disassemble any part of the
                Service.
              </li>
              <li>
                Resell, redistribute, or commercially exploit the AI-generated
                content from the Service without written permission.
              </li>
              <li>
                Upload or transmit viruses, malware, or any harmful code.
              </li>
              <li>
                Impersonate another person or misrepresent your affiliation with
                any person or entity.
              </li>
            </ul>
          </section>

          {/* ── 6. Intellectual Property ───────────────────────────── */}
          <section>
            <h2 className="text-xl font-semibold text-stone-900">
              6. Intellectual Property
            </h2>
            <p className="mt-4">
              The Service and its original content, features, functionality, and design
              are owned by South Asian Fitness and are protected by international
              copyright, trademark, patent, trade secret, and other intellectual
              property laws.
            </p>
            <p className="mt-3">
              You retain ownership of any data you input into the Service. By using the
              Service, you grant us a limited, non-exclusive license to process your
              data solely for the purpose of providing the Service to you.
            </p>
          </section>

          {/* ── 7. Termination ─────────────────────────────────────── */}
          <section>
            <h2 className="text-xl font-semibold text-stone-900">
              7. Termination
            </h2>
            <div className="mt-4 space-y-3">
              <p>
                <strong className="text-stone-900">By you:</strong> You may delete your
                account at any time from the Settings page. Deleting your account
                permanently removes your profile data, saved plans, and progress
                history.
              </p>
              <p>
                <strong className="text-stone-900">By us:</strong> We may suspend or
                terminate your account immediately if you violate these Terms, engage
                in fraudulent or abusive behavior, or if required by law.
              </p>
              <p>
                Upon termination, your right to use the Service ceases immediately.
                We will retain your data for up to 30 days to allow for account
                recovery, after which it will be permanently deleted.
              </p>
            </div>
          </section>

          {/* ── 8. Limitation of Liability ─────────────────────────── */}
          <section>
            <h2 className="text-xl font-semibold text-stone-900">
              8. Limitation of Liability
            </h2>
            <div className="mt-4 space-y-3">
              <p>
                THE SERVICE IS PROVIDED &quot;AS IS&quot; AND &quot;AS AVAILABLE&quot; WITHOUT
                WARRANTIES OF ANY KIND, WHETHER EXPRESS OR IMPLIED, INCLUDING BUT
                NOT LIMITED TO IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
                PARTICULAR PURPOSE, AND NON-INFRINGEMENT.
              </p>
              <p>
                In no event shall South Asian Fitness, its directors, employees,
                partners, agents, suppliers, or affiliates be liable for any
                indirect, incidental, special, consequential, or punitive damages,
                including without limitation, loss of profits, data, use, goodwill,
                or other intangible losses, resulting from:
              </p>
              <ul className="list-disc pl-5 space-y-2">
                <li>
                  Your access to or use of or inability to access or use the
                  Service.
                </li>
                <li>
                  Any conduct or content of any third party on the Service.
                </li>
                <li>
                  Any content obtained from the Service.
                </li>
                <li>
                  Unauthorized access, use, or alteration of your transmissions
                  or content.
                </li>
              </ul>
              <p>
                To the maximum extent permitted by applicable law, our total
                aggregate liability shall not exceed the greater of (a) the amount
                you paid us in the twelve (12) months preceding the claim, or (b)
                one hundred US dollars ($100).
              </p>
            </div>
          </section>

          {/* ── 9. Indemnification ─────────────────────────────────── */}
          <section>
            <h2 className="text-xl font-semibold text-stone-900">
              9. Indemnification
            </h2>
            <p className="mt-4">
              You agree to defend, indemnify, and hold harmless South Asian Fitness
              and its officers, directors, employees, contractors, agents, licensors,
              and suppliers from and against any claims, actions, demands, liabilities,
              and settlements, including reasonable legal and accounting fees, resulting
              from or alleged to result from your violation of these Terms or your use
              of the Service.
            </p>
          </section>

          {/* ── 10. Changes to These Terms ─────────────────────────── */}
          <section>
            <h2 className="text-xl font-semibold text-stone-900">
              10. Changes to These Terms
            </h2>
            <p className="mt-4">
              We reserve the right to modify these Terms at any time. We will notify
              you of material changes by posting the updated Terms on this page with a
              revised &quot;Last updated&quot; date. Continued use of the Service after changes
              are posted constitutes acceptance of the updated Terms.
            </p>
          </section>

          {/* ── 11. Governing Law ──────────────────────────────────── */}
          <section>
            <h2 className="text-xl font-semibold text-stone-900">
              11. Governing Law
            </h2>
            <p className="mt-4">
              These Terms shall be governed by and construed in accordance with the
              laws of the United States, without regard to its conflict of law
              provisions. Any disputes arising under these Terms shall be resolved in
              the competent courts of the United States.
            </p>
          </section>

          {/* ── 12. Contact ─────────────────────────────────────────── */}
          <section>
            <h2 className="text-xl font-semibold text-stone-900">
              12. Contact Us
            </h2>
            <p className="mt-4">
              If you have any questions about these Terms, please contact us:
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
