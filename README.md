# Percy Jackson Fandom API

A Django REST API for Riordanverse reference data. The implemented v1 API includes books and their typed casts, characters, gods, Titans, monsters, creatures, weapons, locations, quests, prophecies, events, cabins, factions, images, and global search. Public lore endpoints are read-only and require an API key; the API directory, key request/verification, health-check, and API documentation routes are public.

> **Status:** The versioned API, seed commands, authentication, filtering, pagination, typed relationships, and tests are implemented. OpenAPI schema, Swagger UI, and ReDoc are available at `/api/schema/`, `/api/docs/`, and `/api/redoc/`. See the [API reference](API.md) for routes, filters, response shapes, and examples.

## Features

- PostgreSQL-backed relational models; no `GenericForeignKey` for typed entity relationships.
- JSON-only API responses, including in a browser; interactive documentation remains at `/api/docs/` and `/api/redoc/`.
- Paginated list responses use `{ "data": [...], "meta": {...} }`.
- API-key authentication via `X-API-Key`, Redis caching for valid key checks, per-key throttling, and request/security logging.
- Strict choice filters and lowercase-only boolean filters; invalid values return a structured `400` response.
- `?sort=<allowed-field>[&order=asc|desc]` with endpoint-specific allowlists; `order` defaults to `asc` when omitted, and legacy `?ordering=` remains supported.
- Typed relationships in API responses: Book narrators/cast/antagonists, family graphs, quest participants/casualties, Event casualties, prophecy subjects, faction members, location controllers, and Monster defeat records.
- Image galleries for books, characters, gods, Titans, monsters, weapons, and locations, plus a paginated global image collection.
- Global search via django-watson, with a typed result for each supported entity.
- Idempotent seed commands for canonical data and relationships.

## Implemented API routes

All versioned routes are under `/api/v1/` and use trailing slashes. `GET /api/v1/` is a public, JSON-only directory of the 14 collections plus search; it returns a flat object of names to relative URLs without pagination or database/cache access. Following those links requires an API key, and search also requires `?q=<query>`. For example:

```json
{
  "books": "/api/v1/books/",
  "characters": "/api/v1/characters/",
  "gods": "/api/v1/gods/",
  "titans": "/api/v1/titans/",
  "monsters": "/api/v1/monsters/",
  "creatures": "/api/v1/creatures/",
  "weapons": "/api/v1/weapons/",
  "locations": "/api/v1/locations/",
  "quests": "/api/v1/quests/",
  "prophecies": "/api/v1/prophecies/",
  "events": "/api/v1/events/",
  "cabins": "/api/v1/cabins/",
  "factions": "/api/v1/factions/",
  "images": "/api/v1/images/",
  "search": "/api/v1/search/"
}
```

The following collections have list and slug-detail routes unless noted:

| Resource | Routes and subresources |
| --- | --- |
| Books | `/books/`, `/books/<slug>/`, `/books/<slug>/characters/`, `/books/<slug>/gods/`, `/books/<slug>/monsters/`, `/books/<slug>/locations/`, `/books/<slug>/quests/`, `/books/<slug>/images/` |
| Characters | `/characters/`, `/characters/<slug>/`, `/characters/<slug>/images/`, `/characters/<slug>/powers/`, `/characters/<slug>/weapons/`, `/characters/<slug>/quests/` |
| Gods | `/gods/`, `/gods/<slug>/`, `/gods/<slug>/images/`, `/gods/<slug>/children/`, `/gods/<slug>/weapons/` |
| Titans | `/titans/`, `/titans/<slug>/`, `/titans/<slug>/images/` |
| Monsters | `/monsters/`, `/monsters/<slug>/`, `/monsters/<slug>/images/` |
| Creatures | `/creatures/`, `/creatures/<slug>/`, `/creatures/<slug>/members/` |
| Weapons | `/weapons/`, `/weapons/<slug>/`, `/weapons/<slug>/images/` |
| Locations | `/locations/`, `/locations/<slug>/`, `/locations/<slug>/images/` |
| Quests | `/quests/`, `/quests/<slug>/`, `/quests/<slug>/participants/` |
| Prophecies and Events | `/prophecies/`, `/prophecies/<slug>/`, `/events/`, `/events/<slug>/` |
| Cabins | `/cabins/`, `/cabins/<slug>/`, `/cabins/number/<number>/`, `/cabins/<slug>/campers/` |
| Factions | `/factions/`, `/factions/<slug>/`, `/factions/<slug>/members/` |
| Images | `/images/` global collection; nested galleries are listed with their entities |
| Search | `/search/?q=<query>`; optional `type=<entity-type>` |

Public health, API-key, and documentation endpoints are outside `/api/v1/`:

- `GET /api/schema/` — OpenAPI 3 schema (YAML by default; add `?format=json` for JSON).
- `GET /api/docs/` — branded Swagger UI with shared light/dark theme controls and locally served assets.
- `GET /api/redoc/` — ReDoc.
- `GET /health/live/` — process liveness.
- `GET /health/ready/` — checks PostgreSQL readiness.
- `POST /auth/request-key/` — request a key with `consumer_name` and `email`.
- `POST /auth/verify-key/` — verify a key passed in the configured API-key header.

