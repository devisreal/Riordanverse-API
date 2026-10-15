from django.db import models


class BaseModel(models.Model):
    """Abstract base model shared by all lore entities."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    wiki_url = models.URLField(blank=True, null=True)

    class Meta:
        abstract = True
