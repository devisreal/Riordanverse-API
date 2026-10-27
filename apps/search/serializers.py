from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

# Maps content_type app_label.model to API type label and URL prefix.
MODEL_TYPE_MAP = {
    'characters.character': ('character', '/api/v1/characters/'),
    'divinities.god': ('god', '/api/v1/gods/'),
    'divinities.titan': ('titan', '/api/v1/titans/'),
    'bestiary.monster': ('monster', '/api/v1/monsters/'),
    'bestiary.creature': ('creature', '/api/v1/creatures/'),
    'items.weapon': ('weapon', '/api/v1/weapons/'),
    'locations.location': ('location', '/api/v1/locations/'),
    'narrative.book': ('book', '/api/v1/books/'),
    'narrative.quest': ('quest', '/api/v1/quests/'),
    'narrative.prophecy': ('prophecy', '/api/v1/prophecies/'),
    'narrative.event': ('event', '/api/v1/events/'),
    'organizations.cabin': ('cabin', '/api/v1/cabins/'),
    'organizations.faction': ('faction', '/api/v1/factions/'),
}


class SearchResultSerializer(serializers.Serializer):
    """Serialize a Watson entry as a flat, typed API result."""

    type = serializers.SerializerMethodField()
    slug = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    wiki_url = serializers.SerializerMethodField()

    def _get_model_key(self, obj):
        content_type = obj.content_type
        return f'{content_type.app_label}.{content_type.model}'

    def get_type(self, obj) -> str:
        return MODEL_TYPE_MAP.get(self._get_model_key(obj), ('unknown', ''))[0]

    def get_slug(self, obj) -> str | None:
        try:
            instance = obj.object
        except AttributeError, ObjectDoesNotExist:
            return None
        return getattr(instance, 'slug', None) if instance is not None else None

    def get_url(self, obj) -> str | None:
        _, prefix = MODEL_TYPE_MAP.get(self._get_model_key(obj), ('unknown', ''))
        slug = self.get_slug(obj)
        return f'{prefix}{slug}/' if prefix and slug else None

    def get_title(self, obj) -> str:
        return obj.title or ''

    def get_description(self, obj) -> str:
        return obj.description or ''

    def get_wiki_url(self, obj) -> str | None:
        try:
            instance = obj.object
        except AttributeError, ObjectDoesNotExist:
            return None
        return getattr(instance, 'wiki_url', None) if instance is not None else None


class SearchMetaSchemaSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    query = serializers.CharField()
    type_filter = serializers.CharField(allow_null=True)


class SearchResponseSchemaSerializer(serializers.Serializer):
    data = SearchResultSerializer(many=True)
    meta = SearchMetaSchemaSerializer()
