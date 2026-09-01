import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Privacy Policy",
  description: "Privacy Policy for South Asian Fitness.",
};

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-[#09090b]">
      <div className="mx-auto max-w-3xl px-6 py-12">
        <Link href="/" className="text-sm font-medium text-emerald-700 hover:text-emerald-800">
          ← Back to South Asian Fitness
        </Link>

        <h1 className="mt-6 text-3xl font-bold text-white">Privacy Policy</h1>
        <p className="mt-2 text-sm text-zinc-500">Last updated: August 2026</p>

        <div className="mt-8 space-y-6 text-zinc-300">
          <section>
            <h2 className="text-xl font-semibold text-white">Information We Collect</h2>
            <p className="mt-2">
              When you create an account, we collect your email address and display name.
              Through onboarding, you may provide profile information including age, height,
              weight, activity level, fitness goals, dietary preferences, and budget information.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white">How We Use Your Information</h2>
            <p className="mt-2">
              Your profile information is used solely to calculate personalized nutrition
              targets and generate meal plans. We do not sell, share, or monetize your personal data.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white">Data Storage</h2>
            <p className="mt-2">
              Your data is stored securely in our database. We use industry-standard security
              measures including encrypted passwords, secure session cookies, and CSRF protection.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white">Contact</h2>
            <p className="mt-2">
              For privacy-related questions, please contact us at{" "}
              <span className="font-medium text-white">[CONTACT EMAIL TO BE ADDED]</span>.
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
