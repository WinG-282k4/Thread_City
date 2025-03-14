from django.apps import AppConfig


class ThreadConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Thread'

    def ready(self):
        import Thread.signals  # Import file signals.py để kích hoạt signal