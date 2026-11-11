# Riordanverse API — Deployment

This guide covers production hosting for the unofficial Riordanverse reference API.
Entire-Riordanverse coverage is the ambition; the current dataset focuses on
Greek/Roman lore. For local development and Docker Compose,
see the [README](README.md#setup). For contribution and asset-authoring details,
see [CONTRIBUTING.md](CONTRIBUTING.md).

## Intended public deployment

The intended website is `https://riordanverse.cc`, with the API at
`https://riordanverse.cc/api/v1/` and Swagger UI at
`https://riordanverse.cc/api/docs/`. The domain is registered, but this does **not**
confirm configured DNS, hosting, a valid HTTPS certificate, or public availability.
Configure the provider's custom domain and DNS, provision HTTPS, then verify the
routes before treating these URLs as live. Local workflows retain
`http://127.0.0.1:8000` (or `http://localhost:8000` for Compose).

The repository is `https://github.com/devisreal/Riordanverse-API`. It is currently
private; authorize hosting integrations and Git access accordingly. Website,
issue-template, and image-audit links use the renamed repository. Package names
are `riordanverse-api` (Python) and `riordanverse-api-website` (frontend); runtime
module paths and API contracts are unchanged by branding. Verify hosting
integrations after the repository rename; this branch does not configure those
integrations or change repository visibility.

## Runtime and configuration

Production uses Gunicorn (WSGI), PostgreSQL, and WhiteNoise for collected static
assets. Redis provides shared API-key caching and throttling; if unavailable,
key validation falls back to PostgreSQL and quotas become process-local.
`config/wsgi.py` defaults to production settings. Set the environment explicitly:

| Variable | Production value |
| --- | --- |
| `DJANGO_SETTINGS_MODULE` | `config.settings.production` |
| `SECRET_KEY` | Stable, randomly generated secret; never commit it |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | Comma-separated actual hostnames, without schemes or paths |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | Production PostgreSQL connection; port defaults to `5432` |
| `REDIS_URL` | Private Redis connection URL |
| `CORS_ALLOWED_ORIGINS` | Explicit allowed browser origins, or an empty value for no cross-origin access |
| `CSRF_TRUSTED_ORIGINS` | Full HTTPS origins when needed for trusted cross-origin form submissions; defaults to empty |
| `PORT` | Listening port; defaults to `8000` |
| `WEB_CONCURRENCY` | Gunicorn worker count; defaults to `1` |
| `APP_VERSION` | Optional release identifier returned by health endpoints |

The app reads individual `DB_*` variables, not `DATABASE_URL`. A host may expose
its own database variables; map them to the names above. Never use the Compose
fallback database password in production. `.env` is local configuration, not a
file to upload into a public repository or bake into an image.

For the intended domain, set `ALLOWED_HOSTS=riordanverse.cc` once the host is
configured. Add other hostnames only when actually needed (for example, a
provider health-check hostname). If trusted cross-origin forms require it, use
`CSRF_TRUSTED_ORIGINS=https://riordanverse.cc`; do not add unrelated origins.
Same-origin website/API access does not require a CORS entry. Enable only actual
external consumer origins in `CORS_ALLOWED_ORIGINS`.

## Application email

The mailboxes `hello@riordanverse.cc` (general inquiries) and
`support@riordanverse.cc` (API support and application emails) exist. This is not
confirmation of outbound SMTP or working application email delivery. The default
application sender is `Riordanverse API <support@riordanverse.cc>` and the server
error sender is `support@riordanverse.cc`; override them with `DEFAULT_FROM_EMAIL`
and `SERVER_EMAIL` as needed. These settings define identities, not mail delivery.

Before sending application emails from `support@riordanverse.cc`:

- Configure an application email backend and a transactional provider or SMTP
  service, with its host/port, TLS requirements, and provider credentials stored
  as deployment secrets. A mailbox alone is not a sending integration.
- Verify the sending address/domain with the provider and publish the required
  DNS authentication records (SPF/DKIM and an appropriate DMARC policy).
- Confirm sender/reply-to settings, any sandbox or recipient restrictions, and
  test real delivery and failure handling before enabling a sending flow.

These are deployment prerequisites, not a claim that an email backend or sending
flow is implemented. API keys are still returned immediately by
`/auth/request-key/`, not emailed; no email-verification requirement is added.

## Deploy the Docker image

The multi-stage [Dockerfile](Dockerfile) builds frontend assets with Node.js 22,
installs locked Python dependencies, and collects static files. Its final image
runs as a non-root user and does not contain frontend build tooling. Build-time
settings placeholders are not runtime credentials. Database migrations and seeds
are deliberately not part of the image build or web-process startup.

For Railway, connect the repository and intended branch, select the Dockerfile
builder, use the repository root, and configure the runtime variables above.
Railway uses the Dockerfile, **not** `compose.yaml`. Leave the start-command
override unset to use the image's Gunicorn `CMD`.

Configure a controlled pre-deploy migration command:

```bash
/opt/venv/bin/python manage.py migrate --noinput
```

After deployment, use `railway ssh` from your computer to open the running app
container. From `/app`, run administrative commands only when intended:

```bash
/opt/venv/bin/python manage.py seed_all
/opt/venv/bin/python manage.py createsuperuser
```

These commands modify the deployed database. `railway run` is different: it runs
commands locally with service variables and may not reach private database hosts.
The explicit Python path avoids an SSH shell selecting the system Python, which
does not have Django installed. Do not install another copy of Django in the shell.

## Deploy without Docker

Use Python 3.14+, uv, and Node.js 22+ with npm. Configure production variables first,
then install runtime dependencies, build frontend assets, and collect static files:

```bash
export DJANGO_SETTINGS_MODULE=config.settings.production
uv sync --locked --no-dev
npm ci --include=dev --prefix website/static_src
npm run build --prefix website/static_src
uv run --locked --no-dev python manage.py collectstatic --noinput
uv run --locked --no-dev python manage.py check --deploy
```

Node build tools are needed during the build, not in the running web process.
Generated CSS, Motion JavaScript, and Swagger assets are Git-ignored; every fresh
build must generate them **before** `collectstatic`. WhiteNoise serves hashed,
compressed files from `STATIC_ROOT` and does not serve user uploads.

Run migrations as a release step, then start the web process:

```bash
uv run --locked --no-dev python manage.py migrate --noinput
uv run --locked --no-dev gunicorn --config gunicorn.conf.py
```

Seed separately when appropriate. Do not use `runserver` for production.
Gunicorn binds `0.0.0.0:$PORT`, uses one `gthread` worker by default with four
threads per worker, and reads the worker count from `WEB_CONCURRENCY`. Size this
for the hosting plan. Gunicorn errors go to stderr; Django emits structured request
logs without duplicate Gunicorn access logs.

## HTTPS, health checks, and browser access

Production redirects HTTP to HTTPS and sets secure session/CSRF cookies. It trusts
`X-Forwarded-Proto` through `SECURE_PROXY_SSL_HEADER`; only deploy behind an edge
that controls that header and prevents untrusted clients from spoofing it.
Review Gunicorn's proxy trust and DRF client-IP handling for the provider so
anonymous quotas do not accidentally group everyone under the proxy address.

The current HSTS policy is 300 seconds, without subdomain inclusion or preload.
Review it deliberately before changing it. Set the actual domain in `ALLOWED_HOSTS`
and the appropriate full HTTPS origins in `CSRF_TRUSTED_ORIGINS`. CORS and CSRF are
separate controls. Cross-origin browser access supports `X-API-Key` in addition
to the standard CORS request headers. Enable only the intended frontend origins
in the API deployment's environment (scheme, hostname, and port must match):

```dotenv
CORS_ALLOWED_ORIGINS=https://your-frontend.example,http://localhost:8080
```

An empty value disables cross-origin access. All origins are **not** allowed by
default, and cookies/cross-origin credentials remain disabled. No code change is
needed to add an origin. Verify a real browser request and its preflight; for an
initial preflight inspection:

```bash
curl -i -X OPTIONS "$BASE_URL/api/v1/books/" \
  -H "Origin: http://localhost:8080" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: x-api-key"
```

Expect the allowed origin and `x-api-key` in the corresponding allow headers.
An unapproved origin must not receive `Access-Control-Allow-Origin`. Curl does
not enforce CORS; also test from a page served at the approved origin. Use a
disposable key and revoke it afterward.

Use an HTTPS API URL from an HTTPS frontend to avoid mixed-content blocking. If
the frontend serves its own Content Security Policy, its `connect-src` directive
must allow the API origin. That is a setting on the consuming website, not a
reason to loosen this API's CSP. API-key requests do not need cookies or
`credentials: 'include'`, and enabling CORS does not require adding frontend
origins to `CSRF_TRUSTED_ORIGINS` for these read-only requests.

`CORS_EXPOSE_HEADERS` controls which response headers JavaScript can read; it does
not permit an authentication request header. A browser cannot keep an embedded
key secret, even when CORS is configured. **Keys shipped to browsers are visible
to users** in bundles, developer tools, and network requests; frontend build-time
environment variables do not hide them. Copied keys can consume the owner's
quota. Prefer a backend/serverless proxy for private keys. CORS is not an access
control substitute; authentication and API quotas still apply.

- `/health/live/` checks process responsiveness.
- `/health/ready/` checks PostgreSQL; Redis is not a readiness dependency.

Verify the provider's probe hostname is allowed and its HTTPS/proxy headers are
compatible with the redirect policy. Do not assume an HTTP probe will succeed
without checking the actual provider configuration.

Before launch, smoke-test the homepage, hashed CSS/JS, Swagger, the API directory,
an authenticated data request, rate-limit headers, admin login, and readiness.
API keys are issued immediately by `/auth/request-key/`; there is currently no
email-verification delivery flow. `/auth/verify-key/` checks key validity, not
ownership of an email address.

## Content Security Policy rollout

Django emits `Content-Security-Policy-Report-Only` on application responses using
its built-in middleware. This is an observation stage, **not an enforced CSP**:
violations are logged in browser developer tools but resources are not blocked.
There is no reporting endpoint or central violation collection yet.

The default policy restricts scripts and connections to the same origin, with a
fresh nonce for Swagger's official inline initializer; it does not allow inline
script handlers or `eval`. Inline styles remain allowed for Motion, Swagger, and
admin widgets. ReDoc alone permits its existing jsDelivr script, Google Fonts,
ReDoc CDN logo, and blob workers. Those exceptions do not apply to the landing page or Swagger.
ReDoc is pinned to the compatible `2.5.2` CDN bundle (the upstream `@latest`
bundle is no longer a drop-in classic script). It is not self-hosted; review
upgrades and their CSP requirements rather than switching back to `@latest`.

Swagger responses are marked private/no-store so intermediaries must not cache
nonce-bearing HTML. Do not add a reverse-proxy/CDN cache rule that overrides that
header. WhiteNoise's static responses need not carry an HTML document policy.

Before promoting a policy to `SECURE_CSP`, check actual production browser reports
for the landing page, themes, animations, Swagger authorization/Try it out, ReDoc,
and authenticated admin forms/widgets. Recheck any CDN or separately hosted static
origin. Add only narrowly justified sources; do not solve reports by allowing
all scripts, inline scripts, or `unsafe-eval` globally. A CSP supplements escaping
and safe DOM handling; it does not replace them.

## Backups and release safety

- Take a PostgreSQL backup before risky migrations or deleting a deployment.
- Configure managed volume/database backups in your hosting provider and test a
  restore. `compose.yaml` does not provision Railway backups or a backup service.
- Keep an independent copy of important backups and store secrets separately.
- Consumer and hashed API-key records live in the database; raw keys cannot be
  recovered from a backup. Preserve the original key securely.
- A database restored from backup is distinct from rebuilding lore with seed data.
  Seeding does not recreate production consumers or their keys.
- Local PostgreSQL, Compose PostgreSQL, and Railway PostgreSQL are separate unless
  you explicitly configure them otherwise. Confirm the target before any write.
- `docker compose down` preserves named local volumes; `down -v` deletes them.

The project license does not grant rights to lore, datasets, wiki image URLs, or
third-party images. Review the [license scope](LICENSE) and asset provenance before
redistributing a deployment's content.
