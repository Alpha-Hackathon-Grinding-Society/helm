import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // The dashboard reads the agent's committed ledger at request time, so the ledger
  // has to be readable from the deployed bundle rather than imported at build time.
  outputFileTracingIncludes: {
    "/**": [
      "./public/**/*",
      "./data/**/*",
      "../agent/ledger/**/*",
      "../agent/models/**/*",
      "../deployments/**/*",
      "../docs/BENCHMARK.md",
    ],
  },
};

export default nextConfig;
