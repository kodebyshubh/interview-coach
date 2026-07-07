import type { Config } from "tailwindcss";

// Theme is configured via @theme in globals.css (Tailwind v4).
// This file retained only for plugin/content overrides if needed.
const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
};

export default config;
