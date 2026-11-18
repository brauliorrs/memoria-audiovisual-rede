import type { NextConfig } from "next";

const config: NextConfig = {
  // Phase 1: no runtime database, tokens or paid server functions.
  // The output can run on Vercel or a static host. Remove "export" only
  // after the scientific publication and database authority gates pass.
  output: "export",
  trailingSlash: true,
  reactStrictMode: true,
};
export default config;
