import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono, Playfair_Display } from "next/font/google";

import "./globals.css";
import { LenisProvider } from "@/components/lenis-provider";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const playfair = Playfair_Display({
  variable: "--font-playfair",
  subsets: ["latin"],
  display: "swap",
});

export const viewport: Viewport = {
  themeColor: "#09090b",
  width: "device-width",
  initialScale: 1,
};

export const metadata: Metadata = {
  title: {
    default: "South Asian Fitness — Personalized Meal Planning",
    template: "%s — South Asian Fitness",
  },
  description:
    "Personalized, budget-friendly South Asian diet and fitness planning. " +
    "Get meal plans built around the foods, meals, and budgets that fit your life.",
  metadataBase: new URL(
    process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000",
  ),
  openGraph: {
    type: "website",
    locale: "en_US",
    siteName: "South Asian Fitness",
    title: "South Asian Fitness — Personalized Meal Planning",
    description:
      "Personalized, budget-friendly South Asian diet and fitness planning.",
  },
  robots: { index: true, follow: true },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} ${playfair.variable} dark h-full antialiased`}
    >
      <body className="min-h-full bg-[#09090b] text-zinc-100">
        {/* Ambient brand glow orbs */}
        <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden">
          <div className="glow-orb-brand absolute -left-40 -top-40 h-96 w-96" />
          <div className="glow-orb-brand absolute -bottom-40 -right-40 h-96 w-96" />
        </div>
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:m-2 focus:rounded-lg focus:bg-zinc-800 focus:px-4 focus:py-2 focus:text-white focus:outline-none"
        >
          Skip to content
        </a>
        <LenisProvider>
          <div id="main-content" className="flex-1 flex flex-col relative">
              <div className="relative z-10">
              {children}
            </div>
          </div>
        </LenisProvider>
      </body>
    </html>
  );
}
