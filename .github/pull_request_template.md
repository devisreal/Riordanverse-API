## What does this PR do?

<!-- Briefly describe the change -->

## Type of change

- [ ] Bug fix
- [ ] New feature
- [ ] Refactor / cleanup
- [ ] Docs / config
- [ ] Chore / tooling
- [ ] Lore data / seed data

## Checklist

- [ ] `uv run ruff check .` passes
- [ ] `uv run ruff format --check .` passes
- [ ] `uv run python manage.py check --settings=config.settings.test` passes
- [ ] `uv run python manage.py makemigrations --check --dry-run --settings=config.settings.test` passes
- [ ] `uv run python manage.py test --settings=config.settings.test` passes
- [ ] `.env.example` updated if new env vars were added
- [ ] `important-notes.md` consulted for relevant constraints (e.g. `JSONField` not `ArrayField`)

## Migration changes

- [ ] No migrations in this PR
- [ ] New migration(s) included — confirmed reversible

## Screenshots / API responses (if applicable)
