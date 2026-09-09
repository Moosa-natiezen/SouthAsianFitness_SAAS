import type { MetadataRoute } from "next";

// Canonical origin MUST match Vercel's primary domain (www). Apex URLs
// 308-redirect to www, and Google flags redirecting URLs as "Page with
// redirect" in Search Console instead of indexing them directly.
const BASE_URL = "https://www.southasianfitness.com";

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();

  // Only crawlable, indexable public routes. /pricing is an on-page anchor
  // of the homepage (no standalone route), and /auth/* is disallowed in
  // robots.ts — neither belongs in a sitemap.
  return [
    {
      url: BASE_URL,
      lastModified: now,
      changeFrequency: "weekly",
      priority: 1,
    },
    {
      url: `${BASE_URL}/privacy`,
      lastModified: now,
      changeFrequency: "yearly",
      priority: 0.2,
    },
    {
      url: `${BASE_URL}/terms`,
      lastModified: now,
      changeFrequency: "yearly",
      priority: 0.2,
    },
  ];
}
