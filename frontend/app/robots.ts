import type { MetadataRoute } from "next";

// Sitemap URL uses the canonical origin (www) — Vercel's primary domain.
// Pointing crawlers at apex URLs just sends them through a 308 redirect.
export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
        disallow: ["/dashboard", "/api/", "/auth/"],
      },
    ],
    sitemap: "https://www.southasianfitness.com/sitemap.xml",
  };
}
