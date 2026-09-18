import type { NextConfig } from "next";

const config: NextConfig = {
  // Le moteur tourne dans un ouvrier Python séparé : rien de lourd ici.
  experimental: { serverActions: { bodySizeLimit: "2mb" } },
};

export default config;
