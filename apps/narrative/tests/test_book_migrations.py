from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class BookNarratorMigrationTests(TransactionTestCase):
    migrate_from = ('narrative', '0009_bookantagonist_alter_book_antagonists_and_more')
    migrate_to = ('narrative', '0010_booknarrator_book_narrators_and_more')
    characters_migrate_from = ('characters', '0006_power_wiki_url')
    migration_targets_from = (migrate_from, characters_migrate_from)
    migration_targets_to = (migrate_to, characters_migrate_from)

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def test_migration_copies_legacy_narrator_to_typed_character_link(self):
        executor = MigrationExecutor(connection)
        executor.migrate(self.migration_targets_from)
        old_apps = executor.loader.project_state(self.migration_targets_from).apps
        OldBook = old_apps.get_model('narrative', 'Book')
        OldCharacter = old_apps.get_model('characters', 'Character')

        character = OldCharacter.objects.create(name='Legacy Narrator')
        book = OldBook.objects.create(
            title='Legacy Narrator Book',
            series='companion',
            book_number=1,
            narrator=character,
        )

        executor = MigrationExecutor(connection)
        executor.migrate(self.migration_targets_to)
        new_apps = executor.loader.project_state(self.migration_targets_to).apps
        BookNarrator = new_apps.get_model('narrative', 'BookNarrator')

        self.assertTrue(
            BookNarrator.objects.filter(
                book_id=book.pk,
                character_id=character.pk,
            ).exists()
        )

    def test_typed_narrator_constraints_are_created(self):
        executor = MigrationExecutor(connection)
        executor.migrate(self.migration_targets_to)
        apps = executor.loader.project_state(self.migration_targets_to).apps
        BookNarrator = apps.get_model('narrative', 'BookNarrator')
        Book = apps.get_model('narrative', 'Book')
        book = Book.objects.create(
            title='Narrator Constraint Book', series='companion', book_number=1
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            BookNarrator.objects.create(book=book)


class BookTypedCastMigrationTests(TransactionTestCase):
    migrate_from = ('narrative', '0008_eventcasualty_alter_event_casualties_and_more')
    migrate_to = ('narrative', '0009_bookantagonist_alter_book_antagonists_and_more')
    characters_migrate_from = ('characters', '0006_power_wiki_url')
    migration_targets_from = (migrate_from, characters_migrate_from)
    migration_targets_to = (migrate_to, characters_migrate_from)

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def test_migration_preserves_existing_character_m2m_links(self):
        executor = MigrationExecutor(connection)
        executor.migrate(self.migration_targets_from)
        old_apps = executor.loader.project_state(self.migration_targets_from).apps
        OldBook = old_apps.get_model('narrative', 'Book')
        OldCharacter = old_apps.get_model('characters', 'Character')

        book = OldBook.objects.create(
            title='Legacy Book',
            series='companion',
            book_number=1,
        )
        character = OldCharacter.objects.create(name='Legacy Percy')
        book.main_characters.add(character)
        book.antagonists.add(character)

        executor = MigrationExecutor(connection)
        executor.migrate(self.migration_targets_to)
        new_apps = executor.loader.project_state(self.migration_targets_to).apps
        BookMainCharacter = new_apps.get_model('narrative', 'BookMainCharacter')
        BookAntagonist = new_apps.get_model('narrative', 'BookAntagonist')

        self.assertTrue(
            BookMainCharacter.objects.filter(
                book_id=book.pk,
                character_id=character.pk,
            ).exists()
        )
        self.assertTrue(
            BookAntagonist.objects.filter(
                book_id=book.pk,
                character_id=character.pk,
            ).exists()
        )
