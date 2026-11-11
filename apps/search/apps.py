from django.apps import AppConfig


class SearchConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.search'

    def ready(self):
        from apps.search.adapters import register_all

        register_all()
