# Percy Jackson Fandom API — Reference & Planning Notes

**Project:** Percy Jackson Fandom Platform

**API Version:** 1.0 (`/api/v1/`; current routes cover the records in the canonical seed corpus)

**Source Reference:** [Riordan Wiki (Fandom)](https://riordan.fandom.com/wiki/Riordan_Wiki)

**Status:** Implemented API details are documented in Sections 13–15 and 23. Sections explicitly labeled proposed are not current contracts.
**Future Versions:** Additional Riordanverse coverage is a future expansion; see the final Future Work section.

---

## Table of Contents

1. [Project Vision](#1-project-vision)
2. [API Scope & Versioning](#2-api-scope--versioning)
3. [Core Concepts & Lore Considerations](#3-core-concepts--lore-considerations)
4. [Data Models](#4-data-models)
   - [Book](#41-book)
   - [Character](#42-character)
   - [God](#43-god)
   - [Titan](#44-titan)
   - [Monster](#45-monster)
   - [Creature / Species](#46-creature--species)
   - [Weapon & Magical Item](#47-weapon--magical-item)
   - [Location](#48-location)
   - [Quest](#49-quest)
   - [Cabin](#410-cabin)
   - [Prophecy](#411-prophecy)
   - [Event / Battle](#412-event--battle)
   - [Faction / Affiliation](#413-faction--affiliation)
5. [Relationships & Linking Strategy](#5-relationships--linking-strategy)
6. [Enumerations (Enums)](#6-enumerations-enums)
7. [API Endpoints (v1)](#7-api-endpoints-v1)
8. [Filtering, Sorting & Pagination](#8-filtering-sorting--pagination)
   - [Pagination](#pagination)
   - [Sorting & Default Sort Order](#sorting)
   - [Filtering & Case Sensitivity](#filtering)
   - [Sparse Fieldsets](#sparse-fieldsets--not-implemented)
   - [Includes / Relationships](#include-relationship-expansion--not-implemented)
9. [Image Strategy](#9-image-strategy)
10. [Seed Data — V1 Canonical Entries](#10-seed-data--current-canonical-json-counts)
11. [Edge Cases & Lore Nuances](#11-edge-cases--lore-nuances)
12. [V2 Expansion Considerations](#12-v2-expansion-considerations-proposals)
13. [General API Design Principles](#13-general-api-design-principles)
14. [Authentication & Security](#14-authentication--security)
15. [Search](#15-search)
16. [Lore Accuracy and Source Provenance](#16-lore-accuracy-and-source-provenance)
17. [Soft Delete](#17-soft-delete)
18. [Ordering Within Related Sets](#18-ordering-within-related-sets--partially-implemented)
19. [Environment Configuration](#19-environment-configuration)
20. [BaseModel — Implemented Shared Fields and Earlier Proposal](#20-basemodel--implemented-shared-fields-and-earlier-proposal)
21. [Power Sub-Model](#21-power-sub-model)
22. [Typed Family Relationships](#22-typed-family-relationships)
23. [Current Implemented API Reference](#23-current-implemented-api-reference)
24. [Future Work](#24-future-work)

---

## Decision Log

A running record of project decisions. Some earlier rows were proposals and are marked below where they are not implemented. For the current, testable API contract, use Sections 13–15 and 23.

### Stack & Infrastructure

| # | Decision | Choice Made | Reason |
| --- | --- | --- | --- |
| 1 | Backend stack | **Python 3.14+ / Django / DRF + PostgreSQL; dependencies managed with `uv`** | Relational ORM, Django Admin, DRF serializers/filtering, and migration support; test settings use SQLite |
| 21 | Environments | **`base.py`, `development.py`, `production.py`, `test.py`, and `test_postgresql.py`**; development/production use PostgreSQL, SQLite is the default test backend, and CI also runs the full suite against PostgreSQL | Redis is optional and has outage fallbacks; see Section 19 |
| 14 | Caching | **Redis is optional** — caches successful API-key validation and shares rate-limit counters when available | PostgreSQL and process-local fallbacks keep requests available during a Redis outage; lore responses are not generally cached |

### API Design & Conventions

| # | Decision | Choice Made | Reason |
| --- | --- | --- | --- |
| 1 (URLs) | Trailing slash | **With trailing slash** — `/api/v1/characters/` | Django default; enforce consistently across all endpoints |
| 2 | Timestamp format | **ISO 8601** — `2005-07-28T00:00:00Z` | Universal standard; unambiguous across timezones and clients |
| 3 | Field naming | **`snake_case` in all API responses** | DB uses snake_case; consistent end-to-end; avoids DRF camelCase conversion overhead |
| 4 | Boolean filter format | **`?is_demigod=true`** — only lowercase `true` and `false` | Boolean query filters reject other spellings with a 400 response |
| 5 | Empty vs null | **`null` for missing optional scalar fields; `[]` for empty arrays** | Distinguishes "field has no value" from "field has no related items" |
| 6 | HTTP status codes | **Full DRF `status` library** — 200, 400, 401, 403, 404, 429, 500 mapped to correct triggers | See Section 14 for full status code map |
| 7 | Health checks | **`GET /health/live/`** and **`GET /health/ready/`** outside the API prefix | Liveness checks process responsiveness; readiness checks PostgreSQL |
| 9 | Filter validation | **`StrictChoiceFilter` returns `INVALID_FILTER_VALUE`; booleans accept only lowercase `true`/`false`** | Invalid choice values include `valid_values`; other invalid query values use `BAD_REQUEST` rather than silently broadening results |
| 10 | Character encoding | **Explicit `UTF8` in PostgreSQL config + DRF automatic `charset=utf-8` headers** | Greek names (Zoë, Ἀχιλλεύς) require full Unicode; DRF handles headers automatically |
| 13 | Rate limiting | **1,000 requests/hour per API-key prefix** using `PerAPIKeyRateThrottle`; 100/day anonymous fallback; 5/hour/IP on public key routes | Redis-backed fixed-window counters with process-local fallback during Redis outage |

### Data & Models

| # | Decision | Choice Made | Reason |
| --- | --- | --- | --- |
| 2 | Image storage | **Option B — `Image` model + separate join tables per entity** (`CharacterImage`, `WeaponImage`, etc.) | Full PostgreSQL FK integrity; avoids GenericForeignKey complexity |
| 3 | Image filtering | **Filterable global collection and typed galleries on supported entities** | The global collection is filterable; typed galleries are implemented for Books, Characters, Gods, Titans, Monsters, Weapons, and Locations, using query params for source/category filters |
| 8 | Default sort order | **Per-view defaults and allowlists** — see Section 23 | Titans use `display_order`, Events use `chronology_order`, and Locations use `location_order`; each exposed sort is explicitly allowlisted |
| 11 | Slug generation | **`django-autoslug`** per model — source field varies (`name`, `title`, custom callable for Cabin) | Auto-generates slugs on save; handles collisions; slug is not on BaseModel because `populate_from` differs per model |
| 18 | Soft delete | **Implemented; Admin-only lifecycle** | Default managers and public resource endpoints exclude soft-deleted entities; Admin can restore; no public delete/restore endpoint |
| 19 | Lore accuracy and provenance | **Implemented** | Shared accuracy metadata plus reusable `LoreSource` citations are available in entity serializers and `lore_accuracy` filters |
| 20 | Ordering within related sets | **Partially implemented; additional contextual ordering is future work** | Image galleries and Titan/Event/Location collections have explicit ordering; other historical relationship-order proposals remain deferred |
| — | Primary key type | **`BigAutoField` globally** via `DEFAULT_AUTO_FIELD` in `base.py` | PostgreSQL `bigint NOT NULL PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY` on every model; not declared on `BaseModel` — handled by settings |
| — | BaseModel | **Implemented abstract `BaseModel`** in `apps/core/models.py` with timestamps, nullable `wiki_url`, lore metadata, and soft-delete state | Slugs and entity-specific data remain on concrete models; `objects` hides deleted records and `all_objects` supports internal/Admin operations |

### Authentication & Search

| # | Decision | Choice Made | Reason |
| --- | --- | --- | --- |
| 12 | API authentication | **`djangorestframework-api-key` + `ConsumerAPIKey`; `X-API-Key`; 5-minute positive validation cache** | Cache is keyed by public prefix but stores a settings-salted fingerprint of the full key, so a different secret with the same prefix is not accepted; validation falls back to PostgreSQL, and admin/self-revocation invalidates after commit |
| 12 (flow) | Key lifecycle | **Public key request/verification** at `POST /auth/request-key/` and `/auth/verify-key/`; key holders can revoke only the presented key at `POST /auth/revoke-key/` | Request and verification require `consumer_name` and `email` as applicable and use IP-based throttles; revocation requires `X-API-Key`, not an email address |
| 15 | Search | **`django-watson`** with custom adapters per model | Mature, PostgreSQL-native full-text search; custom adapters handle aliases, `true_name`, `disguise_form` |
| 16 | Alias search | **Included in watson custom adapters via `get_search_text()`** | Flattens `aliases` array, `true_name`, `disguise_form` into indexed text; "Aunty Em" finds Medusa |
| 17 | API documentation | **Public OpenAPI, Swagger UI, and ReDoc routes are registered with `drf-spectacular==0.30.0`** | `/api/schema/` serves the schema; `/api/docs/` and `/api/redoc/` serve public interactive documentation. The schema declares `X-API-Key` for protected operations |

---

## 1. Project Vision

The Percy Jackson Fandom API is an implemented, read-only REST API serving canonical Riordanverse reference data. The v1 API exposes books, characters, divinities, monsters, creatures, weapons, locations, quests, prophecies, events, organizations, images, and search through typed relations. The web and mobile clients remain consumers of this API; they are not part of this backend.

**Current V1 data scope:** the canonical JSON seed corpus currently contains 12 Book records, including core books and child companion-story records, plus seeded characters, Gods, Titans, Monsters, Creatures, Weapons, Locations, Quests, Prophecies, Events, Cabins, and Factions. See Section 23 for implemented API routes and Section 10 for current seed-file counts. This is the current corpus, not a promise that every Riordanverse entity has been added.

---

## 2. API Scope & Versioning

### Version 1 — Implemented Seed Corpus

The actual supported scope is the canonical data present in `data/*.json`; the collection is broader than the original five-book planning scope but is not exhaustive. Missing or unresolved references are warned about and skipped by seed commands. Current record counts appear in Section 10.

### Version 2 — Expanded Universe

- The Heroes of Olympus (5 books)
- The Kane Chronicles (3 books) — Egyptian mythology system
- The Demigod Diaries
- Crossover short stories (Demigods & Magicians)
- Shorter companion works

### Version 3 (Future)

- The Trials of Apollo (5 books)
- Magnus Chase and the Gods of Asgard (Norse mythology)
- The Nico di Angelo Adventures
- The Senior Year Adventures

---

## 3. Core Concepts & Lore Considerations

These are editorial lore notes, not declarations that a matching field or timeline feature exists in the API. Current fields and testable representations are listed in Section 23; proposed/unimplemented model fields are called out explicitly.

### The Mist

A magical veil that conceals mythological activity from mortals. Mortals who can see through it (like Rachel Elizabeth Dare and Sally Jackson) are flagged in the `Character` model via a boolean `can_see_through_mist`.

### The Big Three Oath

After World War II, Zeus, Poseidon, and Hades swore on the River Styx to father no more demigod children. This oath was broken by Zeus (Thalia, Jason) and Poseidon (Percy). Hades' children (Nico, Bianca) were born before the oath. The oath was dissolved at the end of The Last Olympian. This must be tracked on the `God` model and in character lore notes.

### Demigod Physiology

All Greek demigods share traits rooted in mythology:

- **Dyslexia** — their brains are hardwired for Ancient Greek, not English
- **ADHD** — battlefield reflexes manifesting in civilian life
- **Monster attraction** — the more powerful the demigod, the stronger the scent
- **Cell phones** — using one is the equivalent of firing a flare gun for monsters
- **Claiming** — demigods must be claimed by their divine parent. After The Last Olympian, all gods are required to claim children by age 13.

### Greek vs. Roman Aspects

Gods exist in both Greek and Roman aspects (e.g. Ares/Mars, Athena/Minerva). These aspects have different personalities and limited knowledge of each other's actions. The implemented God detail exposes `roman_name` and related aspect fields. A dedicated `roman_equivalent` cross-reference is not currently exposed; additional cross-universe modeling is deferred.

### Monster Reformation

Monsters do not permanently die — they dissolve into dust (Tartarus) and reform. The time to reform varies. The `Monster` model exposes `can_reform` and `regeneration_time`; see the current serializer fields in Section 23.

### Spoils of War

When some monsters are killed, they leave a trophy (part of their body, armor, or weapon). This is tracked in `Monster.spoils_of_war`.

### Celestial Bronze, Stygian Iron & Imperial Gold

- **Celestial Bronze** — forged by Hephaestus's Cyclopes, passes through mortals, hurts gods and monsters
- **Stygian Iron** — from the Underworld, affects souls and undead, causes great pain to mortals
- **Imperial Gold** — Roman equivalent of Celestial Bronze (V2)
- **Mortal steel** — cannot harm mythological beings

### The River Styx Oath

Swearing on the River Styx is the most binding oath in existence. Breaking it brings divine punishment. Referenced in character backstories (e.g., Luke Castellan's betrayal, Percy's invulnerability blessing).

### The Mist & Empathy Links

Satyrs can form telepathic "Empathy Links" with their assigned demigods — an extremely rare bond between best friends. Only established between Grover and Percy in V1.

---

## 4. Data Models

> The model tables below originated as design notes and may mention fields that were not implemented. The implemented API shape is defined by the serializers and documented in Section 23. Current lore models share `created_at`, `updated_at`, and nullable `wiki_url` through `BaseModel`; their primary keys use `BigAutoField`, and slugs are declared per concrete model.

---

### 4.1 Book

Represents a Book or child companion-story record in the current corpus. The fields below are the original planning schema; see Section 23 for current list/detail serializer fields and typed role relationships.

| Field | Type | Description |
| --- | --- | --- |
| `id` | int | Primary key |
| `slug` | string | e.g. `"the-lightning-thief"` |
| `title` | string | Full title |
| `series` | enum | See Enums — Series |
| `book_number` | int | Position in series (1–5 for PJO) |
| `published_date` | date | Original publication date |
| `synopsis` | text | Full plot summary |
| `short_description` | string | One-line tagline |
| `narrator` | FK → Character | Percy Jackson for all PJO books |
| `main_characters` | FK[] → Character | Primary POV and quest characters |
| `antagonists` | FK[] → Character/Titan | Primary villains |
| `quests` | FK[] → Quest | Quests that occur in this book |
| `new_locations` | FK[] → Location | Locations introduced in this book |
| `cover_image_url` | string | Book cover image |
| `camp_bead_description` | string | The end-of-summer bead painted for this year (see below) |
| `type` | enum | `novel`, `companion`, `short_story_collection`, `myth_anthology` |

**Camp Bead Notes (V1 seed data):**

- Book 1 — Black bead with a green trident
- Book 2 — Golden Fleece symbol
- Book 3 — No bead (winter events, same year as Book 2)
- Book 4 — Intricate maze design
- Book 5 — Empire State Building with names of the deceased in tiny Greek letters

---

### 4.2 Character

The most complex and central model. Covers demigods, mortals, satyrs, nymphs, hunters, oracles, and non-god immortals.

| Field | Type | Description |
| --- | --- | --- |
| `id` | int | Primary key |
| `slug` | string | e.g. `"annabeth-chase"` |
| `name` | string | Full canonical name |
| `aliases` | string[] | Nicknames, false identities (e.g. "Annabeth Chase" → ["Wise Girl"]) |
| `type` | enum | See Enums — Character Type |
| `species` | enum | See Enums — Species |
| `gender` | enum | `male`, `female`, `non_binary`, `unknown` |
| `age_first_appearance` | int | Age at first book appearance |
| `status` | enum | `alive`, `deceased`, `immortal`, `transformed`, `unknown` |
| `greek_or_roman` | enum | `greek`, `roman`, `both`, `neither` (for V1, mostly `greek`) |
| `divine_parent` | FK → God | Olympian or minor god parent (null for mortals/satyrs) |
| `mortal_parent_name` | string | Name of mortal parent(s) |
| `mortal_parent_ref` | FK → Character | If mortal parent is a named character |
| `siblings` | FK[] → Character | Named siblings (divine and mortal) |
| `cabin_number` | int | Camp Half-Blood cabin (null if not a CHB camper) |
| `affiliation` | enum[] | See Enums — Affiliation (can have multiple) |
| `fatal_flaw` | string | E.g. "Excessive personal loyalty" (Percy), "Hubris/deadly pride" (Annabeth) |
| `powers` | Power[] | Nested array (see Power sub-model below) |
| `weapons` | FK[] → Weapon | Weapons carried or associated with |
| `can_see_through_mist` | boolean | True for Rachel Dare, Sally Jackson, etc. |
| `has_adhd` | boolean | Demigod trait |
| `has_dyslexia` | boolean | Demigod trait |
| `empathy_link` | FK → Character | Character they share an Empathy Link with |
| `appearance` | Appearance | Nested object (see below) |
| `personality_traits` | string[] | Array of descriptive traits |
| `quote` | string | Iconic quote from the character |
| `description` | text | Full lore description |
| `books_appeared_in` | FK[] → Book | Books this character appears in |
| `first_appearance_book` | FK → Book | First book they appear in |
| `image_url` | string | Primary character image |
| `image_alt` | string | Accessible image description |
| `is_big_three_child` | boolean | Child of Zeus, Poseidon, or Hades |
| `is_hunter_of_artemis` | boolean | Member of the Hunters |
| `is_oracle` | boolean | Hosts the Oracle of Delphi spirit |
| `wiki_url` | string | Riordan Wiki URL |

**Appearance sub-object:**

```json
{
  "hair_color": "black",
  "hair_description": "jet-black, messy",
  "eye_color": "sea-green",
  "build": "lean",
  "height": "average for age",
  "notable_features": ["often has a sarcastic smile", "tan skin"]
}
```

**Power sub-model:**

```json
{
  "name": "Hydrokinesis",
  "description": "The ability to control water",
  "source": "divine_parent",
  "scope": ["water", "sea", "ocean"],
  "limitations": "Weakened when far from water"
}
```

**Key V1 Characters (non-exhaustive seed list):**

*Demigods:*

- Percy Jackson (Poseidon)
- Annabeth Chase (Athena)
- Thalia Grace (Zeus)
- Nico di Angelo (Hades)
- Bianca di Angelo (Hades, deceased)
- Luke Castellan (Hermes, antagonist/redeemed)
- Clarisse La Rue (Ares)
- Charles Beckendorf (Hephaestus, deceased)
- Silena Beauregard (Aphrodite, deceased)
- Lee Fletcher (Apollo, deceased)
- Castor (Dionysus, deceased)
- Ethan Nakamura (Nemesis, deceased)
- Zoë Nightshade (daughter of Atlas, Hunter, deceased)
- Chris Rodriguez (Hermes)
- Michael Yew (Apollo)
- Malcolm (Athena)
- Tyson (Poseidon — Cyclops, half-brother of Percy)

*Mortals:*

- Sally Jackson (Percy's mother, can see through Mist)
- Rachel Elizabeth Dare (mortal, can see through Mist, becomes Oracle)
- Paul Blofis (Sally's fiancé/husband)
- Gabe Ugliano (Sally's abusive first husband, turned to statue)

*Satyrs / Non-demigod Beings:*

- Grover Underwood (satyr, Lord of the Wild, Council of Cloven Elders)
- Chiron (centaur, Camp Half-Blood director/trainer)
- Dionysus / Mr. D (camp director, Olympian god)
- Blackjack (Percy's pegasus)

*Hunters of Artemis:*

- Zoë Nightshade (lieutenant, deceased)
- Thalia Grace (joins after Book 3)
- Bianca di Angelo (briefly, deceased)

---

### 4.3 God

Covers all Olympians, minor gods, and primordial beings with divine status (not Titans — see 4.4).

| Field | Type | Description |
| --- | --- | --- |
| `id` | int | Primary key |
| `slug` | string | e.g. `"poseidon"` |
| `name` | string | Greek canonical name |
| `roman_name` | string | Roman equivalent name (e.g. Neptune) |
| `tier` | enum | `olympian`, `minor`, `primordial`, `chthonic` |
| `domains` | string[] | Areas of divine authority |
| `symbols` | string[] | Sacred symbols and attributes |
| `sacred_animals` | string[] | |
| `sacred_plants` | string[] | |
| `sacred_items` | string[] | |
| `weapon_or_item` | FK[] → Weapon | Divine weapons/items associated |
| `parents` | FK[] → God | Divine parents |
| `siblings` | FK[] → God | Divine siblings |
| `consort` | FK → God | Divine spouse or partner |
| `children_gods` | FK[] → God | Divine children |
| `children_demigods` | FK[] → Character | Named demigod children |
| `cabin_number` | int | Camp Half-Blood cabin number (null if no cabin) |
| `has_cabin` | boolean | Whether they have a cabin at CHB |
| `is_big_three` | boolean | Zeus, Poseidon, or Hades |
| `oath_status` | enum | `bound_by_oath`, `oath_dissolved`, `exempt`, `not_applicable` — relates to Big Three oath |
| `greek_aspect_personality` | text | Personality in Greek form |
| `roman_aspect_personality` | text | Personality in Roman form (prep for V2) |
| `affiliation` | enum | `olympian_council`, `neutral`, `titan_allied`, `chthonic` |
| `home` | string | Primary domain / residence (e.g. "Mount Olympus", "The Underworld", "The Sea") |
| `first_appearance_book` | FK → Book | |
| `books_appeared_in` | FK[] → Book | |
| `description` | text | Full lore write-up |
| `image_url` | string | |
| `wiki_url` | string | |

**The 12 Olympians (V1 seed):**

| # | Greek Name | Roman Name | Domain | Cabin |
| --- | --- | --- | --- | --- |
| 1 | Zeus | Jupiter | Sky, lightning, thunder, king of gods | 1 |
| 2 | Hera | Juno | Marriage, family, queen of gods | 2 (honorary, empty) |
| 3 | Poseidon | Neptune | Sea, earthquakes, horses | 3 |
| 4 | Demeter | Ceres | Agriculture, harvest, fertility | 4 |
| 5 | Ares | Mars | War, violence, courage | 5 |
| 6 | Athena | Minerva | Wisdom, warfare strategy, crafts | 6 |
| 7 | Apollo | Phoebus | Sun, music, poetry, truth, healing, archery | 7 |
| 8 | Artemis | Diana | Moon, hunt, wilderness, maidenhood | 8 (empty, Hunters only) |
| 9 | Hephaestus | Vulcan | Fire, forge, blacksmiths, craftsmen | 9 |
| 10 | Aphrodite | Venus | Love, beauty, desire | 10 |
| 11 | Hermes | Mercury | Travel, messengers, thieves, trade | 11 |
| 12 | Dionysus | Bacchus | Wine, madness, festivity | 12 |

**Additional Gods relevant to V1:**

- Hades (Pluto) — Underworld, dead — added Cabin 13 post-Last Olympian
- Hestia — Hearth — no cabin (gave up throne for Dionysus), fire pit in mess hall
- Persephone — Springtime, Underworld queen
- Iris — Rainbow, messages (Iris messages = magical communication)
- Hecate — Magic, crossroads, mist (relevant in Labyrinth)
- Hypnos — Sleep
- Nemesis — Revenge and balance
- Nike — Victory
- Hebe — Youth
- Tyche — Fortune
- Janus — Doorways (Roman god, appears in Labyrinth — flag as `roman_only: true`)
- Pomona — Trees and orchards (Roman, sides with Titans)
- Circe — Magic (minor goddess, operates a salon in Sea of Monsters)
- Phobos & Deimos — Fear and panic (sons of Ares)
- Melinoë — Ghosts (Underworld, Demigod Files)
- Triton — Sea messenger (Poseidon's son)
- Pan — Wild (faded during V1, searched for by Grover)

---

### 4.4 Titan

Titans are distinct from gods and deserve their own model due to their unique role as predecessors and antagonists.

| Field | Type | Description |
| --- | --- | --- |
| `id` | int | Primary key |
| `slug` | string | |
| `name` | string | |
| `domains` | string[] | Domains of power |
| `generation` | enum | `elder_titan`, `younger_titan` |
| `display_order` | integer, nullable | Curated list order; independent of the generation classification |
| `parents` | string[] | Ouranos (sky), Gaia (earth), or other Titans |
| `siblings` | FK[] → Titan | |
| `children` | FK[] → Titan or God | Divine offspring |
| `status` | enum | `imprisoned_tartarus`, `active`, `defeated`, `destroyed`, `faded` |
| `alignment` | enum | `kronos_army`, `neutral`, `olympian_allied` |
| `role_in_series` | text | Their function in the narrative |
| `prison_location` | string | Where they are imprisoned (if applicable) |
| `weapon_or_power` | string[] | Notable powers or items |
| `books_appeared_in` | FK[] → Book | |
| `description` | text | |
| `image_url` | string | |

**Key V1 Titans:**

- Kronos — Time; supreme antagonist; possesses Luke Castellan; defeated at end of Book 5
- Atlas — Heavens (holds up the sky); general of Titan army; imprisoned at Mt. Othrys (San Francisco)
- Hyperion — Light and the East; general; defeated in Battle of Manhattan (turned into a maple tree)
- Iapetus (Bob) — Mortality; stripped of memory in River Lethe; becomes friendly to Percy
- Oceanus — Sea Titan; fights Poseidon in underwater front
- Prometheus — Forethought; parley envoy for Kronos
- Koios & Krios — Titanesses imprisoned in Tartarus; freed briefly in Last Olympian

---

### 4.5 Monster

| Field | Type | Description |
| --- | --- | --- |
| `id` | int | Primary key |
| `slug` | string | |
| `name` | string | |
| `aliases` | string[] | Alternate names or disguise names (e.g. Medusa → "Aunty Em") |
| `type` | enum | See Enums — Monster Type |
| `origin_myth` | text | The original Greek myth origin story |
| `physical_description` | text | Appearance in the series |
| `abilities` | string[] | Powers and attacks |
| `weaknesses` | string[] | Known vulnerabilities |
| `allegiance` | enum | `kronos_army`, `olympian_ally`, `neutral`, `independent`, `hades_servant` |
| `can_reform` | boolean | Whether they reform after death |
| `reform_time` | string | How long reformation takes (e.g. "months", "days", "instantly") |
| `reform_location` | string | Usually Tartarus |
| `spoils_of_war` | string | Trophy left behind on death |
| `parent_entity` | string | Mythological parentage (e.g. "Phorcys and Ceto" for Medusa) |
| `notable_victims` | string[] | Named characters they harmed |
| `defeated_by` | FK[] → Character | Who ultimately defeats them in V1 |
| `first_appearance_book` | FK → Book | |
| `books_appeared_in` | FK[] → Book | |
| `disguise_form` | string | Human disguise used (e.g. "Middle Eastern woman running garden centre") |
| `description` | text | |
| `image_url` | string | |
| `wiki_url` | string | |

**Key V1 Monsters (by book):**

*Book 1 — The Lightning Thief:*

- The Minotaur (Asterion) — half-bull/half-man; defeated by Percy with its own horn
- The Furies (Alecto, Tisiphone, Megaera) — Hades' servants; disguised as teachers/bats
- Medusa — Gorgon; disguised as "Aunty Em"; defeated by Percy (decapitation)
- Chimera — lion/goat/snake hybrid; attacks at St. Louis Arch
- Echidna — Mother of All Monsters; appears with Chimera
- Procrustes (Crusty) — stretching bed monster; defeated by Percy
- Ares (antagonist role, not a monster but acts as one)
- Cerberus — three-headed dog guardian of Underworld
- Charon — ferryman of the dead
- The Fates — appear cutting thread of life at beginning

*Book 2 — The Sea of Monsters:*

- Polyphemus — cyclops; holds Grover captive with Golden Fleece
- Hydra — many-headed; destroyed by Clarisse's ship cannon, then by Medusa's head (film)/defeated at Parthenon
- Charybdis & Scylla — sea monsters; Clarisse navigates between them
- Stymphalian Birds — metal-feathered birds at Chesapeake Bay
- Laistrygonian Giants (Canadian cannibals) — attack Percy's school dodgeball game
- Colchis Bulls — fire-breathing mechanical bulls guarding the Fleece
- Circe — turns Percy into guinea pig

*Book 3 — The Titan's Curse:*

- The Manticore (Dr. Thorn) — lion body, human face, scorpion tail; disguised as school vice principal
- The Nemean Lion — golden fur, impervious hide
- Erymanthian Boar — enormous wild boar; gift from Pan
- The Skeleton Warriors / Spartoi — soldiers grown from dragon teeth
- Geryon — three-bodied rancher at Triple G Ranch
- Orthus — two-headed guard dog of Geryon
- The Ophiotaurus — bull-serpent; its entrails could destroy Olympus
- The Atlas-held sky — not a monster but a trap/location

*Book 4 — The Battle of the Labyrinth:*

- Kampê — ancient jailer of Tartarus; most fearsome monster guarding the Cyclopes
- Antaeus — giant son of Gaia; unbeatable while touching the earth (arena in Labyrinth)
- Sphinx — riddle-asking creature at Labyrinth entrance
- The Telekhines — sea-demon smiths reforging Kronos's scythe
- Dracaenae — serpent women soldiers of Kronos's army
- Hellhounds — various
- Keres — death spirits; dark battle spirits
- Automaton Giant Bronze Dragon (Festus's prototype — unnamed)
- Calypso's island as narrative trap (not a monster)
- Luke / Kronos forces — Kronos begins rising

*Book 5 — The Last Olympian:*

- Typhon — greatest monster ever; marches across America, fights the gods
- Hyperion — Titan general in Manhattan
- Kronos (possessing Luke) — supreme antagonist
- The Giant Squid — briefly appears, dealt with by Poseidon
- The Drakon — Lydian Drakon; massive serpent used as army weapon; slain by Clarisse
- Morpheus — god of sleep; puts Manhattan to sleep
- Various Titans and monsters of Kronos's army

---

### 4.6 Creature / Species

Covers named species and creature-types that are not individual monsters but appear in the series.

| Field | Type | Description |
| --- | --- | --- |
| `id` | int | |
| `slug` | string | |
| `name` | string | e.g. "Satyr", "Centaur", "Cyclops", "Harpy" |
| `description` | text | What they are and their role in the world |
| `origin` | string | Greek mythological origin |
| `alignment` | enum | Generally what side they're on |
| `notable_members` | FK[] → Character | Named individuals of this species |
| `abilities` | string[] | |
| `weaknesses` | string[] | |
| `habitat` | string | Where they're typically found |
| `image_url` | string | |

**V1 Species to seed:**
Satyr, Centaur, Cyclops, Harpy, Fury (Erinye), Nymph (tree/naiad/nereid subtypes), Pegasus, Hellhound, Dracaena, Laistrygonian Giant, Gorgon, Automaton, Skeleton Warrior (Spartoi), Empousai, Telekhine

---

### 4.7 Weapon & Magical Item

Covers divine weapons, demigod weapons, and magical artifacts encountered across V1.

| Field | Type | Description |
| --- | --- | --- |
| `id` | int | |
| `slug` | string | e.g. `"riptide"` |
| `name` | string | Common name |
| `true_name` | string | Ancient name (e.g. Riptide → "Anaklusmos") |
| `type` | enum | See Enums — Weapon Type |
| `material` | enum | See Enums — Material |
| `form` | string[] | Forms it can take (e.g. ballpoint pen / sword) |
| `transforms` | boolean | Whether it can change form |
| `transform_trigger` | string | How the transformation is activated (e.g. "uncapping the pen") |
| `abilities` | string[] | Special powers or properties |
| `owner_primary` | FK → Character, God, or Titan | Current/primary owner |
| `owner_history` | JSON history | Previous owners and transfer notes |
| `origin_story` | text | How it was made or obtained |
| `forged_by` | FK → God or Character | Who made it (often Hephaestus, Daedalus, or Tyson) |
| `passes_through_mortals` | boolean | True for Celestial Bronze weapons |
| `first_appearance_book` | FK → Book | |
| `books_appeared_in` | FK[] → Book | |
| `description` | text | |
| `image_url` | string | |
| `wiki_url` | string | |

**Key V1 Weapons & Magical Items:**

*Weapons:*

- Riptide (Anaklusmos) — Percy's Celestial Bronze sword; disguised as ballpoint pen; always returns to owner's pocket
- Annabeth's Celestial Bronze Dagger — given to her by Luke as a child; later used by Luke to kill himself (cursed blade)
- Thalia's Spear (Aegis) — transforms into a shield (Aegis) bearing a horrifying Medusa face; Zeus's shield imprint
- Nico's Stygian Iron Sword — forged from Stygian iron; extremely painful to mortals; kills undead
- Clarisse's Electric Spear (Maimer / "Lamer") — gift from Ares; electrocutes enemies
- Zoë Nightshade's Silver Bow and Arrows — as a Hunter of Artemis
- Backbiter — Luke's sword; half Celestial Bronze, half mortal steel; the only weapon that can harm both mortals and immortals; later transformed into Kronos's scythe
- Kronos's Scythe — remade from Backbiter; weapon of the Titan lord

*Divine Weapons:*

- Zeus's Master Lightning Bolt — most powerful weapon in the world; hidden inside Ares's backpack
- Poseidon's Trident — symbol of sea power
- Hades's Helm of Darkness — makes wearer invisible; stolen at start of Book 1
- Artemis's Silver Bow
- Apollo's Golden Bow
- Ares's War Spear

*Magical Items:*

- Annabeth's Yankees Cap — makes wearer invisible; gift from Athena
- Hermes's Winged Shoes — wings spring out on the word "Maia"; given to Percy by Luke, passed to Grover
- Medusa's Severed Head — turns anything it faces to stone; used by Sally to petrify Gabe
- Golden Fleece — healing artifact from the Ram of Chrysomallus; hung on the tree of the Hesperides; carried by the Fleece
- Ariadne's String — used to navigate the Labyrinth; found by Annabeth
- The Labyrinth — not a weapon but a sentient magical construct; linked to Daedalus's life
- Iris Messages — magical rainbow communication (requires drachma and mist/rainbow)
- Persephone's Pearls — 3 green pearls that allow escape from the Underworld
- Achilles's Blessing (River Styx) — renders Percy invulnerable except at one mortal point (small of back)
- Grover's Wooden Pipes — satyr instrument that channels nature magic

---

### 4.8 Location

| Field | Type | Description |
| --- | --- | --- |
| `id` | int | |
| `slug` | string | |
| `name` | string | |
| `type` | enum | See Enums — Location Type |
| `real_world_location` | string | Mortal equivalent (e.g. "Long Island, New York") |
| `mythological_significance` | text | Why this place matters in Greek myth |
| `description` | text | Full lore description |
| `controlled_by` | FK → God/Titan/Character | Who rules or inhabits this place |
| `notable_events` | string[] | Key events that took place here |
| `books_appeared_in` | FK[] → Book | |
| `first_appearance_book_slug` | string, nullable | Slug of the Book of the first physical on-page appearance |
| `first_appearance_locator` | string, nullable | Chapter/section locator for that appearance |
| `earlier_mention_book_slug` | string, nullable | Earlier Book mention that precedes a physical visit, if any |
| `location_order` | integer, nullable | Curated first-appearance order across the seeded series |
| `is_hidden_from_mortals` | boolean | Whether the Mist conceals it |
| `coordinates_approx` | string | Approximate real-world location (for future map feature) |
| `image_url` | string | |
| `wiki_url` | string | |

**Key V1 Locations:**

*Camp Half-Blood:*

- Camp Half-Blood — Long Island, NY; the main demigod training ground; protected by Thalia's Pine Tree

*Olympus:*

- Mount Olympus — sits atop the Empire State Building, 600th floor, New York City (westernmost point of Western civilization)
- Council Chamber of the Gods

*The Underworld:*

- The Underworld — beneath Los Angeles (DOA Recording Studios as entrance)
- The Fields of Asphodel — where neutral souls wander
- Elysium — paradise for heroic souls
- Tartarus — deepest pit; prison of Titans and monsters
- The River Styx — most sacred oath-binding river
- The River Lethe — causes total memory loss
- Charon's Ferry — River Styx crossing
- Hades's Palace

*Quest Locations (Book 1):*

- Yancy Academy — Percy's school in upstate New York
- Medusa's Garden Emporium — New Jersey
- St. Louis Arch — site of Chimera/Echidna battle
- Lotus Hotel & Casino — Las Vegas; time-suspension trap
- Hollywood, CA — Entrance to the Underworld

*Quest Locations (Book 2):*

- Camp Half-Blood
- Princess Andromeda (Luke's ship)
- Chesapeake Bay — Stymphalian Birds
- Sea of Monsters (Bermuda Triangle) — location of Golden Fleece
- Polyphemus's Island — inside Sea of Monsters
- Circe's Island / C.C.'s Spa and Resort

*Quest Locations (Book 3):*

- Westover Hall — military school in Maine (Bianca and Nico found here)
- Smithsonian Air and Space Museum, Washington D.C.
- Junkyard of the Gods — Nevada desert
- Triple G Ranch — Texas; owned by Geryon
- San Francisco / Mount Tamalpais (Othrys) — Atlas imprisoned here; Artemis held here
- Garden of the Hesperides

*Quest Locations (Book 4):*

- The Labyrinth — sentient underground maze built by Daedalus; entrance at Camp Half-Blood rocks
- Daedalus's Workshop — various underground locations
- Alcatraz — Briares was imprisoned here
- Mount St. Helens — Hephaestus's forge; Percy triggers eruption; ends up on Ogygia
- Ogygia — Calypso's island; no fixed location
- Antaeus's Arena — underground fighting ring

*Quest Locations (Book 5):*

- Manhattan — primary battleground of the Last Olympian war
- Williamsburg Bridge — key battle location
- Central Park — Grover's forest protection zone
- The Princess Andromeda — destroyed in the opening
- River Styx — Percy bathes here for Achilles's blessing
- Empire State Building / Olympus — final battle

*Other Notable:*

- The Sea of Monsters (Bermuda Triangle) — dangerous mythological sea zone
- Island of Ogygia — Calypso's prison island; cannot be found twice the same way
- Mount Othrys — Titan base, reformed in San Francisco
- The Council of Cloven Elders — Grover's governing body

---

### 4.9 Quest

| Field | Type | Description |
| --- | --- | --- |
| `id` | int | |
| `slug` | string | |
| `title` | string | e.g. "The Quest for Zeus's Lightning Bolt" |
| `book` | FK → Book | Which book this quest takes place in |
| `prophecy` | FK → Prophecy | The Oracle prophecy that initiated the quest |
| `led_by` | FK → Character | Quest leader |
| `participants` | FK[] → Character | All quest members |
| `objective` | text | What the quest is trying to achieve |
| `outcome` | text | What actually happened |
| `locations_visited` | FK[] → Location | |
| `monsters_encountered` | FK[] → Monster | |
| `items_recovered` | FK[] → Weapon | Magical items found or returned |
| `casualties` | FK[] → Character | Deaths during the quest |
| `initiated_by` | string | Who or what started the quest (usually Oracle) |
| `description` | text | |

**V1 Quests:**

1. Quest for Zeus's Lightning Bolt (Book 1) — Percy, Annabeth, Grover
2. Quest for the Golden Fleece (Book 2) — Clarisse (official), Percy, Annabeth, Tyson, Grover (unofficial)
3. Quest for Artemis (Book 3) — Zoe, Bianca, Grover, Thalia, Percy
4. Quest through the Labyrinth (Book 4) — Percy, Annabeth, Grover, Tyson, Nico
5. Defense of Olympus / Battle of Manhattan (Book 5) — Percy leads, all campers

---

### 4.10 Cabin

Each cabin at Camp Half-Blood represents a deity and houses their demigod children.

| Field | Type | Description |
| --- | --- | --- |
| `id` | int | |
| `number` | int | Cabin number (1–20 after Last Olympian) |
| `slug` | string | e.g. `"cabin-3-poseidon"` |
| `deity` | FK → God | The god this cabin honors |
| `is_honorary` | boolean | True for Hera (no children) and Artemis (no demigod children) |
| `is_empty` | boolean | Whether it currently has any campers |
| `architecture_description` | text | What the cabin looks like (lore-accurate) |
| `known_campers` | FK[] → Character | Named characters who live here |
| `head_counselor` | FK → Character | Current head counselor |
| `added_in_book` | FK → Book | When this cabin was added (original 12 vs. post-Last Olympian) |
| `position` | string | Left or right side of camp (odd = left/male, even = right/female) |

**V1 Cabins (1–12, original) with architecture notes from the Riordan Wiki:**

1. Zeus — massive, looks like a mausoleum; bronze double doors with holographic lightning bolts; biggest cabin
2. Hera — honorary, no furniture; strictly a tribute; no children ever stay here
3. Poseidon — rough sea stone with coral and seashell embedded in walls; trident and #3 over the door; smells of the sea; saltwater fountain inside
4. Demeter — flower-covered; green exterior
5. Ares — barbed wire perimeter, angry red walls, rock music blaring; campers are aggressive
6. Athena — neat and orderly; grey/silver tones; bookshelves
7. Apollo — sunny, bright gold; musical instruments inside
8. Artemis — empty except when Hunters visit; silver tones; archery-themed
9. Hephaestus — industrial, forge-like; fire-proof; machine parts and tools
10. Aphrodite — pink, heart-shaped mirrors; beauty products; most glamorous
11. Hermes — the default cabin; overcrowded; any unclaimed demigod stays here; posters and maps on walls; welcoming policy
12. Dionysus — grapevines lining the roof and walls; only green-lit interior

**Post-Last Olympian additions (13–20):**
13. Hades — solid obsidian with heavy columns; green Greek fire torches burn 24/7; skull over the door; Nico's cabin
14. Iris — rainbow-colored; tie-dye; wind chimes
15. Hypnos — dark, quiet; campers spend most of their time sleeping
16. Nemesis — balance-themed; scales imagery
17. Nike — victory trophies; athletic equipment
18. Hebe — youthful, playful décor
19. Tyche — fortune-themed; lucky charms
20. Hecate — mysterious; magical artefacts; crossroads imagery

---

### 4.11 Prophecy

| Field | Type | Description |
| --- | --- | --- |
| `id` | int | |
| `slug` | string | |
| `title` | string | e.g. "The Great Prophecy" |
| `text` | text | Full prophecy lines |
| `delivered_by` | FK → Character | The Oracle who delivered it |
| `oracle_type` | string | "Oracle of Delphi", etc. |
| `subject` | FK[] → Character | Who the prophecy is about |
| `fulfilled_in` | FK → Book | Book in which it was fulfilled |
| `interpretation_notes` | text | How it was ultimately interpreted |
| `books_relevant_to` | FK[] → Book | |
| `description` | text | |

**V1 Prophecies:**

- The Great Prophecy — "A half-blood of the eldest gods shall reach sixteen against all odds..." — the central prophecy of the entire PJO series, fulfilled in Book 5 (Percy chooses to give Luke the knife)
- The Titan's Curse Prophecy — "Five shall go west to the goddess in chains..." — Books 3
- Sea of Monsters Prophecy — relates to the Golden Fleece quest
- Per-book Oracle warnings / minor prophecies from the Oracle at Camp Half-Blood

---

### 4.12 Event / Battle

Key named battles and significant events in the lore.

| Field | Type | Description |
| --- | --- | --- |
| `id` | int | |
| `slug` | string | |
| `name` | string | e.g. "Battle of Manhattan" |
| `type` | enum | `battle`, `war`, `quest_event`, `political_event`, `sacrifice` |
| `in_universe_timeframe` | string, nullable | Human-readable in-universe timeframe; not publication date |
| `date_precision` | enum | `exact`, `approximate`, `relative_period`, `mythological_era`, `disputed`, `unknown` |
| `date_precision_display` | string | Human-readable label for `date_precision` |
| `chronology_order` | integer, nullable | Curated timeline order; overlapping events may have sequential display positions |
| `book` | FK → Book | |
| `location` | FK → Location | |
| `participants_olympian` | FK[] → Character or God | |
| `participants_titan` | FK[] → Titan or Character | |
| `outcome` | text | |
| `casualties` | FK[] → Character | |
| `significance` | text | Why this event matters in the lore |
| `description` | text | |

**Key V1 Events:**

- Theft of the Master Lightning Bolt (precedes Book 1)
- The First Titan War (backstory — Olympians vs. Kronos)
- World War II (demigod conflict mirroring the mortal world)
- The Big Three Oath (post-WWII)
- Battle at the Museum (Alecto attack, Book 1)
- The Duel with Ares (Book 1)
- The Battle at Camp Half-Blood (end of Book 2)
- The Fall of Thalia's Tree (beginning of Book 2)
- Death and Resurrection of Thalia Grace
- Battle of the Labyrinth (end of Book 4)
- Beckendorf's Sacrifice (opening of Book 5)
- Battle of Manhattan / Second Titan War (Book 5)
- Luke Castellan's Sacrifice and Death (Book 5)
- Percy Refuses Immortality (Book 5)
- The Minor Gods Reform Decree (Book 5)

---

### 4.13 Faction / Affiliation

Named groups within the lore.

| Field | Type | Description |
| --- | --- | --- |
| `id` | int | |
| `slug` | string | |
| `name` | string | e.g. "Camp Half-Blood", "The Hunters of Artemis", "Titan Army" |
| `type` | enum | `camp`, `army`, `order`, `group`, `council`, `family` |
| `leader` | FK → Character or God | |
| `members` | FK[] → Character | Named members |
| `alignment` | enum | `olympian`, `titan`, `neutral`, `independent` |
| `description` | text | |
| `books_active_in` | FK[] → Book | |

**Key V1 Factions:**

- Camp Half-Blood — Greek demigod training camp, Long Island
- The Hunters of Artemis — immortal band of maidens pledged to Artemis
- The Titan Army (Kronos's forces) — includes monsters, enemy demigods, minor gods
- Council of Cloven Elders — satyr governing council
- The Olympian Council — the 12 Olympians + Hades
- The Council of Olympus — formal political body on Mount Olympus

---

## 5. Relationships & Linking Strategy

The diagram below describes implemented relationships and their public API projections. Relationship data is exposed through entity details and nested subresources; there is no standalone CRUD endpoint for `DivineRelationship`, Book cast relationships, `FactionMember`, or `ProphecySubject`.

```text
Book ────────── parent_collection / included_stories ───▶ Book
Book ────────── narrators / main_characters / antagonists ▶ Character, God, Titan, Monster, Creature
Book ────────── characters subresource ──────────────────▶ Character list

God / Titan / Character / Monster / Creature
               └─ family ───────────────────────────────▶ parents, siblings, consorts, children
                  (typed {name, type, slug} references; shared DivineRelationship graph)

Character ──── weapons / quests ────────────────────────▶ Weapon[] / Quest[]
Character ──── cabin / divine parent / siblings ─────────▶ related entities

Quest ──────── participants / casualties ───────────────▶ Character, God, Titan, Monster
Quest ──────── locations / monsters / items ────────────▶ Location[], Monster[], Weapon[]
Quest ──────── prophecy / book ──────────────────────────▶ Prophecy / Book
Event ──────── participants / casualties ──────────────▶ Character, God, Titan, Monster

Prophecy ───── subjects ────────────────────────────────▶ Character, God, Titan, Monster
Faction ────── members / leader ────────────────────────▶ Character, God, Titan, Monster
Location ───── controlled_by ───────────────────────────▶ God, Titan, Character, Monster
Weapon ─────── owner_primary / forged_by ───────────────▶ Character, God, Titan
Monster ────── defeat records ──────────────────────────▶ Character (MonsterDefeat) and God links
Image ──────── typed image join ────────────────────────▶ Book, Character, God, Titan, Monster, Weapon, Location
```

---

## 6. Enumerations (Enums)

> This section includes historical planning vocabularies. Filter values actually accepted by each list endpoint are the model/filter choices in Section 23; do not treat a listed proposal as supported unless it appears there.

### Series

`percy_jackson_and_the_olympians`, `heroes_of_olympus`, `kane_chronicles`, `trials_of_apollo`, `magnus_chase`, `nico_di_angelo_adventures`, `senior_year_adventures`, `companion`, `short_story`

### Book Type

`novel`, `companion_book`, `short_story_collection`, `myth_anthology`, `graphic_novel`

### Character Type

`demigod`, `god`, `titan`, `monster`, `mortal`, `satyr`, `centaur`, `cyclops`, `nymph`, `hunter`, `oracle`, `legacy`, `automaton`, `spirit`, `primordial`

### Species

`human`, `demigod`, `satyr`, `centaur`, `cyclops`, `pegasus`, `nymph`, `naiad`, `nereid`, `harpy`, `fury`, `gorgon`, `dracaena`, `telekhine`, `giant`, `automaton`, `other`

### Status

`alive`, `deceased`, `immortal`, `transformed`, `imprisoned`, `faded`, `unknown`

### Affiliation

`camp_half_blood`, `hunters_of_artemis`, `olympian_council`, `titan_army`, `neutral`, `underworld`, `council_of_cloven_elders`, `kronos_army`

### God Tier

`olympian`, `minor`, `chthonic`, `primordial`, `river_god`, `nature_deity`

### Material

`celestial_bronze`, `composite`, `flint`, `gold`, `imperial_gold`, `mortal_steel`, `other`, `silver`, `stygian_iron`, `divine_material`, `enchanted`, `wood`

### Weapon Type

`sword`, `spear`, `dagger`, `bow`, `shield`, `trident`, `scythe`, `club`, `staff`, `helm`, `whip`, `arrows`, `magical_item`, `artifact`

### Monster Type

`gorgon`, `cyclops`, `giant`, `sea_monster`, `underworld_creature`, `chimeric`, `undead`, `nature_spirit`, `shapeshifter`, `mechanical`

### Location Type

`camp`, `olympus`, `underworld`, `mortal_city`, `mythical_island`, `labyrinth`, `sea`, `mountain`, `forest`, `hotel_or_building`, `divine_realm`, `crossroads`

### Titan Alignment

`kronos_army`, `neutral`, `olympian_allied`, `independent`

---

## 7. API Endpoints (v1)

> **Current contract:** the complete tested route and response inventory is in Section 23. The examples in this original endpoint-planning section are incomplete; where they differ, Section 23 is authoritative.

All versioned API endpoints are prefixed with `/api/v1/` and end with a trailing slash. Infrastructure health and key-management routes are outside the versioned API. The legacy per-resource snippets below use shortened paths for readability; prepend `/api/v1` and add a trailing slash. Section 23 is the canonical route list and corrects paths that changed since these examples were first drafted.

### Health Checks

```bash
GET    /health/live/                 Process liveness; no dependency checks
GET    /health/ready/                Readiness; checks the required database dependency
```

Liveness returns `200` while the application process can respond. Readiness runs a lightweight `SELECT 1` against the default database and returns `503 Service Unavailable` when that required dependency cannot be reached. The Redis cache is not a hard service dependency: API-key validation falls back to PostgreSQL and throttling falls back to process-local memory during a Redis outage. Readiness therefore does not fail solely because Redis is unavailable.

Health endpoints are unauthenticated, unthrottled, and return `Cache-Control: no-store`. They do not expose exception details. Uptime is intentionally omitted because per-worker process uptime is not equivalent to service uptime; obtain service uptime from deployment monitoring.

Example liveness response:

```json
{
  "status": "ok",
  "version": "0.1.0"
}
```

Example readiness response:

```json
{
  "status": "ok",
  "checks": {
    "database": "connected"
  },
  "version": "0.1.0"
}
```

When the database is unavailable, readiness returns HTTP 503 with `status: "not_ready"` and `checks.database: "unavailable"`.

### Authentication — API Key Registration

```bash
POST   /auth/request-key/            Self-service API key registration
```

Request body:

```json
{
  "consumer_name": "My Fan App",
  "email": "dev@example.com"
}
```

Response (`201 Created`; key shown once only):

```json
{
  "api_key": "<generated-api-key>",
  "consumer_name": "My Fan App",
  "email": "dev@example.com",
  "message": "Your API key has been created."
}
```

All other endpoints require:

```http
X-API-Key: <your-key>
```

### Books

```http
GET    /books                        List all books (filterable by series, type)
GET    /books/:slug                  Get a single book
GET    /books/:slug/characters       All characters in a book
GET    /books/:slug/gods             All gods appearing in a book
GET    /books/:slug/quests           Quests in a book
GET    /books/:slug/monsters         Monsters appearing in a book
GET    /books/:slug/locations        Locations visited in a book
```

### Characters

```http
GET    /characters                   List all characters
GET    /characters/:slug             Get a single character
GET    /characters/:slug/weapons     Weapons associated with character
GET    /characters/:slug/quests      Quests this character participated in
GET    /characters?type=demigod
GET    /characters?divine_parent=poseidon
GET    /characters?cabin=3
GET    /characters?affiliation=hunters_of_artemis
GET    /characters?is_big_three_child=true
GET    /characters?book=the-lightning-thief
GET    /characters?status=deceased
```

### Gods

```http
GET    /gods                         List all gods
GET    /gods/:slug                   Get a single god
GET    /gods/:slug/children          All demigod children
GET    /gods/:slug/weapons           Divine weapons/items
GET    /gods?tier=olympian
GET    /gods?tier=minor
GET    /gods?has_cabin=true
```

### Titans

```http
GET    /titans                       List all Titans
GET    /titans/:slug                 Get a single Titan
GET    /titans?alignment=kronos_army
GET    /api/v1/titans/?status=imprisoned
GET    /api/v1/titans/?sort=display_order&order=asc
```

### Monsters

```http
GET    /monsters                     List all monsters
GET    /monsters/:slug               Get a single monster
GET    /monsters?book=the-lightning-thief
GET    /monsters?type=gorgon
GET    /monsters?allegiance=kronos_army
GET    /monsters?can_reform=true
GET    /monsters?defeated_by=percy-jackson
```

### Weapons & Items

```http
GET    /weapons                      List all weapons and items
GET    /weapons/:slug                Get a single weapon/item
GET    /weapons?type=sword
GET    /weapons?material=celestial_bronze
GET    /weapons?owner_character=percy-jackson
GET    /weapons?owner_god=poseidon
GET    /weapons?owner_titan=kronos
GET    /weapons?forged_by=hephaestus
GET    /weapons?transforms=true
```

### Locations

```http
GET    /locations                    List all locations
GET    /locations/:slug              Get a single location
GET    /locations?type=underworld
GET    /locations?book=the-titan-s-curse
GET    /locations?first_appearance_book=the-lightning-thief
GET    /locations?sort=location_order&order=asc
GET    /locations?is_hidden_from_mortals=true
```

### Quests

```http
GET    /quests                       List all quests
GET    /quests/:slug                 Get a single quest
GET    /quests/:slug/participants    All characters on a quest
GET    /quests?book=the-sea-of-monsters
GET    /quests?led_by=percy-jackson
```

### Cabins

```http
GET    /cabins                       List all cabins
GET    /cabins/number/<number>/      Get a single cabin by number
GET    /cabins/:slug                 Get a single cabin by slug
GET    /cabins/:slug/campers         All known campers
```

### Prophecies

```http
GET    /prophecies                   List all prophecies
GET    /prophecies/:slug             Get a single prophecy
```

### Events

```http
GET    /events                       List all events/battles
GET    /events/:slug                 Get a single event
GET    /events?type=battle
GET    /events?book=the-last-olympian
GET    /events?date_precision=exact
GET    /events?sort=chronology_order&order=asc
```

### Factions

```http
GET    /factions                     List all factions
GET    /factions/:slug               Get a single faction
GET    /factions/:slug/members       All members
```

### Creatures / Species

```http
GET    /creatures                    List all species
GET    /creatures/:slug              Get a single species
GET    /creatures/:slug/members      Named individuals of that species
```

### Images (Global collection and entity galleries)

```http
GET    /images                                           Paginated global image collection
GET    /images?source_type=wiki&source_url=<encoded-url>
GET    /images?wiki_url=<encoded-file-page-url>

GET    /characters/:slug/images                          All images for a character
GET    /characters/:slug/images?source_type=official_book
GET    /characters/:slug/images?source_type=fan_art
GET    /characters/:slug/images?source_type=disney_plus
GET    /characters/:slug/images?category=portrait
GET    /characters/:slug/images?category=full_body

GET    /gods/:slug/images                                All images for a god
GET    /gods/:slug/images?source_type=fan_art
GET    /gods/:slug/images?category=concept_art

GET    /weapons/:slug/images                             All images for a weapon/item
GET    /weapons/:slug/images?source_type=official_book
GET    /weapons/:slug/images?category=weapon_closeup

GET    /monsters/:slug/images
GET    /locations/:slug/images
GET    /locations/:slug/images?category=concept_art
GET    /books/:slug/images
```

Filters can be combined on any image endpoint:

```http
GET    /characters/annabeth-chase/images?source_type=official_book&category=portrait
```

### Search (Global)

```http
GET    /search?q=riptide             Global search across all models
GET    /search?q=poseidon&type=god   Search within a model type
```

---

## 8. Filtering, Sorting & Pagination

> **Current contract:** Section 23 lists supported filters, field allowlists, actual default ordering, strict value rules, and pagination. The older examples in this section include proposals that are not implemented; Section 23 is authoritative.

List endpoints that use DRF pagination support `page` and `limit` (20 default; maximum 100).

### Pagination

```http
?page=1&limit=20          Default: page 1, 20 results
?page=2&limit=50          Max limit: 100
```

Response envelope:

```json
{
  "data": [...],
  "meta": {
    "total": 150,
    "page": 1,
    "limit": 20,
    "total_pages": 8
  }
}
```

### Sorting

List endpoints that declare `sort` fields in Section 23 accept `?sort=<field>[&order=asc|desc]` to override the default; if omitted, `order` defaults to `asc`. The allowlist is endpoint-specific; image galleries do not declare a `sort`/`order` allowlist. Supplying `order` without `sort` is invalid. Views using DRF's ordering backend may retain legacy `?ordering=` behavior where noted in Section 23. Example:

```http
?sort=name&order=asc
?sort=book_number&order=desc
?sort=age_first_appearance
```

#### Default Sort Order Per Endpoint — Original Proposal

> The rationale/examples below are historical design notes, not the current defaults. Use the implemented defaults and per-view allowlists in Section 23. The proposed Titan and Event fields are now implemented; Event chronology sorts by `chronology_order`, while `in_universe_timeframe` is a descriptive label.

---

##### Books — Original Proposal

**`book_number` ascending (1 → 5)**

The only logical default. A reader always wants chronological order. Companion works sort after the main series entry they are associated with.

---

##### Characters — Original Proposal

**`name` ascending (A → Z)**

Characters function as an encyclopedia — alphabetical is the most intuitive default for lookup. Filtering by `type=demigod` or `book=` already gives context-specific ordering when needed.

---

##### Gods — Original Proposal

**`tier` weight first, then `name` ascending within tier**

Olympians are the most important and recognisable — Zeus through Dionysus should lead. Minor gods, chthonic, and primordials follow. Within each tier, alphabetical.

Tier weight order: `olympian` → `minor` → `chthonic` → `primordial`

---

##### Titans — Original Proposal

**`display_order` ascending, then `name` ascending**

Canonical lore importance does not map cleanly to alphabetical or chronological, so Titan has a manual `display_order` integer field. Kronos leads as the primary antagonist, followed by Atlas, Hyperion, and the remaining named Titans.

> **Note:** This is the rationale for adding a `display_order` field to the `Titan` model.

---

##### Monsters — Original Proposal

**`first_appearance_book__book_number` ascending, then `name` ascending within book**

Monsters are most meaningful in the context of when they appear in the story. Book 1 monsters first, Book 5 last. Alphabetical within each book.

---

##### Weapons & Magical Items

**`name` ascending (A → Z)**

Weapons are reference data — alphabetical works best for browsing. Filtering by `owner` or `material` is how users find what they need contextually.

---

##### Locations — Original Proposal

**`first_appearance_book__book_number` ascending, then `name` ascending**

Same logic as monsters — locations are tied to the journey. Camp Half-Blood and Olympus appear early and lead naturally.

---

##### Quests — Original Proposal

**`book__book_number` ascending**

Quests are strictly chronological. Quest 1 through Quest 5 in story order.

---

##### Cabins — Original Proposal

**`number` ascending (1 → 20)**

Cabin number is canonical and universally understood by fans. Always sort 1 through 20.

---

##### Prophecies — Original Proposal

**`books_relevant_to__book_number` ascending**

The Great Prophecy spans all 5 books and should lead. Sub-prophecies follow in the book order they are delivered.

---

##### Events / Battles

**`book__book_number` ascending, then `in_universe_timeframe` ascending within book**

Events are inherently a timeline — chronological is the only default that makes sense. This is also the primary rationale for the `in_universe_timeframe` field: multiple major events occur within the same book (e.g. Book 5 contains Beckendorf's sacrifice, the Battle of Manhattan, Luke's death, and Percy refusing immortality) and need explicit ordering within that book.

> **Historical note:** the current Event model exposes `in_universe_timeframe` as a descriptive label, `date_precision` for uncertainty, and `chronology_order` as the sortable integer. The current contract is documented in Section 23.

---

##### Factions — Original Proposal

**`alignment` weight first, then `name` ascending within alignment**

Camp Half-Blood and the Olympian Council should lead since they are the protagonist side. Neutral factions follow. Titan Army last. Alphabetical within each group.

Alignment weight order: `olympian` → `neutral` → `independent` → `titan`

---

##### Creatures / Species — Original Proposal

**`name` ascending (A → Z)**

Species are pure reference data. Alphabetical is simplest and most useful for browsing.

---

#### Current Default Sort Summary

Section 23 is the single source of truth for current defaults and sort allowlists. The curated collection defaults are Titan `display_order`, Event `chronology_order`, and Location `location_order`; the global Image collection defaults to ID ascending. Image galleries retain `display_order` then image PK and do not declare a `sort`/`order` allowlist.

### Filtering

Multiple filters can be combined:

```http
?type=demigod&affiliation=camp_half_blood&status=alive
```

#### Choice Values — Strict Validation

Filters implemented with `StrictChoiceFilter` reject invalid values with a `400 Bad Request` and the allowed values in `valid_values`. Other invalid query inputs use the generic `BAD_REQUEST` envelope. See the live filter list in Section 23.

```http
GET /api/v1/characters/?type=Demigod HTTP/1.1
Accept: application/json

HTTP/1.1 400 Bad Request
Content-Type: application/json
{
  "error": {
    "code": "INVALID_FILTER_VALUE",
    "message": "type: 'Demigod' is not a valid choice.",
    "valid_values": ["demigod", "god", "titan", "monster", "mortal", "satyr", "centaur", "cyclops", "nymph", "hunter", "oracle", "legacy", "automaton", "spirit", "primordial"]
  }
}
```

This applies to choice filters that use `StrictChoiceFilter`; invalid boolean and ordering parameters use `BAD_REQUEST` instead. Only supported filters in Section 23 are part of the current contract. Values are not normalised: for example, `type=Demigod` is rejected while `type=demigod` is accepted.

#### Boolean Filters

Boolean query params accept lowercase `true` or `false` only:

```http
?is_demigod=true               ✅
?can_reform=false               ✅
?is_demigod=True               ❌  returns 400
?transforms=1                  ❌  returns 400
```

#### Lore metadata and soft-delete behavior — Implemented

`lore_accuracy`, `lore_notes`, and read-only `lore_sources` are included in lore entity list/detail payloads; `lore_accuracy` is filterable. `is_deleted` and `deleted_at` remain internal: deleted entities are hidden from public resource endpoints and search, with 404 on detail lookup. See Sections 16 and 17.

### Sparse Fieldsets — Not Implemented

The `fields=` query parameter is not supported. See Section 23 for current serializer fields.

### `include=` Relationship Expansion — Not Implemented

The `include=` query parameter is not supported. Implemented relationships are returned by resource-specific serializers and subresources described in Section 23.

---

## 9. Image Strategy

> **Implementation status:** image records, typed entity joins, image galleries, a global image collection, and a read-only wiki image audit/import workflow are implemented. Wiki seed records use `source_type='wiki'`; `license` and `license_url` remain null because the source did not expose machine-readable license metadata. See Section 23 for routes and serializer fields. The API returns external URLs, does not proxy or host image bytes, and does not assert reuse rights. Runtime fallback behavior and storage/CDN migration are not guaranteed by the current API.

### Decision: Standalone `Image` Model + Separate Join Tables Per Entity (Option B)

Images are their own first-class model. Rather than storing `image_url` strings directly on lore models, each supported gallery entity—Book, Character, God, Titan, Monster, Weapon, and Location—links to the `Image` model through a dedicated join table. Other entities do not have typed image galleries, but their image records may remain available in the global collection. This gives full PostgreSQL referential integrity, proper categorisation, multi-image support, and fan art attribution — all without any generic FK complexity.

---

### The `Image` Model

Every image stored in the system has the following fields:

| Field | Type | Description |
| --- | --- | --- |
| `id` | int | Primary key |
| `url` | URLField | Direct URL to the original image source; image files are not self-hosted |
| `thumbnail_url` | string | Lower-resolution version for list views (nullable) |
| `alt_text` | string | Accessible image description |
| `source_type` | enum | See Source Type enum below |
| `category` | enum | See Image Category enum below |
| `artist_name` | string | Credit for fan art or illustrated works (nullable) |
| `artist_url` | string | Link to artist's profile or portfolio (nullable) |
| `source_url` | string | Original page where the image was found (nullable) |
| `license` | string | e.g. "All Rights Reserved", "CC BY-NC" (nullable) |
| `license_url` | URLField | Canonical URL describing the image license (nullable) |
| `width` | int | Pixel width (nullable) |
| `height` | int | Pixel height (nullable) |
| `file_format` | string | jpg, png, webp (nullable) |
| `uploaded_at` | datetime | auto_now_add |
| `wiki_url` | string | Riordan Wiki image page reference (nullable) |

**Source Type enum:**
`official_book`, `official_publisher`, `disney_plus`, `official_game`, `fan_art`, `wiki`, `unknown`

**Image Category enum:**
`portrait`, `full_body`, `action`, `weapon_closeup`, `location`, `book_cover`, `concept_art`, `promotional`, `other`

---

### Join Tables Per Entity

Each supported entity type gets its own join table. This preserves full FK integrity in PostgreSQL and keeps queries simple. `is_primary` and `display_order` live on these join rows, not on `Image`; a database partial-unique constraint enforces at most one primary image per entity.

**Pattern (same structure repeated per entity):**

```text
CharacterImage   → character (FK) + image (FK) + is_primary + display_order
WeaponImage      → weapon (FK)    + image (FK) + is_primary + display_order
GodImage         → god (FK)       + image (FK) + is_primary + display_order
TitanImage       → titan (FK)     + image (FK) + is_primary + display_order
MonsterImage     → monster (FK)   + image (FK) + is_primary + display_order
LocationImage    → location (FK)  + image (FK) + is_primary + display_order
BookImage        → book (FK)      + image (FK) + is_primary + display_order
```

`display_order` controls the sequence images appear in the gallery. `is_primary` flags the single default image used in list views and cards.

---

### Illustrative Character Image Shape (Not the Current Serializer)

> The nested `images.primary` / `images.gallery` object below is a design illustration, not the current Character response. Current details expose `primary_image`; the gallery is a separate `/characters/<slug>/images/` subresource (see Section 23).

```json
{
  "id": 1,
  "name": "Percy Jackson",
  "slug": "percy-jackson",
  "images": {
    "primary": {
      "url": "https://cdn.yourapi.com/images/percy-jackson-primary.jpg",
      "thumbnail_url": "https://cdn.yourapi.com/images/percy-jackson-thumb.jpg",
      "alt_text": "Percy Jackson, son of Poseidon, holding Riptide",
      "source_type": "official_book",
      "category": "portrait",
      "artist_name": "John Rocco",
      "source_url": "https://rickriordan.com/..."
    },
    "gallery": [
      {
        "url": "https://cdn.yourapi.com/images/percy-disney-plus.jpg",
        "source_type": "disney_plus",
        "category": "promotional",
        "alt_text": "Walker Scobell as Percy Jackson in the Disney+ series"
      },
      {
        "url": "https://cdn.yourapi.com/images/percy-fanart-01.jpg",
        "source_type": "fan_art",
        "category": "full_body",
        "artist_name": "viria",
        "artist_url": "https://viria.tumblr.com",
        "alt_text": "Fan art of Percy Jackson in battle"
      }
    ]
  }
}
```

---

### Image Filtering via the API

Images are filterable as a sub-resource on the supported entities listed in Section 23. The API accepts the strict `source_type` and `category` choice filters.

```http
GET /api/v1/characters/<slug>/images/
GET /api/v1/characters/<slug>/images/?source_type=official_book
GET /api/v1/characters/<slug>/images/?source_type=fan_art
GET /api/v1/characters/<slug>/images/?source_type=disney_plus
GET /api/v1/characters/<slug>/images/?category=portrait
GET /api/v1/characters/<slug>/images/?category=full_body

GET /api/v1/weapons/<slug>/images/
GET /api/v1/weapons/<slug>/images/?source_type=official_book
GET /api/v1/weapons/<slug>/images/?category=weapon_closeup

GET /api/v1/gods/<slug>/images/
GET /api/v1/gods/<slug>/images/?source_type=fan_art

GET /api/v1/locations/<slug>/images/
GET /api/v1/locations/<slug>/images/?category=concept_art
```

Multiple filters can be combined:

```http
GET /api/v1/characters/annabeth-chase/images/?source_type=official_book&category=portrait
```

---

### Wiki Image Audit and Import

The report-only audit scans entity seed files and writes JSON; it does not modify the database. Strict allowlist mode is the default. To include every discovered URL for the v1 seed, pass `--include-all-images`; license fields will remain null and this does not assert reuse rights:

```bash
uv run python manage.py audit_wiki_images \
  --input data/books.json \
  --input data/cabins.json \
  --input data/characters.json \
  --input data/creatures.json \
  --input data/events.json \
  --input data/factions.json \
  --input data/gods.json \
  --input data/locations.json \
  --input data/monsters.json \
  --input data/powers.json \
  --input data/prophecies.json \
  --input data/quests.json \
  --input data/titans.json \
  --input data/weapons.json \
  --include-all-images \
  --request-delay 0.5 \
  --output data/images.json \
  --settings=config.settings.development
```

`--request-delay` defaults to 0.25 seconds. The current seed contains 2,787 per-page image references from 330 pages; `seed_images` upserts these into 2,651 unique Image rows by `(url, source_url)`. Fifteen pages have no image candidates. The audit follows MediaWiki page redirects when resolving page images, including unaccented aliases such as `Zoe_Nightshade`. Import after entity seeds with `uv run python manage.py seed_images --settings=config.settings.development` or use `seed_all`. Imported rows use `source_type='wiki'`; license fields remain null. Characters, Gods, Titans, Monsters, and Weapons receive a gallery link only when the decoded image URL filename contains the entity name or slug, except for entity-specific `include_file_titles` and `exclude_file_titles` overrides in `data/image_gallery_overrides.json`; excluded images remain in the global collection, and curated entries retain their original `source_url` provenance even when sourced from a related page. A per-entity `primary_file_title` override can set one included link as primary, clearing any other primary for that entity. Book galleries include explicit cover/CVR/Bookpic files or portrait image filenames matching the book title; those Image rows use `category='book_cover'`. Other imported images use `category='other'` and remain available in the global collection, and re-seeding removes stale wiki gallery links that no longer meet the matching rules. Location gallery matching remains page-based. Missing license metadata means reuse rights are unverified, not granted; confirm permissions separately before public reuse.

### Additional Notes

- The `is_primary` flag is stored on each entity-image join row; a conditional unique constraint enforces at most one primary image per entity.
- For a Book, `category='book_cover'` is stored on the Image row and identifies cover candidates; the `BookImage` join links only qualifying covers.
- Requiring `artist_name` for fan art is a future validation-policy decision; the current model allows it to be null.
- External URLs (e.g. Riordan Wiki) should be stored but the system should support migrating to internally hosted CDN URLs in future without breaking the API response shape
- A separate `map_marker_icon` field on `Location` is not currently implemented; consider it only if a client use case requires it.

---

## 10. Seed Data — Current Canonical JSON Counts

Counts below are record counts in the current root-level `data/*.json` files, not claims that every canon entity is represented. Seed commands warn and skip unresolved references rather than inventing missing records.

| Seed file / model | Current records |
| --- | ---: |
| `books.json` / Books | 12 |
| `characters.json` / Characters | 96 |
| `gods.json` / Gods | 41 |
| `titans.json` / Titans | 23 |
| `monsters.json` / Monsters | 29 |
| `creatures.json` / Creatures | 18 |
| `weapons.json` / Weapons | 50 |
| `locations.json` / Locations | 27 |
| `quests.json` / Quests | 12 |
| `prophecies.json` / Prophecies | 11 |
| `events.json` / Events | 23 |
| `cabins.json` / Cabins | 20 |
| `factions.json` / Factions | 8 |
| `family_relationships.json` / typed family edges | 383 |
| `book_character_relationships.json` / Book relationship records | 12 |
| `monster_defeats.json` / defeat events | 27 |
| `powers.json` / Powers | 14 |
| `images.json` / wiki Image references | 2,787 refs from 330 pages; 2,651 unique Image rows |

---

## 11. Edge Cases & Lore Nuances

These are lore/reference notes used when reviewing canonical seed records. They are not guarantees that the API has timeline-aware fields for every nuance; the implemented serializer/model fields are listed in Section 23.

1. **Luke Castellan's arc** — he is simultaneously a protagonist (early), antagonist (Books 1–5), and hero (sacrifice, Book 5). `affiliation` must be an array, and `status` must track his arc by book.

2. **Thalia Grace** — turned into a pine tree by Zeus at end of backstory, restored to human form in Book 2 by the Golden Fleece. Her `status` should have a timeline: `alive → transformed (tree) → alive → immortal (Hunter)`.

3. **Bianca and Nico di Angelo** — time-displaced children of Hades, born before WWII but aged normally into the 21st century due to being kept in the Lotus Hotel. This must be noted in their `lore_notes` field.

4. **Nico in Book 3** — appears to be a minor character; his importance grows dramatically. He must be fully modeled from first appearance.

5. **Tyson** — Percy's half-brother and a Cyclops. He is technically not a demigod but is a child of Poseidon. His `type` should be `cyclops` and `species` should be `cyclops`, but `divine_parent` should still link to Poseidon. Flag `is_demigod: false`.

6. **Chiron's dual identity** — Chiron uses the alias "Mr. Brunner" (Latin teacher at Yancy Academy) and later "Ronnie" as a cover. `aliases` field is critical.

7. **The Oracle** — prior to Rachel taking the role, the spirit of the Oracle was trapped in an unnamed mummy at Camp Half-Blood (cursed by Hades). Rachel Dare becomes the Oracle at the end of Book 5. The `Character` model must handle this transition.

8. **Dionysus / Mr. D** — a full Olympian god serving as camp director as a punishment. His `affiliation` includes both `olympian_council` and `camp_half_blood`.

9. **Pan's Fading** — the god Pan fades (dies) at the end of Book 4. This is the only god depicted fading in V1. His `status` should be `faded` and this should be explained in `description`.

10. **Iapetus → Bob** — Iapetus falls into the River Lethe and forgets he is a Titan. He becomes friendly and calls himself "Bob." His `status` should be `active` but with `notes` explaining the memory loss. Critical for V2 (he returns in House of Hades).

11. **Kronos's possession of Luke** — Kronos does not have a physical body; he possesses Luke. The `Titan` model for Kronos should include `host_character: Luke Castellan` and the `Character` model for Luke should flag `is_possessed: true` in the relevant book range.

12. **Hestia's cabin** — she has no cabin because she gave up her throne to Dionysus. She exists as a fire in the mess hall. She should be in the `God` model with `has_cabin: false` and this explained in `description`.

13. **Janus** — a Roman god who appears in the Labyrinth. He should be flagged `roman_only: true` and noted as an anomaly (Greek-world story featuring a purely Roman god).

14. **Achilles's Blessing / Mortal Point** — Percy's invulnerability (small of his back) is a temporary state specific to Books 5+. This should be a `special_states` array on the `Character` model with book-range validity.

15. **The Great Prophecy's ambiguity** — the prophecy was interpreted as referring to Percy for the entire series, but the final act was Luke's. This nuance must be captured in the `Prophecy` model's `interpretation_notes`.

---

## 12. V2 Expansion Considerations (Proposals)

These are future design ideas, not implemented models or current API fields. Any expansion should be reviewed against the existing typed relationship model and the future-work decisions at the end of this document.

### New Fields on Existing Models

- `Character` — add `roman_equivalent_character` (e.g. Percy → no Roman name, but Jason Grace is the Roman equivalent figure)
- `God` — add full `roman_aspect_personality` and `roman_domain_emphasis`
- `Weapon` — add `material: imperial_gold` to the enum

### New Models for V2

- **Camp Jupiter** — Roman demigod camp (San Francisco); Cohort system instead of cabins
- **Cohort** — Roman equivalent of Cabin; 5 cohorts at Camp Jupiter
- **Egyptian God** — entirely separate deity system for Kane Chronicles
- **Nome** — Egyptian equivalent of Camp Half-Blood (the 21st Nome, Brooklyn)
- **Spell / Scroll** — Egyptian magic system (different from Greek divine power)
- **Path of the Gods** — Egyptian magic users host gods within them
- **Crossover Events** — The Son of Sobek, Staff of Serapis, Crown of Ptolemy (Percy + Kane characters meeting)
- **Legacy** — a mortal descended from a demigod (Roman concept; e.g. Octavian is a legacy of Apollo)

### Mythology Field

Add `mythology` enum to most models: `greek`, `roman`, `egyptian`, `norse` (V3)

---

## 13. General API Design Principles

### Implemented Conventions

- All versioned resources are mounted under `/api/v1/` and use trailing slashes; health and key-management routes are outside that prefix.
- API responses use JSON and `snake_case`, including for normal browser requests; the DRF browsable API renderer is disabled. Requests accepting only `text/html` receive `406 Not Acceptable`; `?format=api` is unsupported. Swagger UI and ReDoc remain HTML, and `/api/schema/` retains its YAML/JSON schema formats. Detail URLs use slugs; the Cabin number lookup is `/api/v1/cabins/number/<number>/`.
- List views that use DRF pagination return `{ "data": [...], "meta": { "total", "page", "limit", "total_pages" } }`; the default page size is 20 and the maximum `limit` is 100. Search has its own `data`/`meta` envelope; detail responses are resource-specific objects.
- Missing optional scalar values may be `null`; empty relationships are returned as empty arrays. Response fields vary by list/detail serializer; see Section 23.
- Query choice errors use the standard API error envelope. Invalid choices use `INVALID_FILTER_VALUE` and include `valid_values`; other handled bad requests use `BAD_REQUEST`.
- Boolean query filters accept exactly lowercase `true` or `false`. List ordering accepts `?sort=<allowlisted-field>[&order=asc|desc]`; `order` defaults to ascending when a sort field is supplied alone, while `order` without `sort` is invalid. The default direction is ascending, and legacy `?ordering=` remains supported.

### Health and access

- Public health routes: `GET /health/live/` and `GET /health/ready/`. Readiness checks PostgreSQL.
- Public key routes: `POST /auth/request-key/` and `POST /auth/verify-key/`.
- Public discovery route: `GET /api/v1/` returns a flat JSON object linking the collections and search, without pagination, database/cache access, or API-key throttling.
- Other API routes require the `X-API-Key` header by default. Lore resources are read-only; the directory, key request/verification, health, and documentation routes are exceptions.
- API-key rate limits and headers are documented in Section 14. Redis is optional at request time; local fallbacks preserve API availability, but local throttle counters are not shared between workers during a Redis outage.

### Not implemented

The following remain proposals, not current API contracts: sparse fieldsets, `include=` relationship expansion, a guaranteed image fallback, and any undeclared ordering field. Lore accuracy/source provenance and soft deletion are implemented as described in Sections 16 and 17. See the final Future Work section.

---

## 14. Authentication & Security

### API key routes and header

Versioned lore endpoints require `X-API-Key`; the `GET /api/v1/` directory is public. Public endpoints outside `/api/v1/` include `GET /api/schema/`, `GET /api/docs/`, `GET /api/redoc/`, `GET /health/live/`, `GET /health/ready/`, `POST /auth/request-key/`, and `POST /auth/verify-key/`.

Request a key with `consumer_name` and `email`:

```http
POST /auth/request-key/
Content-Type: application/json

{"consumer_name":"My Fan App","email":"dev@example.com"}
```

The successful response is `201 Created` and contains `api_key`, `consumer_name`, `email`, and `message`. The plaintext key is shown once. To verify it, send `POST /auth/verify-key/` with the `X-API-Key` header; the response contains `valid` and `consumer_name`. Neither endpoint accepts `intended_use` or `website_url` in its request body.

To revoke the key used for the current request, send `POST /auth/revoke-key/` with `X-API-Key` and no request body. It returns `200 OK` with `revoked: true`; repeated requests are idempotent. A caller cannot select another key to revoke.

The key model is `ConsumerAPIKey`, managed through Django Admin. The API key package stores a hashed key; logs contain neither the plaintext key nor its hash. Revocation is available to administrators and to the holder of the presented key via `POST /auth/revoke-key/`; unverified email cannot authorize revocation. Successful key-validation results are cached for five minutes under the public prefix; the cache value is a settings-salted fingerprint of the full key, not a boolean, and a different secret with that prefix is rejected. Both admin and self-revocation delete the cached prefix after the database transaction commits. If cache invalidation fails because Redis is unavailable, the failure is logged; permission checks fall back to PostgreSQL while Redis is down, and a stale positive can remain until TTL expiry if Redis recovers before the entry expires. A repeated request to the self-revocation route retries cache invalidation.

### Throttling and response headers

- Valid API-key prefixes receive a shared fixed-window limit of **1,000 requests per hour per key**.
- Requests without an API key use the lower **100 requests/day per client IP** fallback.
- Request-key and verify-key routes use **5 requests/hour per client IP**.
- Rate-limited API requests expose `RateLimit-Limit` (including the window), `RateLimit-Remaining`, and `RateLimit-Reset`. A throttled response includes `Retry-After`.
- Redis provides shared counters when available. During a Redis outage, in-process counters are used and are not shared between workers.
- `X-Request-ID` is returned for request correlation. Structured logs omit request bodies, query strings, email addresses, API key plaintext, and key hashes.

Example response headers:

```http
RateLimit-Limit: 1000;w=3600
RateLimit-Remaining: 847
RateLimit-Reset: 1723
X-Request-ID: 9b0e9d3c...
```

### Current permissions

The default DRF permission is cached API-key validation (`CachedHasAPIKey`). API-directory, health, key-request, and key-verification views explicitly allow unauthenticated access; `POST /auth/revoke-key/` requires the presented key and revokes only that key. There is no end-user login/account workflow or email-authorized key revocation.

---

## 15. Search

### Implementation — `django-watson`

Search uses `django-watson` with custom adapters per model. Watson builds a full-text search index in PostgreSQL and queries it across all registered models simultaneously.

#### Custom Adapters

Each model has a `SearchAdapter` that defines exactly what text gets indexed. Crucially, this flattens array fields like `aliases`, `abilities`, and `true_name` so they are fully searchable:

```python
class MonsterSearchAdapter(watson.SearchAdapter):
    def get_search_text(self, obj, language, connection):
        parts = [obj.name, obj.description or '', obj.physical_description or '']
        if obj.aliases:
            parts.extend(obj.aliases)          # "Aunty Em" → finds Medusa
        if obj.disguise_form:
            parts.append(obj.disguise_form)
        return ' '.join(parts)

class WeaponSearchAdapter(watson.SearchAdapter):
    def get_search_text(self, obj, language, connection):
        parts = [obj.name, obj.true_name or '', obj.description or '']
        if obj.abilities:
            parts.extend(obj.abilities)
        return ' '.join(parts)                 # "Anaklusmos" → finds Riptide

class CharacterSearchAdapter(watson.SearchAdapter):
    def get_search_text(self, obj, language, connection):
        parts = [obj.name, obj.description or '', obj.fatal_flaw or '']
        if obj.aliases:
            parts.extend(obj.aliases)          # "Wise Girl" → finds Annabeth
        return ' '.join(parts)
```

#### Alias Search Examples

| Query | Returns | Via |
| --- | --- | --- |
| `"Aunty Em"` | Medusa | `aliases` flattened into index |
| `"Anaklusmos"` | Riptide | `true_name` indexed |
| `"Wise Girl"` | Annabeth Chase | `aliases` flattened into index |
| `"Mr Brunner"` | Chiron | `aliases` flattened into index |
| `"Lord of the Wild"` | Grover Underwood | `description` match |
| `"son of poseidon"` | Percy Jackson | `description` match |

#### Index Management

```bash
# Build index after initial seed
python manage.py buildwatson

# Watson auto-updates on save() via signals — no manual rebuild needed for ongoing changes
```

#### Search Endpoint

```http
GET /api/v1/search/?q=riptide
GET /api/v1/search/?q=poseidon&type=god
```

Search requires a nonblank `q`; `type` optionally limits the query to a supported entity type. The current response is:

```json
{
  "data": [
    {
      "type": "weapon",
      "slug": "riptide",
      "url": "/api/v1/weapons/riptide/",
      "title": "Riptide",
      "description": "Percy Jackson's Celestial Bronze sword...",
      "wiki_url": null
    }
  ],
  "meta": {"total": 1, "query": "riptide", "type_filter": null}
}
```

Search uses `django-watson` adapters across registered entity models. Typo matching is not promised. The current response fields are `type`, `slug`, `url`, `title`, `description`, and `wiki_url`.

---

## 16. Lore Accuracy and Source Provenance

Every lore entity inherits `lore_accuracy` (default `unreviewed`), `lore_notes`, and a many-to-many `lore_sources` relation from `BaseModel`. These fields appear in list/detail responses, and list endpoints accept the `lore_accuracy` filter. `lore_sources` is read-only through the public API; sources are managed through Django Admin or seed data.

`LoreSource` records a title, source type, optional URL, precise citation, and notes. Supported source types are `primary_text`, `author_statement`, `official_reference`, `secondary_reference` (the default), and `other`. Source records may be associated with multiple entities.

### Historical Accuracy-Flagging Proposal (Not the Current Schema)

All 13 data models inherit from this mixin. It adds three fields to every model with zero duplication:

```python
class LoreTrackedModel(models.Model):

    class LoreAccuracy(models.TextChoices):
        CONFIRMED          = 'confirmed',          'Confirmed Canon'
        APPROXIMATE        = 'approximate',        'Approximate / Paraphrased'
        DISPUTED           = 'disputed',           'Disputed Between Sources'
        FAN_INTERPRETATION = 'fan_interpretation', 'Fan Interpretation'

    lore_accuracy = models.CharField(
        max_length=20,
        choices=LoreAccuracy.choices,
        default=LoreAccuracy.CONFIRMED
    )
    lore_notes = models.TextField(blank=True, null=True)
    lore_source = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        abstract = True
```

#### What Each Value Means

| Value | Meaning | Example |
| --- | --- | --- |
| `unreviewed` | Seeded information has not yet been assessed for source confidence | Default for newly seeded entities |
| `confirmed` | Directly stated in the books or by Riordan | Percy's fatal flaw stated explicitly in Book 3 |
| `approximate` | General fact correct but detail inferred or from secondary source | Medusa's reform time — implied but never stated |
| `disputed` | Different sources contradict each other | Nico's exact age due to Lotus Hotel timeline |
| `fan_interpretation` | Community consensus or logical inference; no direct textual evidence | Powers inferred from parentage, never shown on screen |

#### In API Responses

```json
{
  "name": "Zoë Nightshade",
  "status": "deceased",
  "lore_accuracy": "approximate",
  "lore_notes": "Fatal flaw strongly implied by her arc but never named explicitly in the text.",
  "lore_sources": [
    {
      "title": "The Titan's Curse",
      "source_type": "primary_text",
      "url": "",
      "citation": "Chapter 13",
      "notes": ""
    }
  ]
}
```

#### Filterable at API Level

```http
GET /api/v1/characters/?lore_accuracy=disputed
GET /api/v1/monsters/?lore_accuracy=fan_interpretation
GET /api/v1/weapons/?lore_accuracy=confirmed
```

---

## 17. Soft Delete

All lore entities have internal `is_deleted` and `deleted_at` fields. The default `objects` manager returns active rows only; `all_objects` is available to Django Admin, seed upserts, and internal foreign-key handling. Calling an instance’s `delete()` or a queryset’s `delete()` soft-deletes records and preserves model save signals; use the explicit `hard_delete()` method only for an intentional permanent purge.

Deleted entities are hidden from public list/detail endpoints and search; requesting a deleted entity by slug returns 404. Soft deletion does not cascade to other entities. Serializers omit or null references to deleted entities. Django Admin includes deleted records and provides soft-delete and restore actions; hard-delete is not available through Admin. There is no public delete, restore, or deleted-record endpoint.

### Internal Model Operations

These methods are for application and administration code; they are not public API endpoints.

```python
entity.delete()       # soft-delete
entity.restore()      # restore via all_objects
entity.hard_delete()  # explicit permanent purge
```

### Behaviour

- Deleted records are excluded from all list and detail endpoints by default via a custom manager
- `GET /api/v1/characters/gabe-ugliano/` returns `404` after the entity is soft-deleted
- No public endpoint exposes deleted records
- Deletion and restoration are managed exclusively via Django Admin

#### Manager and lifecycle behavior

`objects` is the active-only default manager. `all_objects` includes deleted rows and is used by Admin and canonical seed updates. Both managers expose `SoftDeleteQuerySet`, which implements `delete()`, `soft_delete()`, `restore()`, and explicit `hard_delete()` operations. Instance deletion and restoration update `updated_at` and preserve Django `save()` signals.

---

## 18. Ordering Within Related Sets — Partially Implemented

> Titan, Event, and Location lists have explicit curated order fields and expose them in list/detail payloads. Their defaults and `sort`/`order` allowlists are in Section 23. Other historical proposals in this section remain unimplemented.

### Decision (Historical Proposal)

Two approaches are used depending on whether the ordering is contextual or natural:

**Through models with `display_order`** — for relationships where order is meaningful and specific to the relationship itself (e.g. the order locations are visited on a quest, the order a character acquires weapons).

**Queryset ordering** — for relationships where the related model's natural sort is always correct (e.g. `books_appeared_in` always sorted by `book_number`).

### Historical Ordering Proposal — Not the Current Contract

| Relationship | Approach | Order |
| --- | --- | --- |
| `character.books_appeared_in` | Queryset | `book_number` asc |
| `character.weapons` | Through model | `display_order` asc (acquisition order) |
| `character.images` | Through model | `is_primary` desc, then `display_order` asc |
| `quest.locations_visited` | Through model | `display_order` asc (journey order) |
| `quest.monsters_encountered` | Through model | `display_order` asc (encounter order) |
| `quest.participants` | Queryset | `led_by` first, then `name` asc |
| `god.children_demigods` | Queryset | `name` asc |
| `monster.books_appeared_in` | Queryset | `book_number` asc |
| `cabin.known_campers` | Queryset | head counselor first, then `name` asc |
| `faction.members` | Queryset | leader first, then `name` asc |
| `weapon.owner_history` | Through model | `display_order` asc (chronological) |

### Through Model Pattern

```python
class QuestLocation(models.Model):
    quest = models.ForeignKey('Quest', on_delete=models.CASCADE)
    location = models.ForeignKey('Location', on_delete=models.CASCADE)
    display_order = models.PositiveIntegerField(default=0)
    visit_notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['display_order']
        unique_together = ['quest', 'location']
```

---

## 19. Environment Configuration

> Current repository requires Python 3.14+ (`pyproject.toml`), uses `uv` (`uv.lock`), PostgreSQL for development/production, SQLite for tests, and Redis as an optional cache/throttle backend with outage fallbacks. See `.env.example` and `config/settings/` for authoritative settings.

### Settings Structure — Split Files Per Environment

```text
config/settings/
  base.py          # shared apps, REST_FRAMEWORK, auth, filters, pagination, cache/logging
  development.py   # PostgreSQL; local development hosts
  production.py    # PostgreSQL; ALLOWED_HOSTS supplied by environment
  test.py              # SQLite and test-only settings
  test_postgresql.py   # PostgreSQL test settings used by CI
```

There is no staging settings module. Development and production use PostgreSQL; the default automated test settings use SQLite, while CI also runs the suite with PostgreSQL. Redis is optional: key validation falls back to PostgreSQL, and throttle counters fall back to process-local memory.

### Required Entry in `base.py` — Primary Key Type

```python
# config/settings/base.py

# All model primary keys are bigint across the entire project.
# PostgreSQL equivalent: bigint NOT NULL PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY
# Applies to all 13 lore models, all join/through tables, and Django's own internal models.
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
```

This single line means no model — including `BaseModel` inheritors, image join tables, through models, or Django internals — ever silently defaults to a 32-bit integer primary key.

Use the settings modules explicitly when running management commands:

```bash
uv run python manage.py check --settings=config.settings.development
uv run python manage.py test --settings=config.settings.test
```

### Variable Management

- **Local development** — `.env` file loaded by `django-environ` and ignored by Git.
- **Production** — platform-provided environment variables; no secret files are committed.
- **Tests** — `config.settings.test` uses SQLite; `config.settings.test_postgresql` runs the full suite against PostgreSQL in CI. Development and production settings also use PostgreSQL.

### `.env.example` (committed template; no real secrets)

```bash
SECRET_KEY=
APP_VERSION=0.1.0
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DB_NAME=
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=5432
REDIS_URL=redis://127.0.0.1:6379/1
CORS_ALLOWED_ORIGINS=
API_KEY_CUSTOM_HEADER=HTTP_X_API_KEY
```

The committed `.env.example` and all five settings modules (`base.py`, `development.py`, `production.py`, `test.py`, `test_postgresql.py`) are authoritative. The earlier `REQUIRED_ENV_VARS` startup-guard snippet is not implemented.

---

## 20. BaseModel — Implemented Shared Fields and Earlier Proposal

> The abstract `BaseModel` in `apps/core/models.py` supplies timestamps, nullable `wiki_url`, lore accuracy/provenance, and soft-delete fields. Slugs and entity-specific fields live on concrete models. The historical sketch below is not the authoritative schema; use this section’s implemented inventory and Sections 16–17 for current behavior.

Lore entity models inherit from `BaseModel`. The `id` primary key is supplied by `DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'`; each concrete model declares its own slug.

### Implemented Shared Field Inventory

| Field | Type | Notes |
| --- | --- | --- |
| `id` | `BigAutoField` | Supplied by `DEFAULT_AUTO_FIELD` in settings |
| `created_at` | `DateTimeField` | Set on creation (`auto_now_add=True`) |
| `updated_at` | `DateTimeField` | Updated on save (`auto_now=True`) |
| `wiki_url` | nullable `URLField` | Optional source link shared by lore entity models |
| `lore_accuracy` | indexed `CharField` | Defaults to `unreviewed`; choices are documented in Section 16 |
| `lore_notes` | `TextField` | Optional explanation of uncertainty or interpretation |
| `lore_sources` | blankable many-to-many | Read-only source citations in entity API responses |
| `is_deleted` | indexed `BooleanField` | Internal lifecycle state; active manager filters it out |
| `deleted_at` | nullable `DateTimeField` | Internal deletion timestamp; null for active entities |
| `slug` | model-specific slug field | Declared by concrete models; slug source varies |

The old sketch below includes fields that are not part of the current schema: `last_reviewed_at`, singular `lore_source`, `description`, `notes`, `is_featured`, `search_priority`, and `mythology`. The current fields `lore_accuracy`, `lore_notes`, `lore_sources`, `is_deleted`, and `deleted_at` are implemented.

### Slug Source Per Model

Since `populate_from` must point to a field that exists on the concrete model, slug is declared individually:

| Model | Slug `populate_from` |
| --- | --- |
| `Character` | `'name'` |
| `God` | `'name'` |
| `Titan` | `'name'` |
| `Monster` | `'name'` |
| `Creature` | `'name'` |
| `Weapon` | `'name'` |
| `Location` | `'name'` |
| `Faction` | `'name'` |
| `Event` | `'name'` |
| `Book` | `'title'` |
| `Quest` | `'title'` |
| `Prophecy` | `'title'` |
| `Cabin` | custom callable → `"cabin-{number}-{deity.name}"` e.g. `cabin-3-poseidon` |

### Historical BaseModel Code Sketch (Not Implemented)

```python
# core/models.py

from django.db import models
from django.utils import timezone


class ActiveManager(models.Manager):
    """
    Default manager for all lore models.
    Excludes soft-deleted records from all queries automatically.
    """
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class BaseModel(models.Model):
    """
    Abstract base model inherited by all 13 lore models.

    ID:   Set globally via DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
          in config/settings/base.py. Django creates it automatically on every
          model. PostgreSQL equivalent:
          bigint NOT NULL PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY

    Slug: Declared on each individual model via AutoSlugField(populate_from=<field>)
          because the source field differs per model (name, title, or a custom
          callable for Cabin).
    """

    # ----------------------------------------------------------------
    # Timestamps
    # ----------------------------------------------------------------
    created_at = models.DateTimeField(
        auto_now_add=True
        # null=True and blank=True are unnecessary — auto_now_add
        # always supplies a value and implies editable=False automatically
    )
    updated_at = models.DateTimeField(
        auto_now=True
        # auto_now always supplies a value on every save and implies
        # editable=False automatically — null=True is not needed
    )
    last_reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this entry was last verified against source material."
    )

    # ----------------------------------------------------------------
    # Soft Delete
    # ----------------------------------------------------------------
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def delete(self, *args, **kwargs):
        """Override delete() to soft-delete instead of hard-delete."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def hard_delete(self, *args, **kwargs):
        """Permanent deletion. Admin use only — bypasses soft delete."""
        super().delete(*args, **kwargs)

    def restore(self):
        """Restore a soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at'])

    # ----------------------------------------------------------------
    # Lore Accuracy
    # ----------------------------------------------------------------
    class LoreAccuracy(models.TextChoices):
        CONFIRMED          = 'confirmed',          'Confirmed Canon'
        APPROXIMATE        = 'approximate',        'Approximate / Paraphrased'
        DISPUTED           = 'disputed',           'Disputed Between Sources'
        FAN_INTERPRETATION = 'fan_interpretation', 'Fan Interpretation'

    lore_accuracy = models.CharField(
        max_length=20,
        choices=LoreAccuracy.choices,
        default=LoreAccuracy.CONFIRMED
    )
    lore_notes = models.TextField(
        blank=True,
        null=True,
        help_text="Public-facing note explaining why this entry is flagged."
    )
    lore_source = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Where this data came from. e.g. 'The Titan's Curse, Ch.11' or 'Riordan Wiki'."
    )

    # ----------------------------------------------------------------
    # Content
    # ----------------------------------------------------------------
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Full lore description. Public-facing."
    )
    wiki_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Link to the Riordan Wiki article for this entry."
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Internal admin notes. NOT exposed in API responses."
    )

    # ----------------------------------------------------------------
    # Display & Search
    # ----------------------------------------------------------------
    is_featured = models.BooleanField(
        default=False,
        help_text="Frontend highlight flag. Exposed in API responses."
    )
    search_priority = models.PositiveIntegerField(
        default=0,
        help_text="Manual search ranking weight. Higher = appears earlier in results."
    )

    # ----------------------------------------------------------------
    # Mythology (V2-ready — defaults to greek for all V1 entries)
    # ----------------------------------------------------------------
    class Mythology(models.TextChoices):
        GREEK    = 'greek',    'Greek'
        ROMAN    = 'roman',    'Roman'
        EGYPTIAN = 'egyptian', 'Egyptian'
        NORSE    = 'norse',    'Norse'

    mythology = models.CharField(
        max_length=10,
        choices=Mythology.choices,
        default=Mythology.GREEK
    )

    # ----------------------------------------------------------------
    # Managers
    # ----------------------------------------------------------------
    objects     = ActiveManager()      # default — excludes soft-deleted records
    all_objects = models.Manager()     # admin use only — includes soft-deleted records

    class Meta:
        abstract = True  # no database table is created for BaseModel itself
```

### How a Concrete Model Uses It

```python
# characters/models.py

from django.db import models
from autoslug import AutoSlugField
from core.models import BaseModel


class Character(BaseModel):
    """
    Fields inherited from BaseModel (15 fields, defined once):
      id, created_at, updated_at, last_reviewed_at,
      is_deleted, deleted_at,
      lore_accuracy, lore_notes, lore_source,
      description, wiki_url, notes,
      is_featured, search_priority, mythology

    Declared here (slug + character-specific fields):
    """

    slug = AutoSlugField(
        populate_from='name',
        unique=True,
        always_update=False,  # slug is permanent after creation
        editable=False
    )

    # Character identity
    name = models.CharField(max_length=255)

    # Character-specific enums and fields
    class CharacterType(models.TextChoices):
        DEMIGOD  = 'demigod',  'Demigod'
        MORTAL   = 'mortal',   'Mortal'
        SATYR    = 'satyr',    'Satyr'
        CENTAUR  = 'centaur',  'Centaur'
        CYCLOPS  = 'cyclops',  'Cyclops'
        NYMPH    = 'nymph',    'Nymph'
        HUNTER   = 'hunter',   'Hunter'
        ORACLE   = 'oracle',   'Oracle'
        AUTOMATON = 'automaton', 'Automaton'
        SPIRIT   = 'spirit',   'Spirit'

    class Status(models.TextChoices):
        ALIVE       = 'alive',       'Alive'
        DECEASED    = 'deceased',    'Deceased'
        IMMORTAL    = 'immortal',    'Immortal'
        TRANSFORMED = 'transformed', 'Transformed'
        IMPRISONED  = 'imprisoned',  'Imprisoned'
        FADED       = 'faded',       'Faded'
        UNKNOWN     = 'unknown',     'Unknown'

    type   = models.CharField(max_length=20, choices=CharacterType.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ALIVE)

    # ... remaining character-specific fields

    class Meta:
        ordering = ['name']


# books/models.py

class Book(BaseModel):
    slug = AutoSlugField(
        populate_from='title',  # source is 'title' not 'name'
        unique=True,
        always_update=False,
        editable=False
    )

    title = models.CharField(max_length=255)

    # ... remaining book-specific fields

    class Meta:
        ordering = ['book_number']


# cabins/models.py

def cabin_slug_source(instance):
    """Custom callable for Cabin slug — number + deity name."""
    deity_name = instance.deity.name.lower() if instance.deity else 'unknown'
    return f"cabin-{instance.number}-{deity_name}"
    # produces: "cabin-3-poseidon", "cabin-13-hades", "cabin-8-artemis"


class Cabin(BaseModel):
    slug = AutoSlugField(
        populate_from=cabin_slug_source,
        unique=True,
        always_update=False,
        editable=False
    )

    number = models.PositiveIntegerField(unique=True)

    # ... remaining cabin-specific fields

    class Meta:
        ordering = ['number']
```

### Historical Reuse-Rationale Table (Not a Current Field Inventory)

This table preserves the original proposal’s reuse rationale; entries such as `description`, `notes`, `mythology`, and `is_featured` were never implemented as BaseModel fields. The actual shared fields are listed above.

| Field | Without BaseModel | With BaseModel |
| --- | --- | --- |
| `created_at` | 13× | 1× |
| `updated_at` | 13× | 1× |
| `last_reviewed_at` | 13× | 1× |
| `is_deleted` | 13× | 1× |
| `deleted_at` | 13× | 1× |
| `delete()` method | 13× | 1× |
| `hard_delete()` method | 13× | 1× |
| `restore()` method | 13× | 1× |
| `lore_accuracy` | 13× | 1× |
| `lore_notes` | 13× | 1× |
| `lore_source` | 13× | 1× |
| `description` | 13× | 1× |
| `wiki_url` | 13× | 1× |
| `notes` | 13× | 1× |
| `is_featured` | 13× | 1× |
| `search_priority` | 13× | 1× |
| `mythology` | 13× | 1× |
| `ActiveManager` | 13× | 1× |
| **Total** | **234 definitions** | **18 definitions** |

---

## 21. Power Sub-Model

### Why Not JSON

The `Character` model originally stored powers as a raw JSON array. This works for display but makes filtering and querying impossible:

```http
GET /characters/?has_power=hydrokinesis                         ❌ not queryable on Character lists
GET /api/v1/characters/percy-jackson/powers/?source=divine_parent ✅ character-scoped Power collection
```

A dedicated `Power` model with a FK back to `Character` fixes all of this.

### Design Decision

`Power` does **not** inherit from `BaseModel` and has no slug or standalone route. It is exposed both as an embedded Character detail resource and through the character-scoped `/characters/<slug>/powers/` list endpoint, with its own `wiki_url` and the fields listed in Section 23. There is no standalone `/powers/` collection or detail route.

### The `Power` Model

```python
# powers/models.py

from django.db import models


class Power(models.Model):
    """
    Represents a single ability belonging to a Character.
    Each Character can have multiple Powers (one-to-many via FK).

    Does NOT inherit BaseModel — Powers are not standalone lore
    entities. They exist only in relation to a Character.
    """

    # ----------------------------------------------------------------
    # Relationship
    # ----------------------------------------------------------------
    character = models.ForeignKey(
        'characters.Character',
        on_delete=models.CASCADE,
        related_name='powers',
        help_text="The character this power belongs to."
    )

    # ----------------------------------------------------------------
    # Identity
    # ----------------------------------------------------------------
    name = models.CharField(
        max_length=255,
        help_text="e.g. 'Hydrokinesis', 'Swordsmanship', 'Shadow Travel'"
    )

    # ----------------------------------------------------------------
    # Classification
    # ----------------------------------------------------------------
    class PowerSource(models.TextChoices):
        DIVINE_PARENT = 'divine_parent', 'Divine Parent'
        TRAINED       = 'trained',       'Trained / Learned'
        BLESSING      = 'blessing',      'External Blessing'
        UNIQUE        = 'unique',        'Unique / Unknown Origin'
        ITEM_GRANTED  = 'item_granted',  'Granted by Item'
        OATH          = 'oath',          'Granted by Oath or Pact'

    class PowerType(models.TextChoices):
        OFFENSIVE      = 'offensive',      'Offensive'
        DEFENSIVE      = 'defensive',      'Defensive'
        UTILITY        = 'utility',        'Utility'
        PERCEPTION     = 'perception',     'Perception / Senses'
        COMMUNICATION  = 'communication',  'Communication'
        HEALING        = 'healing',        'Healing'
        SUMMONING      = 'summoning',      'Summoning'
        TRANSFORMATION = 'transformation', 'Transformation'
        PASSIVE        = 'passive',        'Passive / Always Active'

    source = models.CharField(
        max_length=20,
        choices=PowerSource.choices,
        default=PowerSource.DIVINE_PARENT
    )
    type = models.CharField(
        max_length=20,
        choices=PowerType.choices,
        default=PowerType.UTILITY
    )

    # ----------------------------------------------------------------
    # Detail
    # ----------------------------------------------------------------
    description = models.TextField(
        help_text="What the power does and how it manifests."
    )
    limitations = models.TextField(
        blank=True,
        null=True,
        help_text="Known weaknesses, conditions, or constraints on this power."
    )
    scope = models.JSONField(
        default=list,
        blank=True,
        help_text="Domain tags. e.g. ['water', 'ocean', 'sea'] or ['undead', 'shadow']"
    )

    # ----------------------------------------------------------------
    # Lore flags
    # ----------------------------------------------------------------
    is_passive = models.BooleanField(
        default=False,
        help_text="True if the power operates automatically without conscious activation."
    )
    is_book_specific = models.BooleanField(
        default=False,
        help_text="True if this power only manifests in specific books."
    )
    first_demonstrated_book = models.ForeignKey(
        'books.Book',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='powers_first_demonstrated',
        help_text="The book in which this power is first shown or used."
    )

    # ----------------------------------------------------------------
    # Ordering
    # ----------------------------------------------------------------
    display_order = models.PositiveIntegerField(
        default=0,
        help_text="Controls the order powers appear in API responses."
    )

    class Meta:
        ordering = ['display_order', 'name']

    def __str__(self):
        return f"{self.character.name} — {self.name}"
```

### Seed Data Examples

#### Percy Jackson

| name | source | type | is_passive | limitations |
| --- | --- | --- | --- | --- |
| Hydrokinesis | `divine_parent` | `offensive` | False | Weakened far from water; strongest at sea |
| Water Immunity | `divine_parent` | `passive` | True | Specific to Percy — not all Poseidon children |
| Earthquake Generation | `divine_parent` | `offensive` | False | Drains significant energy; risks structural collapse |
| Horse Communication | `divine_parent` | `communication` | False | Poseidon created horses; Percy can speak with them |
| Underwater Breathing | `divine_parent` | `passive` | True | Always active |
| Healing in Water | `divine_parent` | `healing` | False | Must be submerged; rate increases near the sea |
| Achilles's Blessing | `blessing` | `defensive` | True | One mortal point — small of the back |
| Swordsmanship | `trained` | `offensive` | False | Skill-based — no magical limitations |
| Empathy Link (Grover) | `unique` | `communication` | True | Only with Grover; extremely rare satyr bond |

#### Annabeth Chase

| name | source | type | is_passive |
| --- | --- | --- | --- |
| Strategic Intelligence | `divine_parent` | `utility` | True |
| Architecture Intuition | `divine_parent` | `perception` | True |
| Invisibility (Yankees Cap) | `item_granted` | `utility` | False |
| Combat Training | `trained` | `offensive` | False |
| Ancient Greek Literacy | `divine_parent` | `perception` | True |

#### Nico di Angelo

| name | source | type | is_passive |
| --- | --- | --- | --- |
| Shadow Travel | `divine_parent` | `utility` | False |
| Necromancy / Ghost Summoning | `divine_parent` | `summoning` | False |
| Umbrakinesis | `divine_parent` | `offensive` | False |
| Death Sense | `divine_parent` | `perception` | True |
| Undead Army Summoning | `divine_parent` | `summoning` | False |
| Stygian Iron Affinity | `divine_parent` | `passive` | True |

### API Response Shape

```json
{
  "id": 1,
  "name": "Percy Jackson",
  "slug": "percy-jackson",
  "powers": [
    {
      "name": "Hydrokinesis",
      "source": "divine_parent",
      "type": "offensive",
      "description": "The ability to mentally control and manipulate water in all its forms.",
      "limitations": "Significantly weakened when far from any body of water. Most powerful at sea.",
      "scope": ["water", "sea", "ocean", "ice", "steam"],
      "is_passive": false,
      "first_demonstrated_book": "the-lightning-thief"
    },
    {
      "name": "Achilles's Blessing",
      "source": "blessing",
      "type": "defensive",
      "description": "Near-total invulnerability granted by bathing in the River Styx.",
      "limitations": "One mortal point at the small of the back — a fatal vulnerability.",
      "scope": [],
      "is_passive": true,
      "first_demonstrated_book": "the-last-olympian"
    },
    {
      "name": "Swordsmanship",
      "source": "trained",
      "type": "offensive",
      "description": "Expert-level swordsmanship trained under Chiron at Camp Half-Blood.",
      "limitations": null,
      "scope": [],
      "is_passive": false,
      "first_demonstrated_book": "the-lightning-thief"
    }
  ]
}
```

### Endpoints Unlocked

```http
GET  /api/v1/characters/percy-jackson/powers/
GET  /api/v1/characters/percy-jackson/powers/?source=divine_parent
GET  /api/v1/characters/percy-jackson/powers/?type=offensive
GET  /api/v1/characters/percy-jackson/powers/?is_passive=true
```

### Summary

| Approach | Queryable | Filterable | Metadata | Verdict |
| --- | --- | --- | --- | --- |
| Raw JSON array on Character | ❌ | ❌ | Limited | ❌ Rejected |
| Dedicated `Power` model with FK | ✅ | ✅ | Full | ✅ Chosen |

---

## 22. Typed Family Relationships

### Why Greek Mythology Isn't a Tree

The God and Titan family structures are not trees — they are directed graphs with cycles. A single `GodRelationship` model and a separate `TitanRelationship` model would immediately break on the most important relationships in the entire series:

- **Kronos (Titan) → parent → Zeus (God)** — the central relationship of PJO
- **Rhea (Titan) → parent → Poseidon, Hades, Hera, Demeter, Hestia (Gods)**
- **Atlas (Titan) → parent → Zoë Nightshade (Character)**
- **Zeus (God) → sibling → Poseidon (God) AND Zeus → sibling → Hera (God) → consort → Zeus**

The God/Titan boundary does not exist in the actual mythology. The implemented `DivineRelationship` graph now supports God, Titan, Character, Monster, and Creature endpoints with full PostgreSQL referential integrity.

### Design Decision — Nullable FKs over GenericForeignKey

Two approaches were considered:

| | GenericForeignKey | Nullable FKs (chosen) |
| --- | --- | --- |
| God↔God | ✅ | ✅ |
| Titan↔Titan | ✅ | ✅ |
| Titan↔God | ✅ | ✅ |
| Titan↔Character | ✅ | ✅ |
| PostgreSQL FK integrity | ❌ | ✅ |
| DB-level constraint enforcement | ❌ | ✅ via `CheckConstraint` |
| Consistent with Decision #2 | ❌ | ✅ |

`GenericForeignKey` was rejected for the same reason it was rejected for images — it loses PostgreSQL referential integrity. Nullable FKs with `CheckConstraint` enforcement give full integrity while handling every cross-boundary relationship the mythology requires.

### Original Three-Type Model Proposal (Superseded)

The following excerpt is the original God/Titan/Character proposal. The implemented model extends it to Monster and Creature endpoints and uses `parent_of`, `sibling_of`, and `consort_of` rows; see the current implementation below.

```python
# divine/models.py

from django.db import models


class DivineRelationship(models.Model):
    """
    Unified relationship model covering God↔God, Titan↔Titan,
    God↔Titan, and Titan↔Character cross-boundary relationships.

    Each row has exactly one populated FK on each side.
    CheckConstraints enforce this at the PostgreSQL level.

    Does NOT inherit BaseModel — relationships are not standalone
    lore entities. They exist only in relation to God/Titan/Character.
    """

    class RelationshipType(models.TextChoices):
        PARENT   = 'parent',   'Parent'
        CHILD    = 'child',    'Child'
        SIBLING  = 'sibling',  'Sibling'
        CONSORT  = 'consort',  'Consort / Spouse'
        RIVAL    = 'rival',    'Rival'
        ALLY     = 'ally',     'Ally'

    # ----------------------------------------------------------------
    # Subject side — exactly one populated per row (enforced by DB)
    # ----------------------------------------------------------------
    from_god   = models.ForeignKey(
        'gods.God',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='relationships_as_subject'
    )
    from_titan = models.ForeignKey(
        'titans.Titan',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='relationships_as_subject'
    )

    # ----------------------------------------------------------------
    # Object side — exactly one populated per row (enforced by DB)
    # ----------------------------------------------------------------
    to_god       = models.ForeignKey(
        'gods.God',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='relationships_as_object'
    )
    to_titan     = models.ForeignKey(
        'titans.Titan',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='relationships_as_object'
    )
    to_character = models.ForeignKey(
        'characters.Character',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='divine_relationships',
        help_text="For cases like Atlas → Zoë Nightshade (Titan parent, Character child)."
    )

    # ----------------------------------------------------------------
    # Relationship detail
    # ----------------------------------------------------------------
    relationship_type = models.CharField(
        max_length=20,
        choices=RelationshipType.choices
    )
    notes        = models.TextField(blank=True, null=True)
    is_canonical = models.BooleanField(
        default=True,
        help_text="False for mythologically disputed relationships."
    )

    # ----------------------------------------------------------------
    # Database-level integrity constraints
    # ----------------------------------------------------------------
    class Meta:
        constraints = [
            # Exactly one subject FK must be populated
            models.CheckConstraint(
                check=(
                    models.Q(from_god__isnull=False, from_titan__isnull=True) |
                    models.Q(from_god__isnull=True,  from_titan__isnull=False)
                ),
                name='divine_relationship_exactly_one_subject'
            ),
            # Exactly one object FK must be populated
            models.CheckConstraint(
                check=(
                    models.Q(to_god__isnull=False,  to_titan__isnull=True,  to_character__isnull=True) |
                    models.Q(to_god__isnull=True,   to_titan__isnull=False, to_character__isnull=True) |
                    models.Q(to_god__isnull=True,   to_titan__isnull=True,  to_character__isnull=False)
                ),
                name='divine_relationship_exactly_one_object'
            ),
        ]
        indexes = [
            models.Index(fields=['from_god', 'relationship_type']),
            models.Index(fields=['from_titan', 'relationship_type']),
            models.Index(fields=['to_god']),
            models.Index(fields=['to_titan']),
            models.Index(fields=['to_character']),
        ]

    def __str__(self):
        subject = self.from_god or self.from_titan
        obj     = self.to_god or self.to_titan or self.to_character
        return f"{subject.name} → {self.relationship_type} → {obj.name}"
```

### Family Relationship Storage and API

`DivineRelationship` is the normalized family graph despite its historical model name. Each endpoint has exactly one typed FK among God, Titan, Character, Monster, and Creature. `parent_of` is directional; `sibling_of` and `consort_of` are stored once and serializers query both directions. Parent/child API views are inverse projections of the same `parent_of` edge.

God, Titan, Character, Monster, and Creature detail responses expose the same shallow shape: root `type` and `family` containing `parents`, `siblings`, `consorts`, and `children`. Each reference is `{ "name", "type", "slug" }`; relationship metadata is represented by its array, not duplicated on the reference. Empty relationship groups are `[]`. Collection serializers remain unchanged; legacy database relationship fields remain for compatibility/projection but are not emitted as top-level family fields on detail responses.

Canonical relationship rows are seeded from `data/family_relationships.json` using `seed_divine_relationships`, after all referenced entity seed commands. Unresolved references warn and are skipped; rerunning is idempotent.

### Canonical Relationship Types

| Type | Direction/storage | API projection |
| --- | --- | --- |
| `parent_of` | One row from parent to child | Parent appears under child `family.parents`; child appears under parent `family.children` |
| `sibling_of` | One row per unordered pair | Each entity appears under the other's `family.siblings` |
| `consort_of` | One row per unordered pair | Each entity appears under the other's `family.consorts` |

Family links are sourced from the reviewed cross-type map, not duplicated in each entity record.

### Idempotent Family Seeding

`seed_divine_relationships` resolves typed entity references against all five models and uses `get_or_create` for immutable relationship tuples. It stores parent links in one direction, and symmetric sibling/consort links once. Missing references are warned and skipped.

### API Response Example

```json
{
  "name": "Minotaur",
  "slug": "minotaur",
  "type": "monster",
  "family": {
    "parents": [
      { "name": "Pasiphaë", "type": "character", "slug": "pasiphae" },
      { "name": "Cretan Bull", "type": "creature", "slug": "cretan-bull" }
    ],
    "siblings": [
      { "name": "Ariadne", "type": "character", "slug": "ariadne" },
      { "name": "Phaedra", "type": "character", "slug": "phaedra" }
    ],
    "consorts": [],
    "children": []
  }
}
```

### Typed Family Relationship Summary

| Requirement | Handled By |
| --- | --- |
| Cross-type family references | Exactly one of five entity FKs on each endpoint |
| Parents and children | Directional `parent_of` row, projected into both API lists |
| Symmetric siblings and consorts | One canonical row, queried from either endpoint |
| API response consistency | Root `type`; nested `family`; typed shallow references |
| Referential integrity | Database FK and exactly-one endpoint constraints |
| Idempotent seed updates | `get_or_create` immutable family tuples |

---

## 23. Current Implemented API Reference

This section describes routes and behaviors present in the code and test suite. All versioned routes below have a trailing slash and live under `/api/v1/`. Unless noted otherwise, versioned endpoints require `X-API-Key`. List/detail representations differ by serializer; this is a quick contract reference, not a promise that every model field appears in every response. Lore entity payloads include `lore_accuracy`, `lore_notes`, and read-only `lore_sources`. Deleted entities are omitted from public lists, return 404 on detail, and are excluded from search; Admin provides soft-delete and restore actions, with no public deletion endpoint.

### Public routes

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/api/v1/` | JSON-only directory of the 14 collections plus search; no API key required |
| `GET` | `/health/live/` | Liveness; no dependency checks |
| `GET` | `/health/ready/` | PostgreSQL readiness |
| `GET` | `/api/schema/` | OpenAPI 3 schema (YAML by default; `?format=json` for JSON) |
| `GET` | `/api/docs/` | Public Swagger UI |
| `GET` | `/api/redoc/` | Public ReDoc UI |
| `POST` | `/auth/request-key/` | Request a key using `consumer_name` and `email` |
| `POST` | `/auth/verify-key/` | Verify key from `X-API-Key` header |

Except for the directory itself, these routes are outside `/api/v1/`. The directory, schema, and UI pages are public; protected versioned resource operations are identified with the `X-API-Key` security scheme. Swagger UI and ReDoc list Authentication and Health first, followed by resource groups. Key request and verification responses are rate-limited by client IP.

Unlike the public key request and verification endpoints, `POST /auth/revoke-key/` requires `X-API-Key` and revokes only the key used for that request. Auth request succeeds with `201` and fields `api_key`, `consumer_name`, `email`, `message`; verify returns `valid` and `consumer_name`.

### API directory

`GET /api/v1/` returns a flat object of collection names to relative URLs, such as `"books": "/api/v1/books/"` and `"search": "/api/v1/search/"`. It includes every collection in the table below plus search, with no `data`/`meta` envelope. The directory is JSON-only (including in a browser), performs no database or cache access, and does not consume the API-key throttle. Linked resource endpoints still require `X-API-Key`; search additionally requires `?q=<query>`. HEAD and OPTIONS are supported; write methods return `405`.

### Versioned resource routes

| Resource | Collection and detail | Implemented subresources |
| --- | --- | --- |
| Books | `/books/`, `/books/<slug>/` | `/books/<slug>/characters/`, `/gods/`, `/monsters/`, `/locations/`, `/quests/`, `/images/` |
| Characters | `/characters/`, `/characters/<slug>/` | `/images/`, `/powers/`, `/weapons/`, `/quests/` |
| Gods | `/gods/`, `/gods/<slug>/` | `/images/`, `/children/`, `/weapons/` |
| Titans | `/titans/`, `/titans/<slug>/` | `/images/` |
| Monsters | `/monsters/`, `/monsters/<slug>/` | `/images/` |
| Creatures | `/creatures/`, `/creatures/<slug>/` | `/members/` |
| Weapons | `/weapons/`, `/weapons/<slug>/` | `/images/` |
| Locations | `/locations/`, `/locations/<slug>/` | `/images/` |
| Images | `/images/` global collection | — |
| Quests | `/quests/`, `/quests/<slug>/` | `/participants/` |
| Prophecies | `/prophecies/`, `/prophecies/<slug>/` | — |
| Events | `/events/`, `/events/<slug>/` | — |
| Cabins | `/cabins/`, `/cabins/<slug>/`, `/cabins/number/<number>/` | `/campers/` |
| Factions | `/factions/`, `/factions/<slug>/` | `/members/` |
| Search | `/search/?q=<query>` | Optional `type=<entity-type>` |

Subresource paths in the table are appended to the entity detail path shown in the same row. Powers have a Character-scoped list endpoint at `/characters/<slug>/powers/` and are also embedded in Character detail; there is no standalone `/powers/` route. Images have a global paginated `/images/` collection as well as the typed galleries. Book/character role relations, family edges, quest relations, prophecy subjects, and faction members are serialized through resource detail and the listed subresources; these are not relationship CRUD routes.

### List response and error shapes

Versioned endpoints use only the JSON renderer, so opening a resource URL in a normal browser returns JSON, not a DRF page. This also applies to handled API errors; API-key protection is unchanged. Interactive HTML documentation remains at `/api/docs/` and `/api/redoc/`.

Paginated list views use a default page size of 20 (`page`, `limit`; maximum `limit` 100):

```json
{
  "data": [],
  "meta": {"total": 0, "page": 1, "limit": 20, "total_pages": 1}
}
```

Detail views return the resource-specific object. Search returns `data` and `meta` with `total`, `query`, and `type_filter`; each result includes `type`, `slug`, `url`, `title`, `description`, and `wiki_url`.

Handled errors use `{ "error": { "code": "...", "message": "..." } }`. Invalid choices use a more specific payload:

```json
{
  "error": {
    "code": "INVALID_FILTER_VALUE",
    "message": "tier: 'not-a-tier' is not a valid choice.",
    "valid_values": ["olympian", "minor", "chthonic", "primordial", "river_god", "nature_deity"]
  }
}
```

The `valid_values` above is illustrative; the actual values depend on the filter. Other handled invalid inputs use `BAD_REQUEST`. Unhandled server errors are not converted into fabricated successful responses.

### Typed relationship responses

#### Family and DivineRelationship graph

God, Titan, Character, Monster, and Creature detail responses each contain the root `type` and:

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

Each shallow entity reference is `{ "name", "type", "slug" }`; the four arrays are always present and empty groups are `[]`. The graph is stored in `DivineRelationship`, with explicit typed FKs for exactly one God, Titan, Character, Monster, or Creature on each side. The relationship kinds are `parent_of`, `sibling_of`, and `consort_of`; parent edges are directional, while sibling and consort edges are stored once and queried symmetrically. There is no raw relationship-row endpoint.

The idempotent `seed_divine_relationships` command reads `data/family_relationships.json` after the entity seeds. Missing entity references warn and skip the affected relationship. The current file contains 383 rows.

#### Book-character and typed Book roles

`Book` details expose `narrators`, `main_characters`, and `antagonists` as typed `{ "type", "slug", "name" }` references. Supported types are Character, God, Titan, Monster, and Creature. Compatibility slug fields remain on the serializer. `narrator_slug` is null when multiple typed narrator records are present; `narrator_slugs` contains Character narrator slugs. The `/books/<slug>/characters/` subresource returns `CharacterListSerializer` records, and `/books/<slug>/gods/` returns God records linked through each God’s `books_appeared_in` relation.

Book roles are seeded from `data/book_character_relationships.json` with `seed_book_relationships`; it contains 12 book relationship records. There is no standalone role-relationship endpoint.

#### Other typed links

- **Quest detail:** `participants` and `casualties` are typed `{type, slug, name}` records for Character, God, Titan, or Monster. Backward-compatible Character slug fields remain. `/quests/<slug>/participants/` returns Character list records only.
- **Event detail:** participants are exposed as `participant_character_slugs`, `participant_god_slugs`, `participant_titan_slugs`, and `participant_monster_slugs`; `casualties` are typed `{type, slug, name}` for Character, God, Titan, or Monster, with `casualty_slugs` retained for Character compatibility.
- **Prophecy detail:** `subjects` is typed `{type, slug, name}` for Character, God, Titan, or Monster; `subject_slugs` remains for Character compatibility.
- **Faction detail and `/factions/<slug>/members/`:** typed member records for Character, God, Titan, or Monster; leaders are also typed.
- **Location list/detail:** `controlled_by` is a typed object for God, Titan, Character, or Monster.
- **Monster detail:** typed defeat records supplement compatibility slug lists; God defeat links are represented separately.
- **Character detail and `/characters/<slug>/powers/`:** `powers` is embedded in Character detail and the nested list returns Power fields `id`, `name`, `wiki_url`, `description`, `source`, `type`, `scope`, `limitations`, `is_passive`, `is_book_specific`, `first_demonstrated_book`, and `display_order`. The nested list supports `source`, `type`, and `is_passive` filters; no standalone Power endpoint exists.

### List filters

Parameters below are declared by current filter sets. Every lore entity list also supports strict `lore_accuracy` filtering with the choices documented in Section 16. Choice values are strict; use the model/filter choices rather than assuming that every historical planning value is valid. `type` is an alias only on the resources listed here.

| List | Supported filters |
| --- | --- |
| Books | `series`, `book_type`, `type` (alias), `parent_collection` / `parent-collection`, `narrator`, `narrator_character`, `narrator_god`, `narrator_titan`, `narrator_monster`, `narrator_creature`, `main_character`, `main_character_god`, `main_character_titan`, `main_character_monster`, `main_character_creature`, `antagonist`, `antagonist_god`, `antagonist_titan`, `antagonist_monster`, `antagonist_creature` |
| Characters | `character_type`, `type` (alias), `affiliation`, `species`, `status`, `gender`, `greek_or_roman`, `divine_parent`, `first_appearance_book`, `book`, `is_demigod`, `is_big_three_child`, `is_hunter_of_artemis`, `is_oracle`, `is_possessed`, `can_see_through_mist`, `has_adhd`, `cabin` |
| Character Powers subresource | `source`, `type`, `is_passive` |
| Gods | `tier`, `affiliation`, `status`, `has_cabin`, `is_big_three`, `roman_only` |
| Titans | `alignment`, `generation`, `status` |
| Monsters | `monster_type`, `type` (alias), `allegiance`, `can_reform`, `defeated_by`, `defeated_by_god`, `defeated_in_book`, `book` |
| Creatures | `alignment` |
| Weapons | `weapon_type`, `type` (alias), `material`, `owner_character`, `owner_god`, `owner_titan`, `forged_by`, `transforms`, `passes_through_mortals`, `book` |
| Locations | `location_type`, `type` (alias), `is_hidden_from_mortals`, `controlled_by_god`, `controlled_by_titan`, `controlled_by_character`, `controlled_by_monster`, `book`, `first_appearance_book`, `earlier_mention_book` |
| Prophecies | `fulfilled_in`, `subject`, `subject_god`, `subject_titan`, `subject_monster`, `book` |
| Quests | `book`, `led_by`, `participant`, `participant_god`, `participant_titan`, `participant_monster`, `casualty`, `casualty_god`, `casualty_titan`, `casualty_monster` |
| Events | `event_type`, `type` (alias), `in_universe_timeframe` (case-insensitive substring), `date_precision`, `book`, `location`, `participant_character`, `participant_god`, `participant_titan`, `participant_monster`, `casualty`, `casualty_god`, `casualty_titan`, `casualty_monster` |
| Cabins | `is_honorary`, `is_empty`, `position`, `deity` |
| Factions | `faction_type`, `alignment`, `book` |
| Image collection | `source_type`, `category`, exact `source_url`, exact `wiki_url` |
| Image galleries | `source_type`, `category` |
| Search | `q` (required query), optional `type` entity filter |

Boolean filters accept exactly lowercase `true` or `false`; omitted parameters do not filter. Values such as `True`, `1`, `yes`, arbitrary text, empty strings, and repeated boolean values return `400`.

### Sort fields and defaults

Use `?sort=<field>[&order=asc|desc]`; `order` defaults to `asc` when a sort field is supplied alone. Supplying `order` without `sort`, repeated `sort` or `order` values, invalid directions, and invalid or disallowed sort fields return `400`. If neither `sort` nor `order` is supplied, existing `?ordering=` behavior remains available on views using DRF's ordering backend. For Titan, Event, and Location default ordering, records without a curated order sort after ranked records. Sort fields are allowlisted per collection:

| List | Default ordering | `sort` allowlist |
| --- | --- | --- |
| Books | `series`, `book_number` | `book_number`, `published_date`, `title` |
| Characters | `name` | `name`, `status`, `age_first_appearance` |
| Character Powers subresource | `display_order`, `name` | `display_order`, `name`, `source`, `type`, `is_passive`, `is_book_specific` |
| Gods | `name` | `name`, `tier`, `cabin_number` |
| Titans | `display_order`, `name` | `display_order`, `name`, `alignment`, `status` |
| Monsters | `name` | `name`, `allegiance`, `monster_type` |
| Creatures | `name` | `name`, `alignment` |
| Weapons | `name` | `name`, `weapon_type`, `material` |
| Locations | `location_order`, `name` | `location_order`, `name`, `location_type` |
| Prophecies | `title` | `title` |
| Quests | `book__book_number` | `title`, `book__book_number` |
| Events | `chronology_order`, `name` | `chronology_order`, `name`, `in_universe_timeframe`, `date_precision`, `book__book_number` |
| Cabins | `number` | `number` |
| Factions | `name` | `name`, `alignment` |
| Image collection | `id` | `id`, `url`, `source_type`, `category`, `uploaded_at` |
| Image galleries | `display_order`, image PK | no declared `sort`/`order` allowlist |

Nested list views inherit pagination; the Character Powers subresource additionally supports the filters and sort fields documented above. Titan `display_order`, Event `chronology_order`, and Location `location_order` are implemented on their collection endpoints. Sparse fieldsets (`fields=`) and relationship expansion (`include=`) are not supported.

### Image collection and gallery payload

`GET /api/v1/images/` returns a paginated global collection. It accepts `source_type`, `category`, exact `source_url`, and exact `wiki_url` filters. Its default order is image ID ascending; supported sort fields are listed above. The global collection and gallery serializers return `id`, `url`, `thumbnail_url`, `alt_text`, `source_type`, `source_type_display`, `category`, `category_display`, `artist_name`, `artist_url`, `source_url`, `license`, `license_url`, `width`, `height`, `file_format`, `wiki_url`, and `uploaded_at`. Embedded primary-image objects include `id`, `url`, `thumbnail_url`, `alt_text`, `source_type`, `category`, `artist_name`, `artist_url`, `source_url`, `license`, `license_url`, and `wiki_url`. Gallery filters are `source_type` and `category`; order is `display_order`, then image PK. Wiki seed records have both license fields null; the API does not stream image bytes or guarantee runtime placeholder fallback.

---

## 24. Future Work

The following items are intentionally deferred. They are not implemented API guarantees and should be reviewed before schema/data changes.

1. **Claim-level provenance and review workflow.** Entity-level `lore_accuracy`, `lore_notes`, and `lore_sources` are implemented. Consider finer-grained citations attached to individual claims or fields, review timestamps, and editorial workflows if the data-curation process requires them; these would need separate requirements and schema design.
2. **Image rights and fallback policy.** Review licensing and attribution for wiki URLs whose license metadata is absent, define v1 publication rules, and implement runtime broken-image/placeholder behavior and any image hosting/CDN migration. The seed importer records no license when the source provides none; it does not grant reuse rights.
3. **Universe expansion.** Review future seed/model scope for Heroes of Olympus, Kane Chronicles, Magnus Chase, Trials of Apollo, and other companion works. Add domain-specific fields only after the scope and migration/data requirements are approved.

*Reference: [Riordan Wiki](https://riordan.fandom.com/wiki/Riordan_Wiki)*
