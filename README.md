# Riordanverse API

An unofficial reference API for the entire Riordanverse. That is the project's
scope ambition: the current dataset focuses on Greek/Roman lore and is not
complete coverage of every series.

Website: [riordanverse.cc](https://riordanverse.cc) ·
[API directory](https://riordanverse.cc/api/v1/) ·
[Swagger UI](https://riordanverse.cc/api/docs/).

This is an unofficial fan project for educational and portfolio purposes, not
affiliated with or endorsed by Rick Riordan, Disney Hyperion, or the respective
rights holders. Riordanverse works, characters, and third-party artwork remain
the property of their respective owners.

## Table of contents

- [Use the API](#use-the-api)
  - [Define the base URL](#define-the-base-url)
  - [Get an API key](#get-an-api-key)
  - [Make your first request](#make-your-first-request)
  - [Filter and paginate results](#filter-and-paginate-results)
  - [Understand the response](#understand-the-response)
  - [Authentication, limits, and errors](#authentication-limits-and-errors)
- [API features](#api-features)
- [Data sources and version scope](#data-sources-and-version-scope)
- [Setup](#setup)
- [Database setup](#database-setup)
- [Run the project](#run-the-project)
- [Docker and Compose](#docker-and-compose)
- [Report a lore correction](#report-a-lore-correction)
- [Contact](#contact)
- [Contributing](#contributing)
- [Deployment](#deployment)
- [Acknowledgments](#acknowledgments)
- [License](#license)

## Use the API

You do not need to clone the project to use a hosted instance. For self-hosting or
local development, follow [Setup](#setup) first. All examples use trailing slashes.

Documentation: [API reference](API.md) · [Swagger UI](https://riordanverse.cc/api/docs/)
· [ReDoc](https://riordanverse.cc/api/redoc/)
· [OpenAPI schema](https://riordanverse.cc/api/schema/).
These links use the intended public origin, subject to the availability caveat
above. For local use, keep the same paths under `http://127.0.0.1:8000`.

### Define the base URL

In your terminal, set the server origin **without** `/api/v1` or a trailing slash:

```bash
export BASE_URL="https://riordanverse.cc"
```

This is the intended public origin, not a guarantee of availability. Until it is
verified, use a confirmed deployment or set `BASE_URL="http://127.0.0.1:8000"`
for a locally running instance.
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
// Intended public origin; use a confirmed instance until availability is verified.
const baseUrl = "https://riordanverse.cc";
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

## Data sources and version scope

The **Version 1 (V1) source scope** covers the five original *Percy Jackson and
the Olympians* novels and the companion works below, supplemented by secondary
reference data. [`data/books.json`](data/books.json) contains **12 book records**:
the collection *The Demigod Files* and its three individual stories are recorded
separately. This is not a count of 12 independently published books.

The version column identifies the dataset scope in which a source is included;
it is not a claim of exhaustive coverage or a published release tag. Extend this
table as later dataset versions add sources, retaining earlier scope entries.

| Dataset scope | Source | Publication | Role |
| --- | --- | --- | --- |
| V1 | *The Lightning Thief* | 2005 | Core PJO novel — Book 1 |
| V1 | *The Sea of Monsters* | 2006 | Core PJO novel — Book 2 |
| V1 | *The Titan's Curse* | 2007 | Core PJO novel — Book 3 |
| V1 | *The Battle of the Labyrinth* | 2008 | Core PJO novel — Book 4 |
| V1 | *The Last Olympian* | 2009 | Core PJO novel — Book 5 |
| V1 | *The Demigod Files* | 2009 | Companion collection containing the three stories below |
| V1 | *Percy Jackson and the Stolen Chariot* | 2009 collection edition | Short story in *The Demigod Files* |
| V1 | *Percy Jackson and the Bronze Dragon* | 2009 collection edition | Short story in *The Demigod Files* |
| V1 | *Percy Jackson and the Sword of Hades* | 2009 collection edition | Short story in *The Demigod Files* |
| V1 | *Percy Jackson's Greek Gods* | 2014 | Mythology companion |
| V1 | *Percy Jackson's Greek Heroes* | 2015 | Mythology companion |
| V1 | *Percy Jackson and the Singer of Apollo* | 2013; standalone edition 2016 | Companion short story; seeded publication date uses 2013 |
| V1 | [Riordan Wiki on Fandom](https://riordan.fandom.com/) | Continuously updated | Secondary reference for entity URL matching and cross-checking |
| V1 | [V1 seed corpus](data/) (`data/*.json`) | Repository-maintained | Curated dataset and relationships used by the seed commands, not an independent canonical source |

Entity relationships, event chronologies, and location appearances are curated
with reference to this scope. The books are the primary sources; the wiki is a
secondary reference. Inclusion here does not certify that every field has been
independently checked against every text. Corrections should cite the relevant
book and chapter or a supporting reference; see [Report a lore correction](#report-a-lore-correction).

## Setup

For local development, install Python **3.14+**, [uv](https://docs.astral.sh/uv/),
PostgreSQL, and **Node.js 22+ with npm** for website assets. Redis is recommended
for shared caching and quotas, but its absence does not prevent API requests.
If you prefer containers, skip to [Docker and Compose](#docker-and-compose).

Clone the repository into a local `riordanverse-api` directory (authorized GitHub
access is required while the repository is private).

```bash
git clone https://github.com/devisreal/Riordanverse-API.git riordanverse-api
cd riordanverse-api
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

Found incorrect or missing reference data? [Report a lore correction](https://github.com/devisreal/Riordanverse-API/issues/new?template=lore_correction.yml)
using the GitHub issue form. A GitHub account with repository access is required
while the repository is private. Treat submissions as public-facing: they may
become public when the repository is made public.

Include the affected API URL, entity name, or slug; the current information; your
suggested correction; and evidence such as a book title and chapter or a supporting
reference URL. Describe the evidence in your own words rather than copying lengthy
copyrighted excerpts. Never include API keys, email addresses, or other personal
information. Search existing issues first to avoid duplicate reports.

Reports are reviewed manually. Submitting a correction does **not** automatically
change the dataset, and no on-site submission form or new API endpoint is involved.

## Contact

- General inquiries: [hello@riordanverse.cc](mailto:hello@riordanverse.cc).
- API support and application emails: [support@riordanverse.cc](mailto:support@riordanverse.cc).

These mailboxes exist, but mailbox availability alone does not configure outbound
application email. Sending requires provider credentials, verified sending
identity/domain, and tested delivery; see [email deployment requirements](DEPLOYMENT.md#application-email).
API-key issuance remains immediate, without email verification.

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
