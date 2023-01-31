
import traceback
import requests
import datetime
import pytz
import re
import urllib.parse
import xmltodict
import html
from bs4 import BeautifulSoup

from logger.logger import log
from logger.logger_sink import LoggerSink

from newsapp.models import Source
from newsapp.models import Category

# TODO
"""
- methods for fetching sources that are failing and sources that are up
"""

"""
HOW TO ADD SOURCES:
1. create function within class
2. add function to __init__ function
3. add mandatory variables
4. add mandatory handlers and loggers
"""

"""
SAMPLE ARTICLE DATA:
    {   'headline' : 'Sample Headline',
        'headline_img' : 'https://example.com/link_to_image.jpg',
        'subtitle' : 'Something has happenned and you should know about it!',
        'link' : 'https://example.com/articles/link_to_article',
        'published' : <DateTime object>,
        'source' : <Source DB Object>,
        
        'authors' : ['Ben Dover', 'Moe Lester'], 
        or
        'authors' : ['Aktuality'] # If source doesn't display. simply set Source name as author
    }
"""

"""
OTHER INFO:
- each scraping function returns either data or an empty string (in case of error or no new articles)
- if scraping fails for some reason, 'last_seen' is not updated
- SourceHandler keeps track of last cycle and returns only new articles added after last scrape

- source uptime monitoring happens and is handled in this class, 
    the WhatsNewsScraper class can query this data but should not be expected to handle any errors
- 'active' attribute of each source has two functions:
    1. determines the state of the source in the DB when initially added to db
    2. is a guidline for scraping wether to scrape or not (gets updated from db if source is not new on init)
        - when it comes to using 'active' attribute during development, while coding it can be set to False
          to be added as such to the database, once you swtich it on, you have to control it from the DB
"""

"""TODO:
- sources failing on some elements
"""

