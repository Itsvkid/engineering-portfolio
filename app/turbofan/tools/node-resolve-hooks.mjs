// Resolve extensionless relative imports to .js so the atlas modules load in plain Node.
import { existsSync } from "node:fs";
import { fileURLToPath, pathToFileURL } from "node:url";
export async function resolve(specifier, context, next) {
  if (specifier.startsWith("./") || specifier.startsWith("../")) {
    const base = new URL(specifier, context.parentURL);
    const p = fileURLToPath(base);
    if (!/\.[a-z]+$/.test(p) && existsSync(p + ".js")) return next(pathToFileURL(p + ".js").href, context);
  }
  return next(specifier, context);
}
