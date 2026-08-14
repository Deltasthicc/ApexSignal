import type { MetadataRoute } from "next";

// Required for `output: export` (static export / HF static Space builds) --
// without this, Next.js treats the route as dynamic and the build fails.
export const dynamic = "force-static";

export default function sitemap(): MetadataRoute.Sitemap {
  return [
    {
      url: "https://apex-signal-sigma.vercel.app/",
      lastModified: new Date(),
      changeFrequency: "weekly",
      priority: 1,
    },
  ];
}
