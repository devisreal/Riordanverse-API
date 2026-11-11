from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class BookTypedRelationshipMigrationTests(TransactionTestCase):
    migrate_from = ('narrative', '0008_eventcasualty_alter_event_casualties_and_more')
    cast_migration = ('narrative', '0009_bookantagonist_alter_book_antagonists_and_more')
    narrator_migration = ('narrative', '0010_booknarrator_book_narrators_and_more')
    characters_migration = ('characters', '0006_power_wiki_url')

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def test_migrations_preserve_legacy_cast_narrator_and_create_typed_constraint(self):
        # Walk the consecutive migrations once. Each assertion still uses the
        # historical model state immediately after the migration under test.
        targets = (self.migrate_from, self.characters_migration)
        executor = MigrationExecutor(connection)
        executor.migrate(targets)
        old_apps = executor.loader.project_state(targets).apps
        OldBook = old_apps.get_model('narrative', 'Book')
        OldCharacter = old_apps.get_model('characters', 'Character')

        character = OldCharacter.objects.create(name='Legacy Percy')
        book = OldBook.objects.create(
            title='Legacy Book',
            series='companion',
            book_number=1,
            narrator=character,
        )
        book.main_characters.add(character)
        book.antagonists.add(character)

        targets = (self.cast_migration, self.characters_migration)
        executor = MigrationExecutor(connection)
        executor.migrate(targets)
        cast_apps = executor.loader.project_state(targets).apps
        BookMainCharacter = cast_apps.get_model('narrative', 'BookMainCharacter')
        BookAntagonist = cast_apps.get_model('narrative', 'BookAntagonist')
        with self.subTest(migration='0009', relationship='main_character'):
            self.assertTrue(
                BookMainCharacter.objects.filter(
                    book_id=book.pk,
                    character_id=character.pk,
                ).exists()
            )
        with self.subTest(migration='0009', relationship='antagonist'):
            self.assertTrue(
                BookAntagonist.objects.filter(
                    book_id=book.pk,
                    character_id=character.pk,
                ).exists()
            )

        targets = (self.narrator_migration, self.characters_migration)
        executor = MigrationExecutor(connection)
        executor.migrate(targets)
        narrator_apps = executor.loader.project_state(targets).apps
        BookNarrator = narrator_apps.get_model('narrative', 'BookNarrator')
        with self.subTest(migration='0010', relationship='narrator'):
            self.assertTrue(
                BookNarrator.objects.filter(
                    book_id=book.pk,
                    character_id=character.pk,
                ).exists()
            )
        with (
            self.subTest(migration='0010', constraint='exactly_one_narrator'),
            self.assertRaises(IntegrityError),
            transaction.atomic(),
        ):
            BookNarrator.objects.create(book_id=book.pk)
