from django.urls import reverse

from apps.core.tests.base import BaseAPITestCase
from apps.narrative.models import EventCasualty, QuestCasualty, QuestParticipant
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


class ProphecyViewTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.prophecy = make_prophecy(
            title='The Great Prophecy',
            text='A half-blood of the eldest gods\nShall reach sixteen against all odds',
        )

    def test_list_returns_200(self):
        response = self.client.get(reverse('prophecy-list'))
        self.assertEqual(response.status_code, 200)

    def test_list_returns_data_envelope(self):
        response = self.client.get(reverse('prophecy-list'))
        self.assertIn('data', response.data)

    def test_detail_returns_200(self):
        response = self.client.get(
            reverse('prophecy-detail', kwargs={'slug': 'the-great-prophecy'})
        )
        self.assertEqual(response.status_code, 200)

    def test_detail_returns_404_for_unknown(self):
        response = self.client.get(reverse('prophecy-detail', kwargs={'slug': 'no-such-prophecy'}))
        self.assertEqual(response.status_code, 404)

    def test_detail_returns_prophecy_lines(self):
        response = self.client.get(
            reverse('prophecy-detail', kwargs={'slug': 'the-great-prophecy'})
        )
        self.assertIn('prophecy_lines', response.data)
        self.assertIsInstance(response.data['prophecy_lines'], list)
        self.assertEqual(len(response.data['prophecy_lines']), 2)

    def test_detail_returns_raw_text(self):
        response = self.client.get(
            reverse('prophecy-detail', kwargs={'slug': 'the-great-prophecy'})
        )
        self.assertIn('text', response.data)
        self.assertIn('\n', response.data['text'])

    def test_detail_includes_typed_subjects(self):
        god = make_god(name='Ares')
        titan = make_titan(name='Atlas')
        self.prophecy.subject_records.create(subject_god=god)
        self.prophecy.subject_records.create(subject_titan=titan)

        response = self.client.get(reverse('prophecy-detail', kwargs={'slug': self.prophecy.slug}))

        self.assertEqual(
            response.data['subjects'],
            [
                {'type': 'god', 'slug': 'ares', 'name': 'Ares'},
                {'type': 'titan', 'slug': 'atlas', 'name': 'Atlas'},
            ],
        )

    def test_filter_by_character_subject(self):
        character = make_character(name='Percy Jackson')
        self.prophecy.subject.add(character)
        response = self.client.get(reverse('prophecy-list'), {'subject': 'percy-jackson'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']), 1)

    def test_filter_by_god_subject(self):
        god = make_god(name='Ares')
        self.prophecy.subject_records.create(subject_god=god)
        response = self.client.get(reverse('prophecy-list'), {'subject_god': 'ares'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']), 1)

    def test_filter_by_titan_subject(self):
        titan = make_titan(name='Atlas')
        self.prophecy.subject_records.create(subject_titan=titan)
        response = self.client.get(reverse('prophecy-list'), {'subject_titan': 'atlas'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']), 1)

    def test_filter_by_monster_subject(self):
        monster = make_monster(name='Typhon')
        self.prophecy.subject_records.create(subject_monster=monster)
        response = self.client.get(reverse('prophecy-list'), {'subject_monster': 'typhon'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']), 1)


class QuestViewTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.book = make_book(title='The Lightning Thief', book_number=1)
        self.leader = make_character(name='Percy Jackson')
        self.quest = make_quest(
            title="Quest for Zeus's Lightning Bolt",
            book=self.book,
            led_by=self.leader,
        )

    def test_list_returns_200(self):
        response = self.client.get(reverse('quest-list'))
        self.assertEqual(response.status_code, 200)

    def test_detail_returns_200(self):
        response = self.client.get(reverse('quest-detail', kwargs={'slug': self.quest.slug}))
        self.assertEqual(response.status_code, 200)

    def test_detail_returns_404_for_unknown(self):
        response = self.client.get(reverse('quest-detail', kwargs={'slug': 'no-such-quest'}))
        self.assertEqual(response.status_code, 404)

    def test_filter_by_book(self):
        response = self.client.get(reverse('quest-list'), {'book': 'the-lightning-thief'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']), 1)

    def test_filter_by_led_by(self):
        response = self.client.get(reverse('quest-list'), {'led_by': 'percy-jackson'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']), 1)

    def test_detail_returns_typed_participant_and_casualty_payloads(self):
        apollo = make_god(name='Apollo')
        minotaur = make_monster(name='Minotaur')
        QuestParticipant.objects.create(quest=self.quest, participant_god=apollo)
        QuestCasualty.objects.create(quest=self.quest, casualty_monster=minotaur)

        response = self.client.get(reverse('quest-detail', kwargs={'slug': self.quest.slug}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['participants'][0]['type'], 'god')
        self.assertEqual(response.data['participants'][0]['slug'], 'apollo')
        self.assertEqual(response.data['casualties'][0]['type'], 'monster')
        self.assertEqual(response.data['casualties'][0]['slug'], 'minotaur')

    def test_filter_by_typed_god_participant(self):
        QuestParticipant.objects.create(quest=self.quest, participant_god=make_god(name='Apollo'))
        response = self.client.get(reverse('quest-list'), {'participant_god': 'apollo'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']), 1)

    def test_filter_by_typed_monster_casualty(self):
        QuestCasualty.objects.create(
            quest=self.quest, casualty_monster=make_monster(name='Minotaur')
        )
        response = self.client.get(reverse('quest-list'), {'casualty_monster': 'minotaur'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']), 1)

    def test_participants_sub_resource(self):
        annabeth = make_character(name='Annabeth Chase')
        self.quest.participants.add(annabeth)
        response = self.client.get(
            reverse('quest-participant-list', kwargs={'slug': self.quest.slug})
        )
        self.assertEqual(response.status_code, 200)
        slugs = [c['slug'] for c in response.data['data']]
        self.assertIn('annabeth-chase', slugs)


class EventViewTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.book = make_book(title='The Last Olympian', book_number=5)
        self.event = make_event(
            name='Battle of Manhattan',
            event_type='battle',
            book=self.book,
        )

    def test_list_returns_200(self):
        response = self.client.get(reverse('event-list'))
        self.assertEqual(response.status_code, 200)

    def test_detail_returns_200(self):
        response = self.client.get(reverse('event-detail', kwargs={'slug': 'battle-of-manhattan'}))
        self.assertEqual(response.status_code, 200)

    def test_detail_returns_typed_casualties_and_legacy_slugs(self):
        kampe = make_monster(name='Kampe')
        EventCasualty.objects.create(event=self.event, casualty_monster=kampe)

        response = self.client.get(reverse('event-detail', kwargs={'slug': self.event.slug}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data['casualties'],
            [{'type': 'monster', 'slug': 'kampe', 'name': 'Kampe'}],
        )
        self.assertEqual(response.data['casualty_slugs'], [])

    def test_filter_by_monster_casualty(self):
        EventCasualty.objects.create(event=self.event, casualty_monster=make_monster(name='Kampe'))
        response = self.client.get(reverse('event-list'), {'casualty_monster': 'kampe'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']), 1)

    def test_filter_by_event_type(self):
        response = self.client.get(reverse('event-list'), {'event_type': 'battle'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']), 1)

    def test_invalid_event_type_returns_400(self):
        response = self.client.get(reverse('event-list'), {'event_type': 'not-a-type'})
        self.assertEqual(response.status_code, 400)

    def test_filter_by_book(self):
        response = self.client.get(reverse('event-list'), {'book': 'the-last-olympian'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']), 1)


class BookSubResourceViewTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.book = make_book(title='The Lightning Thief', book_number=1)
        self.character = make_character(name='Percy Jackson')
        self.character.books_appeared_in.add(self.book)

    def test_book_characters_returns_200(self):
        response = self.client.get(reverse('book-character-list', kwargs={'slug': self.book.slug}))
        self.assertEqual(response.status_code, 200)

    def test_book_characters_contains_character(self):
        response = self.client.get(reverse('book-character-list', kwargs={'slug': self.book.slug}))
        slugs = [c['slug'] for c in response.data['data']]
        self.assertIn('percy-jackson', slugs)

    def test_book_quests_returns_200(self):
        make_quest(title='Test Quest', book=self.book)
        response = self.client.get(reverse('book-quest-list', kwargs={'slug': self.book.slug}))
        self.assertEqual(response.status_code, 200)

    def test_book_monsters_returns_200(self):
        response = self.client.get(reverse('book-monster-list', kwargs={'slug': self.book.slug}))
        self.assertEqual(response.status_code, 200)

    def test_book_locations_returns_200(self):
        response = self.client.get(reverse('book-location-list', kwargs={'slug': self.book.slug}))
        self.assertEqual(response.status_code, 200)
