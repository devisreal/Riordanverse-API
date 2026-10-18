from django.test import TestCase

from apps.narrative.serializers import (
    BookDetailSerializer,
    EventDetailSerializer,
    ProphecyDetailSerializer,
    ProphecyListSerializer,
    QuestDetailSerializer,
)
from tests.factories import (
    make_book,
    make_character,
    make_event,
    make_prophecy,
    make_quest,
)


class BookDetailSerializerTests(TestCase):
    def test_includes_quest_and_event_counts(self):
        book = make_book(title='The Lightning Thief', book_number=1)
        make_quest(title='The Lightning Thief Quest', book=book)
        make_event(name='Capture the Flag', book=book)

        data = BookDetailSerializer(book).data

        self.assertEqual(data['quest_count'], 1)
        self.assertEqual(data['event_count'], 1)


class ProphecySerializerTests(TestCase):
    def setUp(self):
        self.prophecy = make_prophecy(
            title='The Great Prophecy',
            text='A half-blood of the eldest gods\nShall reach sixteen against all odds\nAnd a choice must be made',
        )

    def test_list_serializer_has_prophecy_lines(self):
        data = ProphecyListSerializer(self.prophecy).data
        self.assertIn('prophecy_lines', data)

    def test_prophecy_lines_is_list(self):
        data = ProphecyListSerializer(self.prophecy).data
        self.assertIsInstance(data['prophecy_lines'], list)

    def test_prophecy_lines_splits_correctly(self):
        data = ProphecyListSerializer(self.prophecy).data
        self.assertEqual(len(data['prophecy_lines']), 3)
        self.assertEqual(data['prophecy_lines'][0], 'A half-blood of the eldest gods')

    def test_detail_serializer_returns_both_text_and_lines(self):
        data = ProphecyDetailSerializer(self.prophecy).data
        self.assertIn('text', data)
        self.assertIn('prophecy_lines', data)
        self.assertIn('\n', data['text'])
        self.assertIsInstance(data['prophecy_lines'], list)

    def test_empty_lines_stripped(self):
        prophecy = make_prophecy(text='Line one\n\n\nLine two')
        data = ProphecyDetailSerializer(prophecy).data
        self.assertEqual(len(data['prophecy_lines']), 2)

    def test_delivered_by_slug_null(self):
        data = ProphecyDetailSerializer(self.prophecy).data
        self.assertIsNone(data['delivered_by_slug'])

    def test_delivered_by_slug_set(self):
        oracle = make_character(name='Rachel Dare')
        self.prophecy.delivered_by = oracle
        self.prophecy.save()
        data = ProphecyDetailSerializer(self.prophecy).data
        self.assertEqual(data['delivered_by_slug'], 'rachel-dare')


class QuestSerializerTests(TestCase):
    def setUp(self):
        self.quest = make_quest(title="Quest for Zeus's Lightning Bolt")

    def test_list_serializer_fields(self):
        data = QuestDetailSerializer(self.quest).data
        self.assertIn('slug', data)
        self.assertIn('title', data)
        self.assertIn('participant_slugs', data)
        self.assertIn('casualty_slugs', data)

    def test_participant_slugs_empty_by_default(self):
        data = QuestDetailSerializer(self.quest).data
        self.assertEqual(data['participant_slugs'], [])

    def test_participant_slugs_populated(self):
        percy = make_character(name='Percy Jackson')
        self.quest.participants.add(percy)
        data = QuestDetailSerializer(self.quest).data
        self.assertIn('percy-jackson', data['participant_slugs'])


class EventSerializerTests(TestCase):
    def setUp(self):
        self.event = make_event(name='Battle of Manhattan')

    def test_participant_character_slugs_empty(self):
        data = EventDetailSerializer(self.event).data
        self.assertEqual(data['participant_character_slugs'], [])

    def test_participant_god_slugs_populated(self):
        from tests.factories import make_god

        god = make_god(name='Poseidon')
        self.event.participant_gods.add(god)
        data = EventDetailSerializer(self.event).data
        self.assertIn('poseidon', data['participant_god_slugs'])

    def test_event_type_display(self):
        data = EventDetailSerializer(self.event).data
        self.assertEqual(data['event_type_display'], 'Battle')
