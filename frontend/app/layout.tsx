import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono, Playfair_Display } from "next/font/google";
import { ThemeProvider } from "next-themes";

import "./globals.css";
import { LenisProvider } from "@/components/lenis-provider";
// TEMPORARILY DISABLED — PostHog analytics paused (see provider POSTHOG_ENABLED flag).
// import { PostHogProvider } from "@/components/providers/posthog-provider";

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
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#FAFAF9" },
    { media: "(prefers-color-scheme: dark)", color: "#09090B" },
  ],
  width: "device-width",
  initialScale: 1,
};

const SITE_URL = "https://southasianfitness.com";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: "South Asian Fitness | Custom Workouts & Cultural Nutrition",
    template: "%s | South Asian Fitness",
  },
  description:
    "The world's first AI-powered nutrition platform built for South Asian cuisine. " +
    "Track macros for Biryani, Daal, Karahi and 200+ cultural dishes. " +
    "Personalized meal plans, workout routines, and macro targets — all free.",
  keywords: [
    "South Asian fitness",
    "Indian meal plan",
    "Pakistani diet",
    "cultural nutrition tracker",
    "Biryani macros",
    "AI meal planner",
    "Desi fitness",
    "macro tracker",
  ],
  authors: [{ name: "South Asian Fitness" }],
  creator: "South Asian Fitness",
  openGraph: {
    type: "website",
    locale: "en_US",
    url: SITE_URL,
    siteName: "South Asian Fitness",
    title: "South Asian Fitness | Custom Workouts & Cultural Nutrition",
    description:
      "AI-powered nutrition tracking for South Asian cuisine. " +
      "200+ cultural dishes, personalized macros, and smart meal plans.",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "South Asian Fitness — AI-powered cultural nutrition platform",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "South Asian Fitness | Custom Workouts & Cultural Nutrition",
    description:
      "AI-powered nutrition tracking for South Asian cuisine. 200+ cultural dishes, personalized macros, and smart meal plans.",
    images: ["/og-image.png"],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  alternates: {
    canonical: SITE_URL,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={`${geistSans.variable} ${geistMono.variable} ${playfair.variable} h-full antialiased`}
    >
      <body className="min-h-full bg-background text-foreground">
        {/* TEMPORARILY DISABLED — PostHog analytics paused. */}
        {/* <PostHogProvider> */}
        <ThemeProvider
            attribute="class"
            defaultTheme="light"
            enableSystem
            disableTransitionOnChange={false}
          >
            <a
              href="#main-content"
              className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:m-2 focus:rounded-lg focus:bg-white focus:px-4 focus:py-2 focus:text-stone-900 focus:outline-none focus:shadow-lg dark:focus:bg-zinc-900 dark:focus:text-zinc-100"
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
          </ThemeProvider>
          {/* </PostHogProvider> — TEMPORARILY DISABLED */}
      </body>
    </html>
  );
}
