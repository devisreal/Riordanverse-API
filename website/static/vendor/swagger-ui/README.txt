Swagger UI — local documentation runtime

Upstream: https://github.com/swagger-api/swagger-ui
Distribution: https://www.npmjs.com/package/swagger-ui-dist
Pinned version: 5.34.1 (Apache-2.0)

The exact version is recorded in website/static_src/package.json and its npm lock.
Run npm ci --include=dev --prefix website/static_src, then
npm run build --prefix website/static_src before collectstatic or deployment.
The development Tailwind watcher also copies the vendor assets on startup.

build-swagger.mjs verifies the installed version and copies only:
- dist/swagger-ui.css
- dist/swagger-ui-bundle.js
- dist/swagger-ui-bundle.js.LICENSE.txt (bundled third-party notices)
- dist/LICENSE
- dist/NOTICE

The CSS's trailing sourceMappingURL comment is removed because source maps are
not distributed; this also prevents missing-map errors in manifest collectstatic.
The vendor CSS is wrapped in a cascade layer below Tailwind utilities and above
Preflight. Swagger's generated DOM is themed with scoped descendant utilities in
website/templates/cotton/swagger/panel.html, reusing the site's fonts and tokens;
there is no separate handwritten Swagger stylesheet. No executable vendor code
is changed. Generated dist/ files are ignored by Git and served by Django's
normal staticfiles pipeline, including hashed manifest URLs in production. The sample
Petstore initializer, standalone layout, telemetry package, and OAuth redirect
sample are not copied or executed. No CDN or external schema validator is used
by the customized Swagger page. The frontend package also explicitly disables
Scarf installation analytics with scarfSettings.enabled=false. ReDoc is separate
and remains unchanged.

LICENSE.txt and NOTICE.txt in this directory retain upstream license notices.
The generated bundle's adjacent LICENSE.txt file retains bundled third-party
notices. Keep those files with redistributed vendor assets. The project's scoped
MIT license does not replace upstream licenses.

The branded HTML shell uses drf-spectacular's own swagger_ui.js initializer,
including its request/response interceptors and CSRF handling. The upstream HTML
shell has no body-attribute block, so a small custom shell supplies the scoped
body class without modifying or copying Swagger's functional initializer.