class SourceHandler():
    
    def __init__(self) -> None:
        
        # Signalizes handles is ready to work
        self._ready = False
        
        self.sources = {
            
            ### SLOVAKIA ###
            'PRAVDA' : { 
                'link' : 'https://spravy.pravda.sk/rss/xml/',
                'icon' : 'static/images/pravda-logo_20x20.png',
                'scrape' : self.get_front_page_links_from_pravda,
                'last_seen' : None, # <Datetime object> - gets updated each time a successful scrape happens
                'display_name' : 'Dennik Pravda',
                'category' : Category.objects.get(title='sk'),
                'active' : True},
            
            'SME' : {
                'link' : 'https://domov.sme.sk/rss', 
                'icon' : 'static/images/sme-logo_20x20.jpeg',
                'scrape' : self.get_front_page_links_from_sme,
                'last_seen' : None, # <Datetime object> - gets updated each time a successful scrape happens
                'display_name' : 'Dennik SME',
                'category' : Category.objects.get(title='sk'),
                'active' : True},
            
            'DENNIKN' : {
                'link' : 'https://dennikn.sk/slovensko/feed/',
                'icon' : 'static/images/dennikn-logo_20x20.png',
                'scrape' : self.get_front_page_links_from_dennikn,
                'last_seen' : None, # <Datetime object> - gets updated each time a successful scrape happens
                'display_name' : 'DennikN',
                'category' : Category.objects.get(title='sk'),
                'active' : True},
            
            'AKTUALITY' : {
                'link' : 'https://www.aktuality.sk/rss/domace/',
                'icon' : 'static/images/aktuality-logo_20x20.png',
                'scrape' : self.get_front_page_links_from_aktuality,
                'last_seen' : None, # <Datetime object> - gets updated each time a successful scrape happens
                'display_name' : 'Aktuality',
                'category' : Category.objects.get(title='sk'),
                'active' : True},
            
            'TA3' : {
                'link' : 'https://www.ta3.com/rss/5/novinky-z-domova',
                'icon' : 'static/images/ta3-logo_20x20.png',
                'scrape' : self.get_front_page_links_from_ta3,
                'last_seen' : None,
                'display_name' :  'Ta3',
                'category' : Category.objects.get(title='sk'),
                'active' : True},
            
             ### EKONOMIKA ###
            'EURACTIV' : {
                'link' : 'https://euractiv.sk/feed/',
                'icon' : 'static/images/euractiv-logo_20x20.png',
                'scrape' : self.get_front_page_links_from_euractiv,
                'last_seen' : None,
                'display_name' :  'Euractiv',
                'category' : Category.objects.get(title='ekonom'),
                'active' : True},
        
             ### RANDOM ###
            'HACKER-NEWS-NEWEST' : {
                'link' : 'https://hnrss.org/newest',
                'icon' : 'static/images/hacker-news-newest_logo_20x20.png',
                'scrape' : self.get_front_page_links_from_hacker_news,
                'last_seen' : None,
                'display_name' :  'Hacker News',
                'category' : Category.objects.get(title='rand'),
                'active' : True},
            
             ### CYBERSECURITY ###
            'THREAT-POST' : {
                'link' : 'https://threatpost.com/feed/',
                'icon' : 'static/images/threat-post_logo_20x20.png',
                'scrape' : self.get_front_page_links_from_threat_post,
                'last_seen' : None,
                'display_name' :  'Threat Post',
                'category' : Category.objects.get(title='kyber'),
                'active' : True},
            
            'SECURITY-MAGAZINE' : {
                'link' : 'https://www.securitymagazine.com/rss/15',
                'icon' : 'static/images/security-magazine_logo_20x20.png',
                'scrape' : self.get_front_page_links_from_security_magazine,
                'last_seen' : None,
                'display_name' :  'Security Magazine',
                'category' : Category.objects.get(title='kyber'),
                'active' : True},
        
        }
        
        
        """
        The below section takes care of the following:
        1. Verifies if all sources exist in in database
            - if not, they get added and initiated
        2. Checks which sources are active
        
        """
        
        # Verify if all sources exist
        for key,val in self.sources.items():
            try:
                
                # Verify if source exists
                source = Source.objects.get(name=key)
                
                # Change local active status if active values dont match
                if source.active != val['active']:
                    self.sources[key]['active'] = source.active
                    
                # Add source object
                self.sources[key]['source'] = source
                    
            except:
                
                # If source doesnt exist, create new one
                try:
                    log(f"Adding new source to DB - {key}.",LoggerSink.SLOVAK_NEWS_SOURCES)
                    new_source = Source(
                        name=key,
                        display_name=val['display_name'],
                        scraping_link = val['link'],
                        active = val['active'],
                        category = val['category'],
                        pfp= val['icon'] if val.get('icon') != None else None
                    )
                    new_source.save()
                    
                    # Add source object
                    self.sources[key]['source'] = new_source
                    
                # Handle error
                except:
                    self.sources[key]['active'] = False
                    log(f"Error adding new source {key}:",LoggerSink.SLOVAK_NEWS_SOURCES)
                    log(f"{traceback.print_exc()}",LoggerSink.SLOVAK_NEWS_SOURCES)
        
        log(f"All sources initiated.",LoggerSink.SLOVAK_NEWS_SOURCES)
        self._ready = True

    def get_front_page_links_from_aktuality(self):
        """Gets all links from Aktuality.sk front page."""
        
        # Mandatory variables
        source_signature = 'AKTUALITY'
        source_link = self.sources[source_signature]['link']
        last_seen = self.sources[source_signature]['last_seen']

        # Mandatory try handler
        try:
            # Send a request to the website and retrieve the HTML
            response = requests.get(source_link)

            # Find the parent div
            rss_feed = xmltodict.parse(response.content)

            # Find all child divs with articles
            articles = rss_feed['rss']['channel']['item']

            # Get urls of new posts
            posts = []
            suc = 0
            failed = 0
            for i in articles:
                
                # Mandatory try functionality
                try:
 
                    # Handle title, desc and link
                    article_headline = i['title']
                    article_url = i['link']
                    
                    # Handle description
                    article_description = i['description'].split('br/>')[1].strip().replace(']]>','')
                    
                    # Handle pub date
                    date = i['pubDate'].split(', ')[1]
                    date = date.strip()
                    article_publish_date = datetime.datetime.strptime(date,'%d %b %Y %H:%M:%S %z')
                    
                    # Handle Authors
                    article_authors = ['Aktuality']
                    
                    # Handle image
                    article_image = i['image:image']['image:url'].strip()
                    article_image = urllib.parse.unquote(article_image)
                    article_image = article_image.replace('amp;','')
                    
                    # Append post only if its new
                    if last_seen == None or article_publish_date > last_seen:
                    
                        # Append new article to list
                        posts.append({
                            'headline': article_headline,
                            'headline_img': article_image,
                            'subtitle': article_description,
                            'link': article_url,
                            'published': article_publish_date,
                            'authors': article_authors,
                            'source' : self.sources[source_signature]['source'],
                        })
                    
                        suc += 1
                    
                # Mandatory except functionality
                except Exception as e:
                    
                    print(traceback.print_exc())
                    
                    failed += 1
                    
            # Reverse order of links to start with oldest
            posts.reverse()
            
            # Mandatory logger
            # If there are many failed scrapes
            if failed > suc:
                log(f"{source_signature} - Failed scraping {failed}/{failed+suc}, reason: {traceback.print_exc()}", LoggerSink.SLOVAK_NEWS_SOURCES)
            
            #
            # Mandatory handling of result
            #
            
            # If scraping of all articles failed, indicating scraping error
            if failed+suc == failed:
                return []
            
            # If at least some went through, meaning scraping is working
            self.sources[source_signature]['last_seen'] = datetime.datetime.now(tz=pytz.timezone('Europe/Bratislava'))
            return posts
        
        # Mandatory except handler
        except Exception as e:
            log(f"{source_signature} - Failed fetching, reason: {e}",LoggerSink.SLOVAK_NEWS_SOURCES)
            log(f"{traceback.print_exc()}",LoggerSink.SLOVAK_NEWS_SOURCES)
            return []
    
    def get_front_page_links_from_sme(self):
        """Gets all links from front page."""
        
        # Mandatory variables
        source_signature = 'SME'
        source_link = self.sources[source_signature]['link']
        last_seen = self.sources[source_signature]['last_seen']

        # Mandatory try handler
        try:
            # Send a request to the website and retrieve the HTML
            response = requests.get(source_link)

            # Find the parent div
            rss_feed = xmltodict.parse(response.content)

            # Find all child divs with articles
            articles = rss_feed['rss']['channel']['item']

            # Get urls of new posts
            posts = []
            suc = 0
            failed = 0
            for i in articles:
                
                # Mandatory try functionality
                try:
 
                    # Handle title, desc and link
                    article_headline = i['title']
                    article_url = i['link']
                    article_description = i['description']
                    
                    # Handle pub date
                    date = i['pubDate'].split(', ')[1]
                    date = date.strip()
                    article_publish_date = datetime.datetime.strptime(date,'%d %b %Y %H:%M:%S %z')
                    
                    # Handle Authors
                    article_authors = ['Sme']
                    
                    # Handle image
                    article_image = i['enclosure']['@url'].split('?rev')[0]
                    
                    # Append post only if its new
                    if last_seen == None or article_publish_date > last_seen:
                    
                        # Append new article to list
                        posts.append({
                            'headline': article_headline,
                            'headline_img': article_image,
                            'subtitle': article_description,
                            'link': article_url,
                            'published': article_publish_date,
                            'authors': article_authors,
                            'source' : self.sources[source_signature]['source'],
                        })
                    
                        suc += 1
                    
                # Mandatory except functionality
                except Exception as e:
                    failed += 1
                    
            # Reverse order of links to start with oldest
            posts.reverse()
            
            # Mandatory logger
            # If there are many failed scrapes
            if failed > suc:
                log(f"{source_signature} - Failed scraping {failed}/{failed+suc}, reason: {traceback.print_exc()}",LoggerSink.SLOVAK_NEWS_SOURCES)
            
            #
            # Mandatory handling of result
            #
            
            # If scraping of all articles failed, indicating scraping error
            if failed+suc == failed:
                return []
            
            # If at least some went through, meaning scraping is working
            self.sources[source_signature]['last_seen'] = datetime.datetime.now(tz=pytz.timezone('Europe/Bratislava'))
            return posts
        
        # Mandatory except handler
        except Exception as e:
            log(f"{source_signature} - Failed fetching, reason: {e}",LoggerSink.SLOVAK_NEWS_SOURCES)
            log(f"{traceback.print_exc()}",LoggerSink.SLOVAK_NEWS_SOURCES)
            return []

    def get_front_page_links_from_dennikn(self):
        
        # Mandatory variables
        source_signature = 'DENNIKN'
        source_link = self.sources[source_signature]['link']
        last_seen = self.sources[source_signature]['last_seen']

        # Mandatory try handler
        try:
            # Send a request to the website and retrieve the HTML
            response = requests.get(source_link)

            # Find the parent div
            rss_feed = xmltodict.parse(response.content)

            # Find all child divs with articles
            articles = rss_feed['rss']['channel']['item']

            # Get urls of new posts
            posts = []
            suc = 0
            failed = 0
            for i in articles:
                
                # Mandatory try functionality
                try:
 
                    # Handle title, desc and link
                    article_headline = i['title']
                    article_url = i['link']
                    article_description = html.unescape(i['description'])
                    
                    # Handle pub date
                    date = i['pubDate'].split(', ')[1]
                    date = date.strip()
                    article_publish_date = datetime.datetime.strptime(date,'%d %b %Y %H:%M:%S %z')
                    article_publish_date = article_publish_date.replace(tzinfo=pytz.timezone('Europe/Bratislava'))
                    
                    # Handle Authors
                    article_authors = [i['dc:creator']]
                    
                    # Handle image
                    article_image = i['enclosure']['@url'].split('.jpg')[0] + '.jpg'
                    
                    # Append post only if its new
                    if last_seen == None or article_publish_date > last_seen:
                    
                        # Append new article to list
                        posts.append({
                            'headline': article_headline,
                            'headline_img': article_image,
                            'subtitle': article_description,
                            'link': article_url,
                            'published': article_publish_date,
                            'authors': article_authors,
                            'source' : self.sources[source_signature]['source'],
                        })
                    
                        suc += 1
                   
                # Mandatory except functionality 
                except Exception as e:
                    print(e)
                    failed += 1
                    
            # Reverse order of links to start with oldest
            posts.reverse()
            
            # Mandatory logger
            # If there are many failed scrapes
            if failed > suc:
                log(f"{source_signature} - Failed scraping {failed}/{failed+suc}, reason: {traceback.print_exc()}",LoggerSink.SLOVAK_NEWS_SOURCES)
            
            #
            # Mandatory handling of result
            #
            
            # If scraping of all articles failed, indicating scraping error
            if failed+suc == failed:
                return []
            
            # If at least some went through, meaning scraping is working
            self.sources[source_signature]['last_seen'] = datetime.datetime.now(tz=pytz.timezone('Europe/Bratislava'))
            return posts
        
        # Mandatory except handler
        except Exception as e:
            log(f"{source_signature} - Failed fetching, reason: {e}",LoggerSink.SLOVAK_NEWS_SOURCES)
            log(f"{traceback.print_exc()}",LoggerSink.SLOVAK_NEWS_SOURCES)
            return []

    def get_front_page_links_from_pravda(self):
        
        # Mandatory variables
        source_signature = 'PRAVDA'
        source_link = self.sources[source_signature]['link']
        last_seen = self.sources[source_signature]['last_seen']

        # Mandatory try handler
        try:
            # Send a request to the website and retrieve the HTML
            response = requests.get(source_link)

            # Find the parent div
            rss_feed = xmltodict.parse(response.content)

            # Find all child divs with articles
            articles = rss_feed['rss']['channel']['item']

            # Get urls of new posts
            posts = []
            suc = 0
            failed = 0
            for i in articles:
                
                # Mandatory try functionality
                try:
 
                    # Handle title, desc and link
                    article_headline = i['title']
                    article_subtitle = i['description']
                    article_url = i['link']
                    
                    # Handle pub date
                    date = i['pubDate'][:22] + i['pubDate'][-2:]
                    date = date.strip()
                    article_publish_date = datetime.datetime.strptime(date,'%Y-%m-%dT%H:%M:%S%z')
                    
                    # Handle Authors
                    article_authors = i['author'].split(',')
                    article_image = i['enclosure']['@url']
                    
                    # Append post only if its new
                    if last_seen == None or article_publish_date > last_seen:
                    
                        # Append new article to list
                        posts.append({
                            'headline': article_headline,
                            'headline_img': article_image,
                            'subtitle': article_subtitle,
                            'link': article_url,
                            'published': article_publish_date,
                            'authors': article_authors,
                            'source' : self.sources[source_signature]['source'],
                        })
                    
                        suc += 1
                    
                # Mandatory except functionality
                except Exception as e:
                    
                    print(traceback.print_exc())
                    
                    failed += 1
                    
            # Reverse order of links to start with oldest
            posts.reverse()
            
            # Mandatory logger
            # If there are many failed scrapes
            if failed > suc:
                log(f"{source_signature} - Failed scraping {failed}/{failed+suc}, reason: {traceback.print_exc()}", LoggerSink.SLOVAK_NEWS_SOURCES)
            
            #
            # Mandatory handling of result
            #
            
            # If scraping of all articles failed, indicating scraping error
            if failed+suc == failed:
                return []
            
            # If at least some went through, meaning scraping is working
            self.sources[source_signature]['last_seen'] = datetime.datetime.now(tz=pytz.timezone('Europe/Bratislava'))
            return posts
        
        # Mandatory except handler
        except Exception as e:
            log(f"{source_signature} - Failed fetching, reason: {e}",LoggerSink.SLOVAK_NEWS_SOURCES)
            log(f"{traceback.print_exc()}",LoggerSink.SLOVAK_NEWS_SOURCES)
            return []
        
    def get_front_page_links_from_ta3(self):
        
        # Mandatory variables
        source_signature = 'TA3'
        source_link = self.sources[source_signature]['link']
        last_seen = self.sources[source_signature]['last_seen']

        # Mandatory try handler
        try:
            # Send a request to the website and retrieve the HTML
            response = requests.get(source_link)

            # Find the parent div
            rss_feed = xmltodict.parse(response.content)

            # Find all child divs with articles
            articles = rss_feed['rss']['channel']['item']

            # Get urls of new posts
            posts = []
            suc = 0
            failed = 0
            for i in articles:
                
                # Mandatory try functionality
                try:
 
                    # Handle title, desc and link
                    article_headline = i['title']
                    article_subtitle = i['description']
                    article_url = i['link']
                    
                    # Handle pub date
                    date = i['pubDate'].split(', ')[1]
                    date = date.strip()
                    article_publish_date = datetime.datetime.strptime(date,'%d %b %Y %H:%M:%S %z')
                    
                    # Handle Authors
                    article_authors = ['Ta3']
                    
                    # Handle article image
                    #       feed doesnt provide image
                    
                    # Append post only if its new
                    if last_seen == None or article_publish_date > last_seen:
                    
                        # Append new article to list
                        posts.append({
                            'headline': article_headline,
                            'subtitle': article_subtitle,
                            'link': article_url,
                            'published': article_publish_date,
                            'authors': article_authors,
                            'source' : self.sources[source_signature]['source'],
                        })
                    
                        suc += 1
                    
                # Mandatory except functionality
                except Exception as e:
                    
                    print(traceback.print_exc())
                    
                    failed += 1
                    
            # Reverse order of links to start with oldest
            posts.reverse()
            
            # Mandatory logger
            # If there are many failed scrapes
            if failed > suc:
                log(f"{source_signature} - Failed scraping {failed}/{failed+suc}, reason: {traceback.print_exc()}", LoggerSink.SLOVAK_NEWS_SOURCES)
            
            #
            # Mandatory handling of result
            #
            
            # If scraping of all articles failed, indicating scraping error
            if failed+suc == failed:
                return []
            
            # If at least some went through, meaning scraping is working
            self.sources[source_signature]['last_seen'] = datetime.datetime.now(tz=pytz.timezone('Europe/Bratislava'))
            return posts
        
        # Mandatory except handler
        except Exception as e:
            log(f"{source_signature} - Failed fetching, reason: {e}",LoggerSink.SLOVAK_NEWS_SOURCES)
            log(f"{traceback.print_exc()}",LoggerSink.SLOVAK_NEWS_SOURCES)
            return []
    
    def get_front_page_links_from_euractiv(self):
        
        # Mandatory variables
        source_signature = 'EURACTIV'
        source_link = self.sources[source_signature]['link']
        last_seen = self.sources[source_signature]['last_seen']

        # Mandatory try handler
        try:
            # Send a request to the website and retrieve the HTML
            response = requests.get(source_link)

            # Find the parent div
            rss_feed = xmltodict.parse(response.content)

            # Find all child divs with articles
            articles = rss_feed['rss']['channel']['item']

            # Get urls of new posts
            posts = []
            suc = 0
            failed = 0
            for i in articles:
                
                # Mandatory try functionality
                try:
 
                    # Handle title, desc and link
                    article_headline = i['title']
                    article_subtitle = i['description']
                    article_url = i['link']
                    
                    # Handle pub date
                    date = i['pubDate'].split(', ')[1]
                    date = date.strip()
                    article_publish_date = datetime.datetime.strptime(date,'%d %b %Y %H:%M:%S %z')
                    
                    # Handle Authors
                    article_authors = i['dc:creator'].split(', ')
                    
                    # Handle article image
                    article_image = i['media:content']['@url']
                    
                    # Append post only if its new
                    if last_seen == None or article_publish_date > last_seen:
                    
                        # Append new article to list
                        posts.append({
                            'headline': article_headline,
                            'headline_img': article_image,
                            'subtitle': article_subtitle,
                            'link': article_url,
                            'published': article_publish_date,
                            'authors': article_authors,
                            'source' : self.sources[source_signature]['source'],
                        })
                    
                        suc += 1
                    
                # Mandatory except functionality
                except Exception as e:
                    
                    print(traceback.print_exc())
                    
                    failed += 1
                    
            # Reverse order of links to start with oldest
            posts.reverse()
            
            # Mandatory logger
            # If there are many failed scrapes
            if failed > suc:
                log(f"{source_signature} - Failed scraping {failed}/{failed+suc}, reason: {traceback.print_exc()}", LoggerSink.SLOVAK_NEWS_SOURCES)
            
            #
            # Mandatory handling of result
            #
            
            # If scraping of all articles failed, indicating scraping error
            if failed+suc == failed:
                return []
            
            # If at least some went through, meaning scraping is working
            self.sources[source_signature]['last_seen'] = datetime.datetime.now(tz=pytz.timezone('Europe/Bratislava'))
            return posts
        
        # Mandatory except handler
        except Exception as e:
            log(f"{source_signature} - Failed fetching, reason: {e}",LoggerSink.SLOVAK_NEWS_SOURCES)
            log(f"{traceback.print_exc()}",LoggerSink.SLOVAK_NEWS_SOURCES)
            return []
    
    def get_front_page_links_from_hacker_news(self):
        
        # Mandatory variables
        source_signature = 'HACKER-NEWS-NEWEST'
        source_link = self.sources[source_signature]['link']
        last_seen = self.sources[source_signature]['last_seen']

        # Mandatory try handler
        try:
            # Send a request to the website and retrieve the HTML
            response = requests.get(source_link)

            # Find the parent div
            try:
                rss_feed = xmltodict.parse(response.content)
            except:
                log(f"{source_signature} - Failed scraping, reason: {response.content}", LoggerSink.SLOVAK_NEWS_SOURCES)
                return []
            
            # Find all child divs with articles
            articles = rss_feed['rss']['channel']['item']

            # Get urls of new posts
            posts = []
            suc = 0
            failed = 0
            for i in articles:
                
                # Mandatory try functionality
                try:
 
                    # Handle title, desc and link
                    article_headline = i['title']
                    article_subtitle = ''
                    article_url = i['link']
                    
                    # Handle pub date
                    date = i['pubDate'].split(', ')[1]
                    date = date.strip()
                    article_publish_date = datetime.datetime.strptime(date,'%d %b %Y %H:%M:%S %z')
                    article_publish_date = article_publish_date.replace(tzinfo=pytz.timezone('Europe/Bratislava'))
                    
                    # Handle Authors
                    article_authors = i['dc:creator'].split(', ')
                    
                    # Append post only if its new
                    if last_seen == None or article_publish_date > last_seen:
                    
                        # Append new article to list
                        posts.append({
                            'headline': article_headline,
                            'subtitle': article_subtitle,
                            'link': article_url,
                            'published': article_publish_date,
                            'authors': article_authors,
                            'source' : self.sources[source_signature]['source'],
                        })
                    
                        suc += 1
                    
                # Mandatory except functionality
                except Exception as e:
                    
                    print(traceback.print_exc())
                    
                    failed += 1
                    
            # Reverse order of links to start with oldest
            posts.reverse()
            
            # Mandatory logger
            # If there are many failed scrapes
            if failed > suc:
                log(f"{source_signature} - Failed scraping {failed}/{failed+suc}, reason: {traceback.print_exc()}", LoggerSink.SLOVAK_NEWS_SOURCES)
            
            #
            # Mandatory handling of result
            #
            
            # If scraping of all articles failed, indicating scraping error
            if failed+suc == failed:
                return []
            
            # If at least some went through, meaning scraping is working
            self.sources[source_signature]['last_seen'] = datetime.datetime.now(tz=pytz.timezone('Europe/Bratislava'))
            return posts
        
        # Mandatory except handler
        except Exception as e:
            log(f"{source_signature} - Failed fetching, reason: {e}",LoggerSink.SLOVAK_NEWS_SOURCES)
            log(f"{traceback.print_exc()}",LoggerSink.SLOVAK_NEWS_SOURCES)
            return []
    
    def get_front_page_links_from_threat_post(self):
        
        # Mandatory variables
        source_signature = 'THREAT-POST'
        source_link = self.sources[source_signature]['link']
        last_seen = self.sources[source_signature]['last_seen']

        # Mandatory try handler
        try:
            # Send a request to the website and retrieve the HTML
            response = requests.get(source_link)

            # Find the parent div
            rss_feed = xmltodict.parse(response.content)
            
            # Find all child divs with articles
            articles = rss_feed['rss']['channel']['item']

            # Get urls of new posts
            posts = []
            suc = 0
            failed = 0
            for i in articles:
                
                # Mandatory try functionality
                try:
 
                    # Handle title, desc and link
                    article_headline = i['title']
                    article_subtitle = i['description']
                    article_url = i['link']
                    
                    # Handle pub date
                    date = i['pubDate'].split(', ')[1]
                    date = date.strip()
                    article_publish_date = datetime.datetime.strptime(date,'%d %b %Y %H:%M:%S %z')
                    article_publish_date = article_publish_date.replace(tzinfo=pytz.timezone('Europe/Bratislava'))
                    
                    # Handle article image
                    article_headline_img = i['media:content'][3]['@url']
                    
                    # Handle Authors
                    article_authors = i['dc:creator'].split(', ')
                    
                    # Append post only if its new
                    if last_seen == None or article_publish_date > last_seen:
                    
                        # Append new article to list
                        posts.append({
                            'headline': article_headline,
                            'headline_img': article_headline_img,
                            'subtitle': article_subtitle,
                            'link': article_url,
                            'published': article_publish_date,
                            'authors': article_authors,
                            'source' : self.sources[source_signature]['source'],
                        })
                    
                        suc += 1
                    
                # Mandatory except functionality
                except Exception as e:
                    
                    print(traceback.print_exc())
                    
                    failed += 1
                    
            # Reverse order of links to start with oldest
            posts.reverse()
            
            # Mandatory logger
            # If there are many failed scrapes
            if failed > suc:
                log(f"{source_signature} - Failed scraping {failed}/{failed+suc}, reason: {traceback.print_exc()}", LoggerSink.SLOVAK_NEWS_SOURCES)
            
            #
            # Mandatory handling of result
            #
            
            # If scraping of all articles failed, indicating scraping error
            if failed+suc == failed:
                return []
            
            # If at least some went through, meaning scraping is working
            self.sources[source_signature]['last_seen'] = datetime.datetime.now(tz=pytz.timezone('Europe/Bratislava'))
            return posts
        
        # Mandatory except handler
        except Exception as e:
            log(f"{source_signature} - Failed fetching, reason: {e}",LoggerSink.SLOVAK_NEWS_SOURCES)
            log(f"{traceback.print_exc()}",LoggerSink.SLOVAK_NEWS_SOURCES)
            return []
    
    def get_front_page_links_from_security_magazine(self):
        
        # Mandatory variables
        source_signature = 'SECURITY-MAGAZINE'
        source_link = self.sources[source_signature]['link']
        last_seen = self.sources[source_signature]['last_seen']

        # Mandatory try handler
        try:
            # Send a request to the website and retrieve the HTML
            response = requests.get(source_link)

            # Find the parent div
            rss_feed = xmltodict.parse(response.content)
            
            # Find all child divs with articles
            articles = rss_feed['rss']['channel']['item']

            # Get urls of new posts
            posts = []
            suc = 0
            failed = 0
            for i in articles:
                
                # Mandatory try functionality
                try:
 
                    # Handle title, desc and link
                    article_headline = i['title']
                    article_url = i['link']
                    
                    # Handle description
                    subtitle_html = BeautifulSoup(i['description'], 'html.parser')
                    article_subtitle = subtitle_html.find('p').text or ''
                    
                    # Handle pub date
                    date = i['pubDate'].split(', ')[1]
                    date = date.strip()
                    article_publish_date = datetime.datetime.strptime(date,'%d %b %Y %H:%M:%S %z')
                    article_publish_date = article_publish_date.replace(tzinfo=pytz.timezone('Europe/Bratislava'))
                    
                    # Handle Authors
                    try:
                        article_authors = i['author'].split(', ')
                    except:
                        article_authors = ['Security Magazine']
                    
                    # Handle headline image
                    article_image = i['enclosure']['@url']
                    
                    # Append post only if its new
                    if last_seen == None or article_publish_date > last_seen:
                    
                        # Append new article to list
                        posts.append({
                            'headline': article_headline,
                            'headline_img': article_image,
                            'subtitle': article_subtitle,
                            'link': article_url,
                            'published': article_publish_date,
                            'authors': article_authors,
                            'source' : self.sources[source_signature]['source'],
                        })
                    
                        suc += 1
                    
                # Mandatory except functionality
                except Exception as e:
                    
                    print(traceback.print_exc())
                    
                    failed += 1
                    
            # Reverse order of links to start with oldest
            posts.reverse()
            
            # Mandatory logger
            # If there are many failed scrapes
            if failed > suc:
                log(f"{source_signature} - Failed scraping {failed}/{failed+suc}, reason: {traceback.print_exc()}", LoggerSink.SLOVAK_NEWS_SOURCES)
            
            #
            # Mandatory handling of result
            #
            
            # If scraping of all articles failed, indicating scraping error
            if failed+suc == failed:
                return []
            
            # If at least some went through, meaning scraping is working
            self.sources[source_signature]['last_seen'] = datetime.datetime.now(tz=pytz.timezone('Europe/Bratislava'))
            return posts
        
        # Mandatory except handler
        except Exception as e:
            log(f"{source_signature} - Failed fetching, reason: {e}",LoggerSink.SLOVAK_NEWS_SOURCES)
            log(f"{traceback.print_exc()}",LoggerSink.SLOVAK_NEWS_SOURCES)
            return []
    
    def get_new_articles(self):
        """ Generates a list of new articles per platform or returns empty list """
        
        # Checks if handler is ready to work
        if self._ready == True:
        
            # Generate articles source by source
            for source,info in self.sources.items():
                if info['active'] == True:
                    yield info['scrape']()
        else:
            yield []
                