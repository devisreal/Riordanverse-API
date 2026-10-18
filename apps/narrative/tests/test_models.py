from django.test import TestCase

from tests.factories import (
    make_book,
    make_character,
    make_event,
    make_prophecy,
    make_quest,
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

    def test_prophecy_onetoone(self):
        prophecy = make_prophecy(title='Lightning Bolt Prophecy')
        self.quest.prophecy = prophecy
        self.quest.save()
        self.assertEqual(self.quest.prophecy, prophecy)


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
        from tests.factories import make_god

        god = make_god(name='Poseidon')
        self.event.participant_gods.add(god)
        self.assertIn(god, self.event.participant_gods.all())
