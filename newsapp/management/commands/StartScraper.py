from django.core.management.base import BaseCommand

from newsapp.scraper import WhatsNewsScraper

class Command(BaseCommand):
    
    def handle(self, *args, **options):
        scraper = WhatsNewsScraper()
        scraper.start_scraper()
