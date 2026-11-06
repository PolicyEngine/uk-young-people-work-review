/** @type {import('next').NextConfig} */
// No basePath, rewrites or deploy target yet: nothing deploys from this
// repository (see .github/workflows/deploy.yml). Set basePath in
// src/lib/basePath.json and here together when the team picks a route.
import basePathConfig from "./src/lib/basePath.json" with { type: "json" };

const { basePath } = basePathConfig;

const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ["@policyengine/ui-kit"],
  ...(basePath ? { basePath } : {}),
  // noindex as a header too, so `next start` and any host send it, not
  // only the meta tag (drill G4 checks both). Removed in the publication
  // flip (docs/RUNBOOK.md), with the meta tag and the CI greps.
  async headers() {
    return [{ source: "/:path*", headers: [{ key: "X-Robots-Tag", value: "noindex, nofollow" }] }];
  },
};

export default nextConfig;
