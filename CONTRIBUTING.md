# Contributing

Thanks for helping improve the Riordanverse API. For API usage, start with the
[README](README.md#use-the-api) and [API reference](API.md). Production hosting
instructions are in [DEPLOYMENT.md](DEPLOYMENT.md).

## Development setup

Follow [Setup](README.md#setup), [Database setup](README.md#database-setup), and
[Run the project](README.md#run-the-project) in the README. Use Python 3.14+,
PostgreSQL, uv, and Node.js 22+ with npm for website assets. Redis is recommended
for shared caching and quotas. Development keeps API-key authentication enabled.
Docker is optional; local development does not require building an image.

## Dependency management

`pyproject.toml` declares direct dependencies and development tools; `uv.lock`
pins direct and transitive dependencies. Install the locked environment with
`uv sync --locked`. `requirements.txt` exports the same environment, including
the development group. After dependency changes, update the lock and regenerate
rather than deleting transitive dependencies manually:

```bash
uv lock
uv export --locked --no-hashes --no-annotate --no-emit-project --no-header --output-file requirements.txt
```

Frontend dependencies are locked in `website/static_src/package-lock.json`.
Use `npm ci --prefix website/static_src` for a reproducible install.

## Website and Tailwind workflow

The public homepage at `/` uses Django templates in `website/templates/website/`.
`home.html` extends `base.html`, which provides `title`, `extra_head`, `content`,
and `extra_js` blocks. It renders a static, database-independent landing page with
links to the real API directory and documentation. Code examples are illustrative,
not live requests; they use the current request origin and the API's actual header,
fields, and key-request contract. API endpoints remain JSON-only.

The responsive page includes a top mobile menu, request/response tabs, clipboard
controls with a manual-copy fallback, and reduced-motion support. There is no
bottom mobile bar. A sun/moon button switches themes at every viewport, with a
Light/Dark selector inside the mobile menu. The tablet navigation uses compact
spacing and an “Explore API” label to accommodate the control. JavaScript defaults
to light mode and honors a saved `localStorage.theme` value of `light` or `dark`;
without JavaScript, the OS color preference applies and theme controls stay hidden.
Explicit `html.light`/`html.dark` classes take precedence on initial load. The local
`website/static/website/js/theme.js` resolves the theme before CSS loads and saves
later selections when storage is available; controls still work when it is blocked.
The hero and section/card groups use locally bundled Motion mini for restrained
14px, 400ms slide-up reveals. Every card grid (including hero overview stats) uses
an 80ms stagger in DOM order, with a distinct delay for every card; separate
observer callbacks do not reset its position. Non-card entrances retain their
150ms stagger cap. Each target reveals only once per page load; scrolling back, resizing, theme changes, or returning through
browser history do not replay it. A reload resets the sequence. Pending content is
not hidden by CSS, so it remains readable without JavaScript or the animation
bundle. Reduced-motion users get a static page; enabling that preference during a
reveal cancels effects immediately and keeps the page static until reload. Focusing
a control also cancels/skips its containing reveal. Third-party notices are in
`website/static/vendor/motion/`. The documented 3.2KB mini-library figure is not the
size of our complete animation bundle.

Run the dependency-free theme/reveal behavior tests with
`node --test website/tests_js/*.test.mjs`.

Fonts, Lucide SVGs, background images, and archive images are served locally; no
runtime font, icon, Tailwind, or Motion CDN is required. The landing uses WebP backgrounds
and lore images; superseded background/Camp/Olympus JPEGs are not shipped. Visible
source credits appear on the three lore cards. The cropped trident photograph also links its CC BY-SA 3.0 license. Font
licenses, image sources, processing details, and asset checksums are documented
under `website/static/website/`. Credits and provenance do **not** grant rights to
the Camp/Olympus or original Stitch images; their redistribution rights remain
unverified.

Lore cards use committed 256/384/512/768px WebP derivatives plus the original
1000px source in `srcset`. The `sizes` attribute mirrors the 244px mobile strip
and three-column desktop layout; update it if that layout changes. Regenerate
derivatives with `sh website/static_src/build-lore-images.sh` when changing a
source image (requires the optional libwebp `cwebp` tool). Normal npm/Docker
builds use the committed images and do not need an image encoder.

Author layout, spacing, typography, borders, and responsive states with Tailwind
utilities in the Django/Cotton templates. `website/static_src/src/styles.css` uses
Tailwind v4's CSS-first `@theme` configuration for fonts, breakpoints, and semantic
color utilities such as `bg-surface` and `text-accent`. Its remaining custom CSS is
limited to shared theme/global defaults, generated syntax tokens, accessibility,
and progressive-enhancement behavior—not a parallel component stylesheet.

The current frontend toolchain uses **Node.js 22+ and npm**. After `uv sync` and
configuring `.env`, install the locked frontend dependencies from the project root:

```bash
npm ci --prefix website/static_src
```

Start Django, the Tailwind CSS watcher, and the Motion script watcher together:

```bash
DJANGO_SETTINGS_MODULE=config.settings.development uv run python manage.py tailwind dev
```

This uses `Procfile.tailwind` through Honcho. Alternatively, run
`uv run python manage.py runserver` and `uv run python manage.py tailwind start`
in separate terminals; both default to development settings. In that case, run
`npm run dev:scripts --prefix website/static_src` in another terminal for animation
script changes. Automatic browser reload is not configured.

For deployment, install frontend dependencies including dev dependencies (the CSS
and JavaScript build tools), then compile CSS, the local Motion bundle, and the
pinned Swagger UI assets **before** collecting static files:

```bash
npm ci --include=dev --prefix website/static_src
DJANGO_SETTINGS_MODULE=config.settings.production uv run python manage.py tailwind build
uv run python manage.py collectstatic --noinput --settings=config.settings.production
```

Production commands require the production environment variables and dependencies
to be configured. Generated CSS at `website/static/css/dist/styles.css` and the
script at `website/static/website/js/dist/animations.js`, along with Swagger's
`website/static/vendor/swagger-ui/dist/` directory, are Git-ignored, so every
fresh checkout or deployment needs a build. The production
server does not run the watcher or `Procfile.tailwind`.

Format and check templates with djLint, and Python with Ruff:

```bash
uv run djlint website/templates/ --reformat
uv run djlint website/templates/ --check --lint
uv run ruff format .
uv run ruff check .
uv run ruff format --check .
git diff --check
```

The test suites inspect built CSS, JavaScript, and their static assets, so build
once before running tests on a fresh checkout. CI builds all assets before database tests
and checks template formatting/linting. Narrow `H026` suppressions apply only to
Cotton variable declarations, where empty defaults are component metadata rather
than empty rendered HTML attributes.

Prettier and Bun are not configured.

### Cotton components and Lucide icons

Django Cotton is installed through `uv sync` and registered in `INSTALLED_APPS`.
It automatically configures the template loader; components live in
`website/templates/cotton/`, while page templates stay in
`website/templates/website/`. Tailwind's existing source pattern scans both.

Lucide icons are local, server-rendered Cotton SVG components: no icon font,
JavaScript initialization, runtime CDN, or npm icon dependency is needed.

```html
<!-- Decorative beside visible text: hidden from assistive technology by default. -->
<c-icons.book-open class="size-5 text-emerald-500" />

<!-- Standalone meaningful icon: label supplies its accessible name. -->
<c-icons.search label="Search" size="20" stroke-width="1.5" />

<!-- Icon-only controls need a name on the control, not just on its icon. -->
<button type="button" aria-label="Open navigation">
  <c-icons.menu />
</button>
```

Available icons include `arrow-right`, `book-open`, `code`, `copy`, `external-link`,
`menu`, `search`, and `x`, plus the landing-page subset listed in
`website/static/vendor/lucide/README.txt`. For example, `<c-icons.book-open />` resolves to
`website/templates/cotton/icons/book_open.html`. Each delegates to `icons/base.html`
for `currentColor`, size, stroke width, and accessibility behavior. Additional
attributes such as `class` and `data-*` are forwarded to the SVG. Interactive
behavior (for example, opening a menu) is separate from rendering an icon.

The paths are vendored from **lucide-static 1.70.0**. Its full ISC license and
Feather-derived MIT notices are preserved in
`website/static/vendor/lucide/LICENSE.txt`, alongside source/version information
in `README.txt`. These third-party assets retain their upstream licenses. When
adding an icon, copy its paths from a pinned official Lucide release into a
Cotton wrapper, retain the license notices, and rebuild Tailwind CSS.

## Choose primary images in Django admin

Staff with image and gallery-link change permissions can open **Images → Images → Choose primary images**, select an entity, review its linked thumbnails, and set or clear that gallery's primary image. The picker currently displays all images linked to one entity without filtering or pagination; a searchable entity selector is planned for a later phase.

## Seed canonical data

Run migrations first. Use the master command for a one-command setup, or run
the individual commands below if you prefer step-by-step control. All seed
commands are idempotent; use them only against the database you intend to
populate.

### One-command setup

```bash
uv run python manage.py seed_all --settings=config.settings.development
```

`seed_all` runs every canonical seed command in dependency order and stops if
a command fails. You can safely rerun it after correcting a seed issue.

### Step-by-step setup

Run these commands in order if you want to seed individual datasets or inspect
each command's output:

```bash
export DJANGO_SETTINGS_MODULE=config.settings.development
uv run python manage.py seed_books
uv run python manage.py seed_gods
uv run python manage.py seed_titans
uv run python manage.py seed_characters
uv run python manage.py seed_items
uv run python manage.py seed_monsters
uv run python manage.py seed_creatures
uv run python manage.py seed_divine_relationships
uv run python manage.py seed_book_relationships
uv run python manage.py seed_powers
uv run python manage.py seed_locations
uv run python manage.py seed_cabins
uv run python manage.py seed_factions
uv run python manage.py seed_prophecies
uv run python manage.py seed_events
uv run python manage.py seed_quests
uv run python manage.py seed_monster_defeats
uv run python manage.py seed_images
```

Curated primary images are recorded per entity in
`data/image_gallery_overrides.json` using `primary_file_title`. Running
`seed_images` (also included in `seed_all`) restores these choices on a fresh
or existing database and clears competing primary flags. Admin changes remain
database-only until the corresponding seed override is updated.

The current JSON seeds contain 12 books, 96 characters, 41 gods, 23 Titans, 29 monsters, 18 creatures, 50 weapons, 27 locations, 12 quests, 11 prophecies, 23 events, 20 cabins, 8 factions, 383 family relationship records, 12 Book cast relationship records, 27 Monster defeat records, 14 Powers, and 2,787 wiki image references from 330 entity pages (2,651 distinct `(url, source_url)` Image records after seeding; 15 pages have no image candidates). Wiki image records use `source_type=wiki`; license fields intentionally remain null. Wiki provenance does not establish permission or grant a license. These are seed-file record counts; unresolved typed entity references are warned about and skipped by the relevant seed command.

## Tests

```bash
uv run python manage.py test --settings=config.settings.test
```

The default test suite uses SQLite. CI also runs the full suite against PostgreSQL using `config.settings.test_postgresql`; locally, configure `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, and `DB_PORT`, then run:

```bash
uv run python manage.py test --settings=config.settings.test_postgresql
```

OpenAPI generation is configured with `drf-spectacular`; validate it with `DJANGO_SETTINGS_MODULE=config.settings.development uv run python manage.py spectacular --validate`. The `/api/v1/` directory, schema, and documentation pages are public; API resource endpoints continue to require `X-API-Key`.

## Submitting a change

- Create a focused branch and describe the problem and solution in your PR.
- Use [the pull-request template](.github/pull_request_template.md) and target
  `develop` for normal development work.
- Keep secrets and local `.env` files out of Git. Do not commit generated static
  files, database dumps, or personal API keys.
- Add regression tests and update the API reference if the public contract changes.
- For schema changes, include reviewed migrations and check reversibility.
- Distinguish lore corrections from schema changes; keep source provenance and
  third-party rights intact. Image attribution does not establish permission.
- Preserve no-JavaScript readability, keyboard access, reduced-motion support,
  and the existing Tailwind/Cotton conventions for website changes.
- Do not migrate, seed, or delete a shared database as part of testing. Use the
  dedicated test settings and inspect the intended database before manual seeds.
