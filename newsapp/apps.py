from django.apps import AppConfig

from django.core.management import call_command
from django.db.models.signals import post_migrate,post_init


# Signal handler that initiates article scraping
def start_web_scraper(sender, **kwargs):
    call_command('StartScraper')

class NewsappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'newsapp'
    
    def ready(self) -> None:
        #return super().ready()
        
        # Connect singal handler to post_migrate singal
        #   ** post_migrate is sent after all migrations have been applied
        post_init.connect(start_web_scraper,sender=self)
