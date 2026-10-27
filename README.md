# Percy Jackson Fandom API

A Django REST API for Riordanverse reference data. The implemented v1 API includes books and their typed casts, characters, gods, Titans, monsters, creatures, weapons, locations, quests, prophecies, events, cabins, factions, images, and global search. Public lore endpoints are read-only and require an API key; key request/verification, health-check, and API documentation routes are public.

> **Status:** The versioned API, seed commands, authentication, filtering, pagination, typed relationships, and tests are implemented. OpenAPI schema, Swagger UI, and ReDoc are available at `/api/schema/`, `/api/docs/`, and `/api/redoc/`. See the [API reference](API.md) for routes, filters, response shapes, and examples.

## Features

- PostgreSQL-backed relational models; no `GenericForeignKey` for typed entity relationships.
- Paginated list responses use `{ "data": [...], "meta": {...} }`.
- API-key authentication via `X-API-Key`, Redis caching for valid key checks, per-key throttling, and request/security logging.
- Strict choice filters and lowercase-only boolean filters; invalid values return a structured `400` response.
- `?sort=<allowed-field>&order=asc|desc` with endpoint-specific allowlists; legacy `?ordering=` remains supported.
- Typed relationships in API responses: Book narrators/cast/antagonists, family graphs, quest participants/casualties, Event casualties, prophecy subjects, faction members, location controllers, and Monster defeat records.
- Image galleries for books, characters, gods, Titans, monsters, weapons, and locations.
- Global search via django-watson, with a typed result for each supported entity.
- Idempotent seed commands for canonical data and relationships.

## Implemented API routes

All versioned routes are under `/api/v1/` and use trailing slashes. Public lore routes require an API key. The following collections have list and slug-detail routes unless noted:

| Resource | Routes and subresources |
| --- | --- |
| Books | `/books/`, `/books/<slug>/`, `/books/<slug>/characters/`, `/books/<slug>/monsters/`, `/books/<slug>/locations/`, `/books/<slug>/quests/`, `/books/<slug>/images/` |
| Characters | `/characters/`, `/characters/<slug>/`, `/characters/<slug>/images/`, `/characters/<slug>/weapons/`, `/characters/<slug>/quests/` |
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
| Search | `/search/?q=<query>`; optional `type=<entity-type>` |

Public health, API-key, and documentation endpoints are outside `/api/v1/`:

- `GET /api/schema/` — OpenAPI 3 schema (YAML by default; add `?format=json` for JSON).
- `GET /api/docs/` — Swagger UI.
- `GET /api/redoc/` — ReDoc.
- `GET /health/live/` — process liveness.
- `GET /health/ready/` — checks PostgreSQL readiness.
- `POST /auth/request-key/` — request a key with `consumer_name` and `email`.
- `POST /auth/verify-key/` — verify a key passed in the configured API-key header.

Swagger UI and ReDoc list Authentication and Health first, followed by the resource groups.

There is no standalone family/divine-relationship, Power, or Image collection endpoint. Family graphs are embedded in God, Titan, Character, Monster, and Creature detail responses; Powers are embedded in Character details; images are exposed through the listed galleries.

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

Book details expose typed `narrators`, `main_characters`, and `antagonists` references, while `/books/<slug>/characters/` lists the linked characters. Quest details provide typed participant and casualty references; Event details expose typed casualties and per-entity participant slug lists; Prophecy details expose typed subjects; Faction details and member subresources expose typed members. These are response relationships, not separate relationship CRUD endpoints.

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

Configure the database and `SECRET_KEY` in `.env`. The development settings connect to PostgreSQL using `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, and `DB_PORT`. Set `REDIS_URL` to your Redis instance; the example file provides a local URL. The API-key header defaults to `X-API-Key` (`API_KEY_CUSTOM_HEADER=HTTP_X_API_KEY`).

Apply migrations, create an admin user if needed, then run the server:

```bash
uv run python manage.py migrate --settings=config.settings.development
uv run python manage.py createsuperuser --settings=config.settings.development
uv run python manage.py runserver --settings=config.settings.development
```

Development keeps API-key authentication enabled. Tests use separate SQLite settings and are not a substitute for running the server with development or production settings.

### Seed canonical data

Run migrations first and seed dependent records in order. Commands are idempotent; use them only against the database you intend to populate.

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
```

The current JSON seeds contain 12 books, 96 characters, 41 gods, 23 Titans, 29 monsters, 18 creatures, 50 weapons, 27 locations, 12 quests, 11 prophecies, 23 events, 20 cabins, 8 factions, 383 family relationship records, 12 Book cast relationship records, 27 Monster defeat records, and 14 Powers. These are seed-file record counts; unresolved references are warned about and skipped by the relevant seed command.

## Authentication and rate limits

Request a key (shown only once):

```bash
curl -X POST http://127.0.0.1:8000/auth/request-key/ \
  -H 'Content-Type: application/json' \
  -d '{"consumer_name":"My Fan App","email":"dev@example.com"}'
```

Use the returned key on v1 requests:

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
/api/v1/characters/?sort=name&order=asc
```

Choice values are validated; invalid choices return `400` with `code: INVALID_FILTER_VALUE` and a `valid_values` list. Boolean filters accept only lowercase `true` and `false`; other spellings return `400`. `sort` and `order` are validated per list endpoint. Sparse fieldsets (`fields=`) and relationship expansion (`include=`) are not implemented.

### API key verification

```bash
curl -X POST http://127.0.0.1:8000/auth/verify-key/ \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: <your-key>'
```

The response contains `valid` and `consumer_name`. API keys can be managed/revoked by an authorized administrator; plaintext keys are not recoverable after creation.

## Tests

```bash
uv run python manage.py test --settings=config.settings.test
```

The test suite uses SQLite test settings. OpenAPI generation is configured with `drf-spectacular`; validate it with `DJANGO_SETTINGS_MODULE=config.settings.development uv run python manage.py spectacular --validate`. The schema and documentation pages are public; API resource endpoints continue to require `X-API-Key`.

## Roadmap

- **Current v1:** implemented/testable routes and seeded Riordanverse reference data described above.
- **Future:** add approved ordering fields that require new model/data decisions and continue planned story-universe expansions. See [Future Work](API.md#future-work).

## Acknowledgments

Lore sourced and cross-referenced from the [Riordan Wiki](https://riordan.fandom.com/wiki/Riordan_Wiki). This is an unofficial, non-commercial fan project built for educational and portfolio purposes. *Percy Jackson & the Olympians* and related characters, names, and lore are the property of Rick Riordan and Disney Hyperion. This project is not affiliated with or endorsed by either.

## License

License to be determined.
