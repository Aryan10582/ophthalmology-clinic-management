import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        clinic: {
          ink: "#17202a",
          muted: "#5d6d7e",
          line: "#d8e0e6",
          wash: "#f6f8fa",
          teal: "#147c72",
          mint: "#dff3ee",
          amber: "#9b6b12",
          rose: "#9f3d4a"
        }
      },
      boxShadow: {
        soft: "0 10px 30px rgba(25, 42, 62, 0.08)"
      }
    }
  },
  plugins: []
};

export default config;