To revoke a key, send `POST /auth/revoke-key/` with that same key in `X-API-Key`; it revokes only the presented key and requires authentication.

Swagger UI and ReDoc list Authentication and Health first, followed by the resource groups. Versioned endpoints return JSON rather than the DRF browsable API. Normal browser requests receive JSON; requests accepting only `text/html` receive `406 Not Acceptable`, and `?format=api` is not supported. `/api/schema/` retains its YAML/JSON schema formats.

Swagger uses pinned, locally served `swagger-ui-dist` assets (see
`website/static/vendor/swagger-ui/README.txt` for version and license details).
Its theme shares the website's saved preference, while API keys entered through
Authorize remain in memory only; authorization is not persisted across reloads.
The official drf-spectacular initializer preserves CSRF and request/response
interceptors. No external schema validator is contacted. ReDoc remains unchanged.

There is no standalone family/divine-relationship or Power collection endpoint. The global `/images/` collection and typed entity galleries return image metadata and URLs; the API does not proxy or host the image bytes. Family graphs are embedded in God, Titan, Character, Monster, and Creature detail responses. Powers are embedded in Character details and available through the Character-scoped `/characters/<slug>/powers/` subresource.

## Relationship response examples

God, Titan, Character, Monster, and Creature detail responses include `type` and a nested `family` object. Each family group contains typed `{ "name", "type", "slug" }` references:

```json
{
  "type": "monster",
  "family": {
    "parents": [{"name": "Pasiphaë", "type": "character", "slug": "pasiphae"}],
    "siblings": [],
    "consorts": [],
    "children": []
  }
}
```

Book details expose typed `narrators`, `main_characters`, and `antagonists` references, while `/books/<slug>/characters/` and `/books/<slug>/gods/` list the linked characters and gods. Quest details provide typed participant and casualty references; Event details expose typed casualties and per-entity participant slug lists; Prophecy details expose typed subjects; Faction details and member subresources expose typed members. These are response relationships, not separate relationship CRUD endpoints.

## Quick start

### Requirements

