from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.narrative.models import (
    EventCasualty,
    ProphecySubject,
    Quest,
    QuestCasualty,
    QuestParticipant,
)
from tests.makers import (
    make_book,
    make_character,
    make_event,
    make_god,
    make_monster,
    make_prophecy,
    make_quest,
    make_titan,
)


class ProphecyModelTests(TestCase):
    def setUp(self):
        self.prophecy = make_prophecy(
            title='The Great Prophecy',
            text='A half-blood of the eldest gods\nShall reach sixteen against all odds',
        )

    def test_str(self):
        self.assertEqual(str(self.prophecy), 'The Great Prophecy')

    def test_slug_generated_from_title(self):
        self.assertEqual(self.prophecy.slug, 'the-great-prophecy')

    def test_text_stores_newlines(self):
        self.assertIn('\n', self.prophecy.text)

    def test_subject_m2m(self):
        character = make_character(name='Percy Jackson')
        self.prophecy.subject.add(character)
        self.assertIn(character, self.prophecy.subject.all())

    def test_typed_subject_links_support_all_entity_types(self):
        entities = (
            ('subject_character', make_character(name='Percy Jackson')),
            ('subject_god', make_god(name='Ares')),
            ('subject_titan', make_titan(name='Atlas')),
            ('subject_monster', make_monster(name='Typhon')),
        )
        for field, entity in entities:
            ProphecySubject.objects.create(prophecy=self.prophecy, **{field: entity})
        self.assertEqual(self.prophecy.subject_records.count(), 4)

    def test_subject_requires_exactly_one_entity(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            ProphecySubject.objects.create(prophecy=self.prophecy)

    def test_subject_rejects_multiple_entity_types(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            ProphecySubject.objects.create(
                prophecy=self.prophecy,
                subject_character=make_character(),
                subject_god=make_god(),
            )

    def test_books_relevant_to_can_span_multiple_books_without_quest_link(self):
        books = [
            make_book(title=f'PJO Book {number}', book_number=number) for number in range(1, 6)
        ]
        self.prophecy.books_relevant_to.add(*books)

        self.assertEqual(
            set(self.prophecy.books_relevant_to.values_list('slug', flat=True)),
            {book.slug for book in books},
        )
        self.assertFalse(Quest.objects.filter(prophecy=self.prophecy).exists())


class QuestModelTests(TestCase):
    def setUp(self):
        self.book = make_book(title='The Lightning Thief', book_number=1)
        self.leader = make_character(name='Percy Jackson')
        self.quest = make_quest(
            title="Quest for Zeus's Lightning Bolt",
            book=self.book,
            led_by=self.leader,
        )

    def test_str(self):
        self.assertEqual(str(self.quest), "Quest for Zeus's Lightning Bolt")

    def test_slug_generated_from_title(self):
        self.assertIn('quest-for-zeus', self.quest.slug)

    def test_participants_m2m(self):
        annabeth = make_character(name='Annabeth Chase')
        self.quest.participants.add(annabeth)
        self.assertIn(annabeth, self.quest.participants.all())

    def test_typed_participants_support_all_entity_types_and_keep_character_m2m(self):
        character = make_character(name='Annabeth Chase')
        god = make_god(name='Apollo')
        titan = make_titan(name='Atlas')
        monster = make_monster(name='Typhon')
        for field, entity in (
            ('participant_character', character),
            ('participant_god', god),
            ('participant_titan', titan),
            ('participant_monster', monster),
        ):
            QuestParticipant.objects.create(quest=self.quest, **{field: entity})

        self.assertEqual(self.quest.participant_records.count(), 4)
        self.assertIn(character, self.quest.participants.all())

    def test_participant_requires_exactly_one_entity(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            QuestParticipant.objects.create(quest=self.quest)

    def test_participant_rejects_multiple_entity_types(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            QuestParticipant.objects.create(
                quest=self.quest,
                participant_character=make_character(),
                participant_god=make_god(),
            )

    def test_typed_casualties_support_all_entity_types(self):
        entities = (
            ('casualty_character', make_character(name='Annabeth Chase')),
            ('casualty_god', make_god(name='Apollo')),
            ('casualty_titan', make_titan(name='Atlas')),
            ('casualty_monster', make_monster(name='Typhon')),
        )
        for field, entity in entities:
            QuestCasualty.objects.create(quest=self.quest, **{field: entity})

        self.assertEqual(self.quest.casualty_records.count(), 4)
        self.assertIn(entities[0][1], self.quest.casualties.all())

    def test_casualty_requires_exactly_one_entity(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            QuestCasualty.objects.create(quest=self.quest)

    def test_casualty_rejects_multiple_entity_types(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            QuestCasualty.objects.create(
                quest=self.quest,
                casualty_character=make_character(),
                casualty_monster=make_monster(),
            )

    def test_prophecy_onetoone(self):
        prophecy = make_prophecy(title='Lightning Bolt Prophecy')
        self.quest.prophecy = prophecy
        self.quest.save()
        self.assertEqual(self.quest.prophecy, prophecy)

    def test_prophecy_cannot_be_linked_to_multiple_quests(self):
        prophecy = make_prophecy(title='Lightning Bolt Prophecy')
        self.quest.prophecy = prophecy
        self.quest.save()

        with self.assertRaises(IntegrityError), transaction.atomic():
            make_quest(title='Second Quest', prophecy=prophecy)


class EventModelTests(TestCase):
    def setUp(self):
        self.book = make_book(title='The Last Olympian', book_number=5)
        self.event = make_event(
            name='Battle of Manhattan',
            event_type='battle',
            book=self.book,
        )

    def test_str(self):
        self.assertEqual(str(self.event), 'Battle of Manhattan')

    def test_slug_generated(self):
        self.assertEqual(self.event.slug, 'battle-of-manhattan')

    def test_participant_characters_m2m(self):
        character = make_character(name='Percy Jackson')
        self.event.participant_characters.add(character)
        self.assertIn(character, self.event.participant_characters.all())

    def test_participant_gods_m2m(self):
        from tests.makers import make_god

        god = make_god(name='Poseidon')
        self.event.participant_gods.add(god)
        self.assertIn(god, self.event.participant_gods.all())

    def test_typed_casualties_support_all_entity_types_and_preserve_character_m2m(self):
        entities = (
            ('casualty_character', make_character(name='Percy Jackson')),
            ('casualty_god', make_god(name='Ares')),
            ('casualty_titan', make_titan(name='Atlas')),
            ('casualty_monster', make_monster(name='Kampe')),
        )
        for field, entity in entities:
            EventCasualty.objects.create(event=self.event, **{field: entity})

        self.assertEqual(self.event.casualty_records.count(), 4)
        self.assertIn(entities[0][1], self.event.casualties.all())

    def test_casualty_requires_exactly_one_entity(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            EventCasualty.objects.create(event=self.event)

    def test_casualty_rejects_multiple_entity_types(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            EventCasualty.objects.create(
                event=self.event,
                casualty_character=make_character(),
                casualty_monster=make_monster(),
            )
