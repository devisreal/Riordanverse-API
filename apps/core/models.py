from django.db import models
from django.utils import timezone


class LoreAccuracy(models.TextChoices):
    UNREVIEWED = 'unreviewed', 'Unreviewed'
    CONFIRMED = 'confirmed', 'Confirmed Canon'
    APPROXIMATE = 'approximate', 'Approximate / Paraphrased'
    DISPUTED = 'disputed', 'Disputed Between Sources'
    FAN_INTERPRETATION = 'fan_interpretation', 'Fan Interpretation'


class LoreSourceType(models.TextChoices):
    PRIMARY_TEXT = 'primary_text', 'Primary Text'
    AUTHOR_STATEMENT = 'author_statement', 'Author Statement'
    OFFICIAL_REFERENCE = 'official_reference', 'Official Reference'
    SECONDARY_REFERENCE = 'secondary_reference', 'Secondary Reference'
    OTHER = 'other', 'Other'


class SoftDeleteQuerySet(models.QuerySet):
    """QuerySet operations that preserve records instead of deleting them."""

    def delete(self):
        return self.soft_delete()

    def soft_delete(self):
        deleted_count = 0
        for instance in self.filter(is_deleted=False).iterator():
            deleted_count += instance.soft_delete()
        return deleted_count, {self.model._meta.label: deleted_count}

    def restore(self):
        restored_count = 0
        for instance in self.filter(is_deleted=True).iterator():
            restored_count += instance.restore()
        return restored_count, {self.model._meta.label: restored_count}

    def hard_delete(self):
        return super().delete()


class ActiveObjectsManager(models.Manager.from_queryset(SoftDeleteQuerySet)):
    """The default manager, which exposes only active lore records."""

    use_in_migrations = True

    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class AllObjectsManager(models.Manager.from_queryset(SoftDeleteQuerySet)):
    """Unfiltered manager for administration, seeding, and FK resolution."""

    use_in_migrations = True


class LoreSource(models.Model):
    """A reusable source citation associated with one or more lore entities."""

    title = models.CharField(max_length=255)
    source_type = models.CharField(
        max_length=32,
        choices=LoreSourceType.choices,
        default=LoreSourceType.SECONDARY_REFERENCE,
    )
    url = models.URLField(blank=True)
    citation = models.CharField(
        max_length=512,
        blank=True,
        help_text='Book, chapter, page, interview date, or other precise locator.',
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('title', 'pk')

    def __str__(self):
        return self.title


class BaseModel(models.Model):
    """Abstract base model shared by all lore entities."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    wiki_url = models.URLField(blank=True, null=True)
    lore_accuracy = models.CharField(
        max_length=20,
        choices=LoreAccuracy.choices,
        default=LoreAccuracy.UNREVIEWED,
        db_index=True,
    )
    lore_notes = models.TextField(blank=True)
    lore_sources = models.ManyToManyField(
        LoreSource,
        blank=True,
        related_name='+',
    )
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    objects = ActiveObjectsManager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True
        base_manager_name = 'all_objects'
        default_manager_name = 'objects'

    def soft_delete(self):
        if self.pk is None or self.is_deleted:
            return 0
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(
            using=self._state.db,
            update_fields=('is_deleted', 'deleted_at', 'updated_at'),
        )
        return 1

    def restore(self):
        if self.pk is None or not self.is_deleted:
            return 0
        self.is_deleted = False
        self.deleted_at = None
        self.save(
            using=self._state.db,
            update_fields=('is_deleted', 'deleted_at', 'updated_at'),
        )
        return 1

    def delete(self, using=None, keep_parents=False):
        if using is not None:
            self._state.db = using
        deleted = self.soft_delete()
        if not deleted:
            return 0, {}
        return deleted, {self._meta.label: deleted}

    def hard_delete(self, using=None, keep_parents=False):
        return super().delete(using=using, keep_parents=keep_parents)
