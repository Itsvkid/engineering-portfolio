import nextCoreWebVitals from "eslint-config-next/core-web-vitals";

/**
 * Flat config. `eslint-config-next` ships flat configs directly as of 16.x —
 * no FlatCompat shim needed (and the shim breaks under ESLint 10).
 */
const eslintConfig = [
  { ignores: [".next/**", "node_modules/**", ".vercel/**", "next-env.d.ts"] },
  ...nextCoreWebVitals,
];

export default eslintConfig;
