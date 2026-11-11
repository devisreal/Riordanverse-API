from django.test import SimpleTestCase

from apps.bestiary.serializers import (
    CreatureDetailSerializer,
    CreatureListSerializer,
    MonsterDetailSerializer,
    MonsterListSerializer,
)
from apps.characters.serializers import (
    CharacterDetailSerializer,
    CharacterListSerializer,
    PowerSerializer,
)
from apps.divinities.serializers import (
    GodDetailSerializer,
    GodListSerializer,
    TitanDetailSerializer,
    TitanListSerializer,
)
from apps.images.serializers import ImageListSerializer, ImageSerializer
from apps.items.serializers import WeaponDetailSerializer, WeaponListSerializer
from apps.locations.serializers import LocationDetailSerializer, LocationListSerializer
from apps.narrative.serializers import (
    BookDetailSerializer,
    BookListSerializer,
    BookSummarySerializer,
    EventDetailSerializer,
    EventListSerializer,
    ProphecyDetailSerializer,
    ProphecyListSerializer,
    QuestDetailSerializer,
    QuestListSerializer,
)
from apps.organizations.serializers import (
    CabinDetailSerializer,
    CabinListSerializer,
    FactionDetailSerializer,
    FactionListSerializer,
)
from apps.search.serializers import SearchResultSerializer


class WikiUrlSerializationTests(SimpleTestCase):
    def test_wiki_url_is_exposed_in_entity_and_nested_serializers(self):
        serializers = (
            CharacterListSerializer,
            CharacterDetailSerializer,
            PowerSerializer,
            GodListSerializer,
            GodDetailSerializer,
            TitanListSerializer,
            TitanDetailSerializer,
            MonsterListSerializer,
            MonsterDetailSerializer,
            CreatureListSerializer,
            CreatureDetailSerializer,
            WeaponListSerializer,
            WeaponDetailSerializer,
            LocationListSerializer,
            LocationDetailSerializer,
            CabinListSerializer,
            CabinDetailSerializer,
            FactionListSerializer,
            FactionDetailSerializer,
            BookSummarySerializer,
            BookListSerializer,
            BookDetailSerializer,
            ProphecyListSerializer,
            ProphecyDetailSerializer,
            QuestListSerializer,
            QuestDetailSerializer,
            EventListSerializer,
            EventDetailSerializer,
            ImageListSerializer,
            ImageSerializer,
            SearchResultSerializer,
        )

        for serializer_class in serializers:
            with self.subTest(serializer=serializer_class.__name__):
                self.assertIn('wiki_url', serializer_class().fields)
