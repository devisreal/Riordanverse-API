# Percy Jackson Fandom API

A RESTful API for the Riordanverse. [Visit the website](https://percy-jackson-fandom.up.railway.app/).

This is an unofficial fan project for educational and portfolio purposes, not
affiliated with or endorsed by Rick Riordan, Disney Hyperion, or the respective
rights holders. Riordanverse works, characters, and third-party artwork remain
the property of their respective owners.

> **Hosted availability:** The linked address was used for the test deployment and
> returned HTTP 404 when checked on November 11, 2026. Until a permanent hosted
> address is confirmed, the examples below use a locally running instance.

## Table of contents

- [Use the API](#use-the-api)
  - [Define the base URL](#define-the-base-url)
  - [Get an API key](#get-an-api-key)
  - [Make your first request](#make-your-first-request)
  - [Filter and paginate results](#filter-and-paginate-results)
  - [Understand the response](#understand-the-response)
  - [Authentication, limits, and errors](#authentication-limits-and-errors)
- [API features](#api-features)
- [Setup](#setup)
- [Database setup](#database-setup)
- [Run the project](#run-the-project)
- [Docker and Compose](#docker-and-compose)
- [Report a lore correction](#report-a-lore-correction)
- [Contributing](#contributing)
- [Deployment](#deployment)
- [Acknowledgments](#acknowledgments)
- [License](#license)

## Use the API

You do not need to clone the project to use a hosted instance. For self-hosting or
local development, follow [Setup](#setup) first. All examples use trailing slashes.

Documentation: [API reference](API.md) · [Swagger UI](http://127.0.0.1:8000/api/docs/)
· [ReDoc](http://127.0.0.1:8000/api/redoc/)
· [OpenAPI schema](http://127.0.0.1:8000/api/schema/).
The browser links above target a local server; on a hosted instance, use the same
paths under that instance's origin.

### Define the base URL

In your terminal, set the server origin **without** `/api/v1` or a trailing slash:

```bash
export BASE_URL="http://127.0.0.1:8000"
```

Replace it with the confirmed HTTPS website origin when using a hosted instance.
The public directory lists the available collections without requiring a key:

```bash
curl "$BASE_URL/api/v1/"
```

### Get an API key

Request a key using your application name and contact email:

```bash
curl -X POST "$BASE_URL/auth/request-key/" \
  -H 'Content-Type: application/json' \
  -d '{"consumer_name":"My Fan App","email":"dev@example.com"}'
```

The response's `api_key` is shown **only once**. Store it securely, then set it in
your current terminal for the examples:

```bash
export API_KEY="<paste-your-key-here>"
```

- Send the key in `X-API-Key`, not a URL query parameter.
- Do not commit keys, include them in screenshots, or publish them in frontend bundles.
- **Keys shipped to browsers are visible to users**, including through JavaScript
  bundles and developer tools. Build-time frontend environment variables do not
  keep them secret. Someone who copies a key can consume its quota. Prefer a
  backend/serverless proxy when a key must stay private.
- Cross-origin browser requests support `X-API-Key` for origins explicitly enabled
  by the API operator in `CORS_ALLOWED_ORIGINS`. Origins are not automatically
  approved. See [browser access configuration](DEPLOYMENT.md#https-health-checks-and-browser-access).
- Key issuance is immediate; there is no email-verification step. Key verification
  below checks whether a key is valid, not whether an email address belongs to you.

### Browser integrations

Once the API operator allows your frontend's origin, browser JavaScript can call
it directly. Supply a disposable or user-provided key; never embed a private
shared key in a public bundle:

```javascript
// Browser example: replace the URL with the API instance you are using.
const baseUrl = "http://127.0.0.1:8000";
async function loadBooks(apiKey) {
  const response = await fetch(`${baseUrl}/api/v1/books/`, {
    headers: { "X-API-Key": apiKey },
    credentials: "omit",
  });
  if (!response.ok) throw new Error(`API request failed: ${response.status}`);
  return response.json();
}
```

Use HTTPS API URLs from HTTPS frontends to avoid mixed-content blocking. CORS is
not authentication: requests still require a valid key and consume its quota.
The exposed `RateLimit-*` and `Retry-After` headers can be read by JavaScript.

### Make your first request

Fetch Percy Jackson by slug:

```bash
curl "$BASE_URL/api/v1/characters/percy-jackson/" \
  -H "X-API-Key: $API_KEY"
```

For a server-side JavaScript application, the equivalent is:

```javascript
const baseUrl = process.env.BASE_URL;
const apiKey = process.env.API_KEY;
const response = await fetch(`${baseUrl}/api/v1/characters/percy-jackson/`, {
  headers: { "X-API-Key": apiKey },
});
if (!response.ok) throw new Error(`API request failed: ${response.status}`);
const percy = await response.json();
console.log(percy.name);
```

This example uses Node.js environment variables; do not copy a private key into
client-side source code.

### Filter and paginate results

List Poseidon's children, requesting five results on the first page:

```bash
curl "$BASE_URL/api/v1/characters/?divine_parent=poseidon&limit=5&page=1" \
  -H "X-API-Key: $API_KEY"
```

List routes default to 20 results per page. Use `page` and `limit` (maximum 100).
Filters are endpoint-specific; see the [full filter reference](API.md#list-filters).
Sorting uses `sort` and optional `order=asc|desc`:

```bash
curl "$BASE_URL/api/v1/characters/?sort=name&order=asc&limit=5" \
  -H "X-API-Key: $API_KEY"
```

### Understand the response

A detail route returns one resource object. This is a **verified excerpt** of the
seeded Percy Jackson detail response; additional fields are omitted:

```json
{
  "name": "Percy Jackson",
  "slug": "percy-jackson"
}
```

List routes instead wrap results in `data` and pagination information in `meta`.
For example, an empty list on the first page with the default page size has this
shape (this is not the response to the Poseidon query above):

```json
{
  "data": [],
  "meta": {
    "total": 0,
    "page": 1,
    "limit": 20,
    "total_pages": 1
  }
}
```

`total` counts all matching records, not just the current page. Search is
unpaginated (`page` and `limit` do not apply) and has its own metadata containing
`total`, `query`, and `type_filter`. See [response and error
shapes](API.md#list-response-and-error-shapes) for the full contracts.

### Authentication, limits, and errors

Lore endpoints are **read-only** and require an API key. The homepage, API
directory, schema, Swagger, ReDoc, health checks, key requests, and key verification
are public. Documentation pages are exempt from API request throttling; executing
a data request through Swagger still requires a key and consumes the data quota.

- Authenticated requests: **1,000 per key per fixed one-hour window**.
- Key requests and key verification: separate limits of **5 per hour per client IP**.
- Data responses include `RateLimit-Limit`, `RateLimit-Remaining`, and
  `RateLimit-Reset`; throttled responses include `Retry-After`.
- If Redis is unavailable, quota counters are process-local, not shared across workers.
- `X-Request-ID` supports request correlation when reporting problems.
- Invalid choice filters or non-lowercase boolean values return `400`; booleans
  must be `true` or `false`. Missing/invalid keys on protected routes return `403`,
  missing resources return `404`, and exhausted quotas return `429`.

Verify your key:

```bash
curl -X POST "$BASE_URL/auth/verify-key/" -H "X-API-Key: $API_KEY"
```

Revoke the key used in the request (no request body):

```bash
curl -X POST "$BASE_URL/auth/revoke-key/" -H "X-API-Key: $API_KEY"
```

Revocation does not accept an email address as authorization. Plaintext keys cannot
be recovered after creation. See [authentication and security](API.md#14-authentication--security)
for caching and revocation details.

## API features

- Books, characters, gods, Titans, monsters, creatures, weapons, locations, quests,
  prophecies, events, cabins, factions, and images.
- Slug-based resource lookups, filters, pagination, and endpoint-specific sorting.
- Typed family graphs, Book casts, quest participants/casualties, and other lore relationships.
- Character powers and nested resources for related entities.
- Image metadata, curated primary images, and entity galleries. Image URLs point
  to external sources; the API does not host or proxy the image bytes.
- Global search across supported resources.
- JSON data responses and interactive OpenAPI documentation.

A few entry points:

| Resource | Example |
| --- | --- |
| Characters | `/api/v1/characters/percy-jackson/` |
| Books | `/api/v1/books/the-lightning-thief/` |
| Gods | `/api/v1/gods/poseidon/` |
| Images | `/api/v1/characters/percy-jackson/images/` |
| Search | `/api/v1/search/?q=riptide` |

See the [complete endpoint reference](API.md#7-api-endpoints-v1),
[implemented API contracts](API.md#23-current-implemented-api-reference), or
`/api/docs/` and `/api/redoc/` on your instance for all resources and subresources.

## Setup

For local development, install Python **3.14+**, [uv](https://docs.astral.sh/uv/),
PostgreSQL, and **Node.js 22+ with npm** for website assets. Redis is recommended
for shared caching and quotas, but its absence does not prevent API requests.
If you prefer containers, skip to [Docker and Compose](#docker-and-compose).

```bash
git clone https://github.com/devisreal/Percy-Jackson-Fandom-API.git
cd Percy-Jackson-Fandom-API
uv sync --locked
cp .env.example .env
npm ci --prefix website/static_src
npm run build --prefix website/static_src
```

Create a local PostgreSQL database and user first; editing `.env` does not create
those resources. Set `SECRET_KEY`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`,
and `DB_PORT` in `.env` for that database; configure `REDIS_URL` if using Redis.
Development keeps API-key authentication enabled. Never commit `.env` or real keys.

## Database setup

Apply migrations, then populate the lore data in dependency order:

```bash
uv run python manage.py migrate --settings=config.settings.development
uv run python manage.py seed_all --settings=config.settings.development
```

Create an optional admin account:

```bash
uv run python manage.py createsuperuser --settings=config.settings.development
```

Seed commands are idempotent but can update existing records. Confirm the target
database before running them. Unlike a database backup, seeds do not restore
consumers or API keys. Curated image choices in `data/image_gallery_overrides.json`
are restored by `seed_images`, which runs as part of `seed_all`.
See [seed maintenance](CONTRIBUTING.md#seed-canonical-data) for individual commands.

## Run the project

```bash
uv run python manage.py runserver --settings=config.settings.development
```

Open [the website](http://127.0.0.1:8000/),
[Swagger UI](http://127.0.0.1:8000/api/docs/), or
[the API directory](http://127.0.0.1:8000/api/v1/).
For website work, start Django and the CSS/JavaScript watchers together instead:

```bash
uv run python manage.py tailwind dev --settings=config.settings.development
```

This does not require Docker. If a Compose app is already using port 8000, stop it
first or use a different local port. See [the frontend workflow](CONTRIBUTING.md#website-and-tailwind-workflow)
for components, asset conventions, and test commands.

## Docker and Compose

The local Compose stack runs the application, PostgreSQL 17, and Redis 7. With
Docker and Compose installed, create `.env` from `.env.example`, set `SECRET_KEY`,
then run from the repository root:

```bash
docker compose up --build -d
docker compose exec app /opt/venv/bin/python manage.py migrate --noinput
docker compose exec app /opt/venv/bin/python manage.py seed_all
```

Open **http://localhost:8000**. Optionally create an admin account:

```bash
docker compose exec app /opt/venv/bin/python manage.py createsuperuser
```

The local-only `config.settings.compose` disables HTTPS redirects and secure-cookie
requirements for local HTTP. The production image must use production settings.
Migrations and seeding are manual; rebuilding the image does not perform them.

```bash
docker compose logs -f app
docker compose down
```

Named volumes preserve local database/cache data between restarts. **Do not add
`-v` to `down` unless you intend to delete those volumes.** Compose uses its own
database, not your ordinary local development database. It has no source bind
mounts or automatic reload; rebuild after source changes. See [deployment](DEPLOYMENT.md)
for Railway and production hosting; Railway does not use this Compose file.

## Report a lore correction

Found incorrect or missing reference data? [Report a lore correction](https://github.com/devisreal/Percy-Jackson-Fandom-API/issues/new?template=lore_correction.yml)
using the GitHub issue form. A GitHub account is required, and submissions are public.

Include the affected API URL, entity name, or slug; the current information; your
suggested correction; and evidence such as a book title and chapter or a supporting
reference URL. Describe the evidence in your own words rather than copying lengthy
copyrighted excerpts. Never include API keys, email addresses, or other personal
information. Search existing issues first to avoid duplicate reports.

Reports are reviewed manually. Submitting a correction does **not** automatically
change the dataset, and no on-site submission form or new API endpoint is involved.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full development workflow, dependency
updates, seed maintenance, frontend conventions, tests, and pull-request guidance.

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for Docker/Railway configuration, Gunicorn,
WhiteNoise, static builds, HTTPS/proxy checks, release commands, and backup safety.

## Acknowledgments

Lore sourced and cross-referenced from the [Riordan Wiki](https://riordan.fandom.com/wiki/Riordan_Wiki). This is an unofficial, non-commercial fan project built for educational and portfolio purposes. *Percy Jackson & the Olympians* and related characters, names, and lore are the property of Rick Riordan and Disney Hyperion. This project is not affiliated with or endorsed by either.

## License

The original source code and original project documentation are licensed under the [MIT License](LICENSE), excluding any embedded third-party material. The license does **not** cover the `data/` seed datasets, externally sourced lore or quotations, wiki images or their metadata and URLs, characters, names, trademarks, or other third-party works. Their inclusion or reference here does not grant reuse rights; check the relevant rights and obtain any required permissions before reusing them. Dependencies retain their own licenses. The project's non-commercial description refers to its current purpose, not a restriction on the MIT-licensed code.
