Motion mini
===========

Website: https://motion.dev/
Documentation: https://motion.dev/docs/animate
Source: https://github.com/motiondivision/motion
Version: motion 14.11.1 (exact versions in website/static_src/package-lock.json)
License: MIT; notices retained in LICENSE.txt.

Only the motion/mini animate entry is bundled with the landing-page reveal
controller. No React runtime or full hybrid animate entry is shipped. The npm
packages are build-time dependencies; the output is a local, self-contained
classic browser script, not a CDN request or module-loader dependency.

Build from website/static_src with npm ci && npm run build. Generated files under
website/static/website/js/dist/ are ignored and must be built before collectstatic.

The advertised 3.2KB refers to the library's mini implementation, not the complete
application bundle. Measure the generated file and its compressed size after
building; application logic and library versions affect the result.
