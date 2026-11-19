import type { NextConfig } from "next";
import { execFileSync } from "node:child_process";
import { join } from "node:path";

// Fail closed even if the Vercel Build Command bypasses npm run build.
// Next.js always evaluates this configuration before producing static HTML.
execFileSync(process.execPath, [join(process.cwd(), "scripts", "verify-scientific-snapshot.cjs")], {
  stdio: "inherit",
});


const config: NextConfig = {
  // Phase 1: no runtime database, tokens or paid server functions.
  // The output can run on Vercel or a static host. Remove "export" only
  // after the scientific publication and database authority gates pass.
  output: "export",
  trailingSlash: true,
  reactStrictMode: true,
};
export default config;
