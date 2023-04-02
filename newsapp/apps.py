from django.apps import AppConfig

class NewsappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'newsapp'
    
    def ready(self) -> None:
        import newsapp.signals
        return super().ready()