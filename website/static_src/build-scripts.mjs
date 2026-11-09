import { build } from "esbuild";

const options = {
  entryPoints: ["src/animations.mjs"],
  outfile: "../static/website/js/dist/animations.js",
  bundle: true,
  format: "iife",
  target: "es2020",
  minify: true,
  legalComments: "linked",
  define: { "process.env.NODE_ENV": '"production"' },
  banner: { js: "/*! Motion mini (MIT). See website/static/vendor/motion/LICENSE.txt. */" },
  logLevel: "info",
};

if (process.argv.includes("--watch")) {
  const { context } = await import("esbuild");
  const ctx = await context(options);
  await ctx.watch();
} else {
  await build(options);
}
