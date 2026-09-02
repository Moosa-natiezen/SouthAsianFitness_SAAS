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
  themeColor: "#FAF9F6",
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
      <body className="min-h-full bg-[#FAF9F6] text-[#1C1917]">
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:m-2 focus:rounded-lg focus:bg-white focus:px-4 focus:py-2 focus:text-[#05050A] focus:outline-none"
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
