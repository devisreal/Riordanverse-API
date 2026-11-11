def update_or_create_by_expected_slug(model, expected_slug, defaults, fallback=None):
    """Upsert a seed entity by canonical slug, preserving legacy primary keys by fallback."""
    if not expected_slug:
        raise ValueError('A canonical expected_slug is required for entity seed upserts.')

    defaults = {**defaults, 'slug': expected_slug}
    if fallback and 'name' in fallback:
        defaults.setdefault('name', fallback['name'])
    existing = model.all_objects.filter(slug=expected_slug).first()
    if existing is None and fallback:
        existing = model.all_objects.filter(**fallback).order_by('pk').first()

    lookup = {'pk': existing.pk} if existing is not None else {'slug': expected_slug}
    return model.all_objects.update_or_create(**lookup, defaults=defaults)
