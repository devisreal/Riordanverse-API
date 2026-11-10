import { copyFile, mkdir, readFile, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";

// Copy only the pinned runtime assets, not Swagger's sample Petstore initializer.
const source = new URL("./node_modules/swagger-ui-dist/", import.meta.url);
const destination = new URL("../static/vendor/swagger-ui/dist/", import.meta.url);
const manifest = JSON.parse(await readFile(new URL("package.json", source), "utf8"));
const own = JSON.parse(await readFile(new URL("package.json", import.meta.url), "utf8"));
if (manifest.version !== own.devDependencies["swagger-ui-dist"]) {
  throw new Error("Swagger UI version differs from the pinned dependency; run npm ci.");
}
await mkdir(destination, { recursive: true });
for (const name of [
  "swagger-ui.css",
  "swagger-ui-bundle.js",
  "swagger-ui-bundle.js.LICENSE.txt",
  "LICENSE",
  "NOTICE",
]) {
  if (name === "swagger-ui.css") {
    // Source maps are not distributed; keep collectstatic's manifest pass valid.
    const css = await readFile(new URL(name, source), "utf8");
    const runtimeCss = css.replace(/\/\*# sourceMappingURL=swagger-ui\.css\.map\s*\*\/\s*$/, "");
    // Vendor layout beats Preflight, while the site's Tailwind utilities can theme it.
    await writeFile(new URL(name, destination),
      `@layer theme, base, swagger, components, utilities;\n@layer swagger {\n${runtimeCss}\n}\n`);
  } else {
    await copyFile(new URL(name, source), new URL(name, destination));
  }
}
console.log(`Copied Swagger UI ${manifest.version} to ${fileURLToPath(destination)}`);
