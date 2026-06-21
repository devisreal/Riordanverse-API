# Percy Jackson Fandom API

A lore-accurate, read-only public REST API covering the Riordanverse — starting with the five core novels of **Percy Jackson & the Olympians**, with companion materials, and built to expand into the wider universe (Heroes of Olympus, Kane Chronicles, and beyond).

This API is the data backbone for a planned fan web application, with a future mobile adaptation.

> 🚧 **Status:** Architecture planning ongoing, implementation in progress. See [`API.md`](./API.md) for the full data model, endpoint, and decision-log documentation.

---

## ✨ Features

- Rich relational lore data: characters, gods, Titans, monsters, weapons, locations, quests, prophecies, cabins, factions, and events
- Full PostgreSQL referential integrity — no `GenericForeignKey` usage anywhere (divine relationships and image galleries are modelled with explicit FK join tables)
- Per-entity, filterable image galleries (official art, Disney+ stills, fan art, concept art, etc.)
- Strict enum filtering — invalid filter values return a `400`, not a silently empty result set
- Global search across all lore entities, including alias resolution (e.g. "Aunty Em" → Medusa)
- API-key authentication with Redis-backed key caching
- Versioned from day one (`/api/v1/`) to support a non-breaking V2 (Heroes of Olympus + Kane Chronicles) and V3 (Trials of Apollo, Magnus Chase) expansion

---

## 🏗 Tech Stack

| Layer | Choice |
|---|---|
| Language / Framework | Python, Django, Django REST Framework |
| Database | PostgreSQL |
| Caching | Redis (`django-redis`) |
| Auth | `djangorestframework-api-key` (custom `ConsumerAPIKey` model, Redis-cached permission check) |
| Filtering | `django-filter` |
| Search | `django-watson` (with custom per-model adapters for alias flattening) |
| Slugs | `django-autoslug` |
| Settings | `django-environ` (split settings, explicit DB env vars) |
| API Docs | `drf-spectacular` (OpenAPI schema + Swagger UI) |

---

## 📁 Project Structure

```
pj_fandom_api/
├── manage.py
├── .env.example
├── API.md                     # full architecture & lore data-model docs
├── requirements/
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   ├── production.py
│   │   └── test.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
└── apps/
    ├── core/             # BaseModel, shared enums, pagination, exceptions
    ├── images/           # Image model + reusable image-join mixin
    ├── characters/       # Character, Power
    ├── divinities/       # God, Titan, DivineRelationship
    ├── bestiary/         # Monster, Creature/Species
    ├── items/            # Weapons & magical items
    ├── locations/        # Location
    ├── narrative/        # Book, Quest, Prophecy, Event
    ├── organizations/    # Cabin, Faction
    ├── search/           # django-watson adapters, global search endpoint
    └── access/           # self-service API key registration
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- PostgreSQL 15+
- Redis 7+

### Installation

```bash
git clone <repo-url>
cd pj_fandom_api
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements/development.txt
```

### Environment Variables

Copy the example file and fill in your local values:

```bash
cp .env.example .env
```

| Variable | Description |
|---|---|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | `True` / `False` |
| `ALLOWED_HOSTS` | Comma-separated hostnames |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | PostgreSQL connection |
| `REDIS_URL` | Redis connection string |
| `CORS_ALLOWED_ORIGINS` | Comma-separated frontend origins |
| `API_KEY_CUSTOM_HEADER` | Header name used for API key auth |

### Database Setup

```bash
createdb pj_fandom_dev
python manage.py migrate --settings=config.settings.development
python manage.py createsuperuser --settings=config.settings.development
```

### Redis

Make sure a local Redis instance is running (used for API key caching):

```bash
redis-server
```

### Run the Dev Server

```bash
python manage.py runserver --settings=config.settings.development
```

Or set `DJANGO_SETTINGS_MODULE=config.settings.development` in your shell/`.env` to drop the `--settings` flag.

---

## 🔑 Authentication

This is a public, **read-only** API. Most endpoints require an API key, passed via the `Api-Key` request header:

```bash
curl -H "Api-Key: <your-key>" https://api.example.com/api/v1/characters/percy-jackson
```

Request a key:

```
POST /auth/request-key/
```

> In the `development` settings, authentication is disabled by default for easier local browsing of the API.

---

## 🧪 Running Tests

Tests always run against SQLite, regardless of your `.env` database config:

```bash
python manage.py test --settings=config.settings.test
```

---

## 📚 Example Requests

```bash
GET /api/v1/characters?divine_parent=poseidon
GET /api/v1/gods/zeus
GET /api/v1/characters/annabeth-chase/images?source_type=fan_art&category=portrait
GET /api/v1/search?q=riptide
```

Full endpoint reference: see [Section 7 of `API.md`](./API.md#7-api-endpoints-v1).

Once `drf-spectacular` is wired up, interactive API docs will be available at `/api/v1/docs/`.

---

## 🗺 Roadmap

- **V1** — Percy Jackson & the Olympians (Books 1–5) + companion materials *(current focus)*
- **V2** — Heroes of Olympus, Kane Chronicles, crossover works (Roman aspects, Egyptian deity system)
- **V3** — Trials of Apollo, Magnus Chase, Nico di Angelo Adventures

See [Section 12 of `API.md`](./API.md#12-v2-expansion-considerations) for expansion notes.

---

## 🙏 Acknowledgments

Lore sourced and cross-referenced from the [Riordan Wiki](https://riordan.fandom.com/wiki/Riordan_Wiki). This is an unofficial, non-commercial fan project built for educational and portfolio purposes. *Percy Jackson & the Olympians* and all related characters, names, and lore are the property of Rick Riordan and Disney Hyperion. This project is not affiliated with or endorsed by either.

---

## 📄 License

License to be determined.