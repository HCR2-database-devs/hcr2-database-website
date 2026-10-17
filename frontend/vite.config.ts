import { fileURLToPath } from "node:url";

import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

const repoRoot = fileURLToPath(new URL("..", import.meta.url));
const sharedDir = fileURLToPath(new URL("../shared", import.meta.url));

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const backendTarget = env.VITE_PROXY_TARGET ?? "http://127.0.0.1:8000";

  return {
    plugins: [react()],
    resolve: {
      alias: {
        // Country data is shared with the backend so the two cannot drift.
        // See shared/countries.json.
        "@shared": sharedDir
      }
    },
    server: {
      port: 5173,
      // Allow serving files from shared/, which lives outside this package.
      fs: {
        allow: [repoRoot]
      },
      proxy: {
        "/api": backendTarget,
        "/auth": backendTarget,
        "/health": backendTarget
      }
    }
  };
});