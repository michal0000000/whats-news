from bs4 import BeautifulSoup
from threading import Thread

import requests
import re
import datetime
import time
import pytz

from logger.logger import log
from logger.logger_sink import LoggerSink

from newsapp.models import Article
from newsapp.models import Author
from newsapp.models import Source

from .source_handler import SourceHandler

DEBUG = True
DEBUG_SLEEP = 5

LOGGING = False

"""
TODO:
- adding and extracting Tags from Articles
- make last_scrape functionality inside scrape_new_links_and_add_to_queue() better
 
- scrape with proxy rotation
- proper starting and terminating of threads
"""

""" SCRAPER CLASS """
class WhatsNewsScraper():
    
    def __init__(self):   
        self.queue_filler_running = False
        self.article_extrator_running = False
        self.__running = False
        self.__new_article_queue = []

        
    # Override run() method
    def start_scraper(self):
        
        # Drop all articles if in debug mode
        if DEBUG == True:
            Article.objects.all().delete()
            print('DEBUG: All articles deleted')
            log("connected: ",LoggerSink.DEBUG)
        
        # Change state of scraper
        self.__running = True
        
        # Scrape front page links and add the new one to the queue
        queue_filler = Thread(target=self.scrape_new_links_and_add_to_queue)
        queue_filler.start()
        self.queue_filler_running = True
        
        # Start adding new articles to database
        article_extractor = Thread(target=self.scrape_articles_from_queue)
        article_extractor.start()
        self.article_extrator_running = True
        
        print("Scraper sucessfully started.\n")
        
    def stop_scraper(self,sig,frame):
        
        print("Waiting for processes to terminate...")
        print("This may take a few minutes.")
        
        # Change state of scraper to initiate stopping of processes
        self.__running = False
        
        # Wait for processes to finish running
        while self.queue_filler_running == True or self.article_extrator_running == True:
            time.sleep(5)
        
        print("Scraper sucessfully stopped.")
        
    def scrape_new_links_and_add_to_queue(self):
        
        # Dont fetch latest article if debug mode is enabled
        if DEBUG == False:
            #last_scrape = Article.objects.latest('published').published
            last_scrape = datetime.datetime.now() - datetime.timedelta(hours = 1)
        else:
            last_scrape = datetime.datetime.now() - datetime.timedelta(days = 300)
            
        # Make last_scrape timezone aware    
        last_scrape = last_scrape.replace(tzinfo=pytz.timezone('Europe/Bratislava'))
        
        # Spawn SourceHandler
        source_handler = SourceHandler()
        
        # Wait for handler to be ready
        while source_handler._ready == False:
            time.sleep(5)
        
        # While scraper hasn't been stopped
        while self.__running == True:
            
            for source in source_handler.get_new_articles():
                
                # Append new articles to queue
                self.__new_article_queue += source
            
            # Wait x mins before checking new articles
            print('Waiting before checking new articles.')
            if DEBUG == False:
                    time.sleep(120)
            else:
                time.sleep(DEBUG_SLEEP)
            
        # Change state of queue_filler process
        self.queue_filler_running = False
        
        # Signal successfull function stop when self.__running changes to False
        return True

    def scrape_articles_from_queue(self):
        
        while self.__running == True:
            
            # Get oldest article in queue
            article_data = self.get_article_from_queue()
            
             # If queue is empty, wait 2 mins and try again
            if article_data == None:        
                print('No new articles, sleeping...')
                
                # Wait x amount of time depending of debug mode
                if DEBUG == False:
                    time.sleep(120)
                else:
                    time.sleep(DEBUG_SLEEP)
                    
                # Poll for articles again
                continue
            
            # If article was succesfully extracted
            if article_data != False and article_data != None:
                
                # Handle Authors
                author_objects = []
                for author in article_data['authors']:
                    try:
                        # Check if author exists in DB
                        single_author = Author.objects.get(name=author)
                        
                        # Append found author
                        author_objects.append(single_author)
                        
                    except Exception as e:
                        
                        # If author doesnt exist, add him to DB
                        single_author = Author(name=author)
                        
                        # Save new author do DB
                        single_author.save()
                        
                        # Append created author
                        author_objects.append(single_author)
                                
                # Create new Article object
                article_object = Article(
                    headline = article_data['headline'],
                    subtitle = article_data['subtitle'],
                    link = article_data['link'],
                    published = article_data['published'],
                    source = article_data['source']
                )
                
                # If article has headline image
                if article_data.get('headline_img') != None:
                    article_object.headline_img = article_data['headline_img']
                
                # Save new article to database
                article_object.save()
                
                # Add authors to article
                for author in author_objects:
                    article_object.authors.add(author)
                
                # Print progress into terminal
                headline = article_object.headline
                print(f'{article_data["source"].name} - Article "{headline[:int(len(headline)/3)]}..." addeed to DB!')
                
                # Remove article from queue
                del self.__new_article_queue[0]
                
        # Change state of article_extractor
        self.article_extrator_running = False
            
        # Signal successfull function stop when self.__running changes to False
        return True
    
    def get_article_from_queue(self):
        
        try:
            
            # Return oldest article in queue
            return self.__new_article_queue[0]
        except:
            
            # If queue is empty
            return None

scraper = WhatsNewsScraper()
scraper.start_scraper() 