- Python **3.14+**.
- PostgreSQL for the development and production settings.
- Redis is recommended for shared API-key caching and rate-limit counters. The API continues if Redis is unavailable, using PostgreSQL for key validation and process-local counters as a fallback.
- [`uv`](https://docs.astral.sh/uv/) for dependency and virtual-environment management.

### Install and configure

```bash
git clone <repo-url>
cd pj-fandom-api
uv sync
cp .env.example .env
```

`pyproject.toml` declares direct dependencies and development tools; `uv.lock` pins
both direct and transitive dependencies. `requirements.txt` is an export of that
same environment, including the development group. Regenerate it after dependency
changes rather than deleting required transitive packages by hand:

```bash
uv export --locked --no-hashes --no-annotate --no-emit-project --no-header --output-file requirements.txt
```

Configure the database and `SECRET_KEY` in `.env`. The development settings connect to PostgreSQL using `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, and `DB_PORT`. Set `REDIS_URL` to your Redis instance; the example file provides a local URL. The API-key header defaults to `X-API-Key` (`API_KEY_CUSTOM_HEADER=HTTP_X_API_KEY`).

Apply migrations, create an admin user if needed, then run the server:

```bash
uv run python manage.py migrate --settings=config.settings.development
uv run python manage.py createsuperuser --settings=config.settings.development
uv run python manage.py runserver --settings=config.settings.development
```

Development keeps API-key authentication enabled. Tests use separate SQLite settings and are not a substitute for running the server with development or production settings.

### Website and Tailwind workflow

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
while retaining the original JPEGs, with visible source credits on the three lore
cards. The cropped trident photograph also links its CC BY-SA 3.0 license. Font
licenses, image sources, processing details, and asset checksums are documented
under `website/static/website/`. Credits and provenance do **not** grant rights to
the Camp/Olympus or original Stitch images; their redistribution rights remain
unverified.

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

#### Cotton components and Lucide icons

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

### Choose primary images in Django admin

Staff with image and gallery-link change permissions can open **Images → Images → Choose primary images**, select an entity, review its linked thumbnails, and set or clear that gallery's primary image. The picker currently displays all images linked to one entity without filtering or pagination; a searchable entity selector is planned for a later phase.

### Seed canonical data

Run migrations first. Use the master command for a one-command setup, or run
the individual commands below if you prefer step-by-step control. All seed
commands are idempotent; use them only against the database you intend to
populate.

#### One-command setup

```bash
uv run python manage.py seed_all --settings=config.settings.development
```

`seed_all` runs every canonical seed command in dependency order and stops if
a command fails. You can safely rerun it after correcting a seed issue.

#### Step-by-step setup

Run these commands in order if you want to seed individual datasets or inspect
each command's output:

```bash
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

The current JSON seeds contain 12 books, 96 characters, 41 gods, 23 Titans, 29 monsters, 18 creatures, 50 weapons, 27 locations, 12 quests, 11 prophecies, 23 events, 20 cabins, 8 factions, 383 family relationship records, 12 Book cast relationship records, 27 Monster defeat records, 14 Powers, and 2,787 wiki image references from 330 entity pages (2,651 distinct `(url, source_url)` Image records after seeding; 15 pages have no image candidates). Wiki image records use `source_type=wiki`; license fields are null because the source does not expose machine-readable license metadata. These are seed-file record counts; unresolved typed entity references are warned about and skipped by the relevant seed command.

## Authentication and rate limits

Request a key (shown only once):

```bash
curl -X POST http://127.0.0.1:8000/auth/request-key/ \
  -H 'Content-Type: application/json' \
  -d '{"consumer_name":"My Fan App","email":"dev@example.com"}'
```

Use the returned key on v1 resource requests (the `/api/v1/` directory itself is public):

```bash
curl 'http://127.0.0.1:8000/api/v1/characters/?type=demigod&is_demigod=true' \
  -H 'X-API-Key: <your-key>'
```

Authenticated requests are limited to **1,000 per key per fixed one-hour window**. Responses include `RateLimit-Limit`, `RateLimit-Remaining`, and `RateLimit-Reset`; throttled responses include `Retry-After`. Key request and verification routes are separately limited to **5 requests per hour per client IP**. If Redis is down, counters are process-local and are not shared between workers. `X-Request-ID` is returned on responses for request correlation.

## Responses and query parameters

List routes use the default page size of 20, configurable by `page` and `limit` (`limit` maximum 100):

```json
{
  "data": [],
  "meta": {"total": 0, "page": 1, "limit": 20, "total_pages": 1}
}
```

Search returns `data` and `meta` containing `total`, `query`, and `type_filter`. Detail routes return a resource-specific object, not the list envelope.

Examples:

```text
/api/v1/books/?series=percy_jackson_and_the_olympians
/api/v1/books/?parent-collection=the-demigod-files
/api/v1/characters/?divine_parent=poseidon&status=alive
/api/v1/gods/?tier=olympian
/api/v1/monsters/?type=gorgon&can_reform=true
/api/v1/weapons/?type=sword&owner_character=percy-jackson
/api/v1/events/?type=battle&book=the-last-olympian
/api/v1/search/?q=riptide&type=weapon
/api/v1/characters/percy-jackson/images/?source_type=fan_art&category=portrait
/api/v1/images/?source_type=wiki&source_url=https%3A%2F%2Friordan.fandom.com%2Fwiki%2FPercy_Jackson
/api/v1/characters/?sort=name&order=asc
```

Choice values are validated; invalid choices return `400` with `code: INVALID_FILTER_VALUE` and a `valid_values` list. Boolean filters accept only lowercase `true` and `false`; other spellings return `400`. `sort` fields are validated per list endpoint; `order` defaults to `asc` when omitted, and sending `order` without `sort` is invalid. Sparse fieldsets (`fields=`) and relationship expansion (`include=`) are not implemented.

### API key verification

```bash
curl -X POST http://127.0.0.1:8000/auth/verify-key/ \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: <your-key>'
```

The response contains `valid` and `consumer_name`. API keys can be revoked by an authorized administrator or by calling `POST /auth/revoke-key/` with the same `X-API-Key`; the endpoint revokes only the presented key. Revocation clears cached validation after the database transaction commits. If Redis is unavailable, invalidation failures are logged and any stale cache entry expires by its five-minute TTL. Plaintext keys are not recoverable after creation.

## Tests

```bash
uv run python manage.py test --settings=config.settings.test
```

The default test suite uses SQLite. CI also runs the full suite against PostgreSQL using `config.settings.test_postgresql`; locally, configure `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, and `DB_PORT`, then run:

```bash
uv run python manage.py test --settings=config.settings.test_postgresql
```

OpenAPI generation is configured with `drf-spectacular`; validate it with `DJANGO_SETTINGS_MODULE=config.settings.development uv run python manage.py spectacular --validate`. The `/api/v1/` directory, schema, and documentation pages are public; API resource endpoints continue to require `X-API-Key`.

## Roadmap

- **Current v1:** implemented/testable routes and seeded Riordanverse reference data described above.
- **Future:** consider additional ordering requirements where new model/data decisions are justified, and continue planned story-universe expansions. Titan, Event, and Location ordering are already implemented. See [Future Work](API.md#future-work).

## Acknowledgments

Lore sourced and cross-referenced from the [Riordan Wiki](https://riordan.fandom.com/wiki/Riordan_Wiki). This is an unofficial, non-commercial fan project built for educational and portfolio purposes. *Percy Jackson & the Olympians* and related characters, names, and lore are the property of Rick Riordan and Disney Hyperion. This project is not affiliated with or endorsed by either.

## License

The original source code and original project documentation are licensed under the [MIT License](LICENSE), excluding any embedded third-party material. The license does **not** cover the `data/` seed datasets, externally sourced lore or quotations, wiki images or their metadata and URLs, characters, names, trademarks, or other third-party works. Their inclusion or reference here does not grant reuse rights; check the relevant rights and obtain any required permissions before reusing them. Dependencies retain their own licenses. The project's non-commercial description refers to its current purpose, not a restriction on the MIT-licensed code.
