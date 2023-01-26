
import traceback
from bs4 import BeautifulSoup
import requests
import datetime
import pytz
import re
import urllib.parse
import xmltodict

from .logger.logger import log
from .logger.logger_sink import LoggerSink

from newsapp.models import Source

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
"""

"""TODO:
- sources failing on some elements
"""

class SlovakNewsSourceHandler():
    
    def __init__(self) -> None:
        
        # Signalizes handles is ready to work
        self._ready = False
        
        self.sources = {
            'PRAVDA' : {
                'link': 'https://spravy.pravda.sk/rss/xml/',
                'scrape' : self.get_front_page_links_from_pravda,
                'last_seen': None, # <Datetime object> - gets updated each time a successful scrape happens
                'display_name' : 'Dennik Pravda',
                'active' : True},
            
            'SME' : {
                'link': 'https://www.sme.sk/najnovsie?f=bez-sportu', 
                'scrape' : self.get_front_page_links_from_sme,
                'last_seen': None, # <Datetime object> - gets updated each time a successful scrape happens
                'display_name' : 'Dennik SME',
                'active' : True},
            
            'DENNIKN' : {
                'link': 'https://dennikn.sk/najnovsie/',
                'scrape' : self.get_front_page_links_from_dennikn,
                'last_seen': None, # <Datetime object> - gets updated each time a successful scrape happens
                'display_name' : 'DennikN',
                'active' : True},
            
            'AKTUALITY' : {
                'link': 'https://www.aktuality.sk/spravy/',
                'scrape' : self.get_front_page_links_from_aktuality,
                'last_seen': None, # <Datetime object> - gets updated each time a successful scrape happens
                'display_name' : 'Aktuality',
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
                        active = val['active']
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
            html = response.text

            # Parse the HTML with Beautiful Soup
            soup = BeautifulSoup(html, 'html.parser')

            # Find all child divs with articles
            child_divs = soup.find_all('li', {'class': 'article-list-item'})

            # Get urls of new posts
            posts = []
            suc = 0
            failed = 0
            
            for div in child_divs:
                
                # Skip mobile ad
                if 'justify-content-center' in div['class']:
                    continue
                
                # Mandatory try functionality
                try:
                    # Find date in post and extract it by removing author info
                    date_str = div.find('span', {'class': 'item-time'}).text
                    date_str = date_str.split(' | ')[0] # Select only day and time
                    date_str = date_str.split(' ') # ['dnes','18:22']
                        
                    # Convert date to datetime object
                    pub_date = datetime.datetime.now().replace(tzinfo=pytz.timezone('Europe/Bratislava'))
                        
                    # If post was published yesterdat
                    if date_str[0].lower() == 'včera':
                        pub_date = pub_date - + datetime.timedelta(days=1)
                    
                    # Add time to date
                    pub_time = date_str[1].split(":")
                    pub_date = pub_date.replace(hour=int(pub_time[0]), minute=int(pub_time[1]))
                    
                    # Find url
                    url = div.find('a', {'class': 'item-link'})['href']
                    
                    # Find headline
                    headline = div.find('a', {'class': 'item-link'}).text
                    
                    # Find and process article image
                    image = div.find('img',{'class': 'image'})
                    image = image['data-src']
                    image = urllib.parse.unquote(image)
                    
                    # Find author (doesnt display)
                    authors = ["Aktuality"]
                    
                    # Append post only if its new
                    if last_seen == None or pub_date > last_seen:
                    
                        # Append new article to list
                        posts.append({
                            'headline' : headline.strip(),
                            'headline_img' : image,
                            'subtitle' : '', # Doesnt display
                            'link' : url,
                            'published' : pub_date,
                            'source' : self.sources[source_signature]['source'],
                            'authors' : authors,
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
                log(f"{source_signature} - Failed scraping {failed}/{failed+suc}, reason: {traceback.print_exc()}",LoggerSink.SOURCES)
            
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
            html = response.text

            # Parse the HTML with Beautiful Soup
            soup = BeautifulSoup(html, 'html.parser')

            # Find the parent div
            parent_div = soup.find('div', {'class': 'my-m'})

            # Find all child divs with articles
            child_divs = parent_div.find_all('div', {'class': 'media'})

            # Get urls of new posts
            posts = []
            suc = 0
            failed = 0
            
            for div in child_divs:
                
                # Mandatory try functionality
                try:
                    # Find date in post and extract it by removing author info
                    date_str = div.find('small', {'class': 'media-bottom'}).text
                    author_str = div.find('address',{'class':'media-author'}).text
                    extracted_date = date_str.replace(author_str,'').strip()
                    
                    # Convert date to datetime object
                    pub_date = datetime.datetime.strptime(extracted_date, '%d. %b %Y, o %H:%M')
                    pub_date = pub_date.replace(tzinfo=pytz.timezone('Europe/Bratislava'))
                    
                    # Find url
                    url = div.find('a', {'class': 'media-image'})['href']
                    
                    # Find headline
                    headline = div.find('a', {'class': 'js-pvt-title'}).text
                    
                    # Find article image
                    image = div.find('a',{'class': 'media-image'})
                    image = image.find('img')['data-src']
                    
                    # Find subtitle
                    subtitle = div.find('p',{'class':'js-pvt-perex'}).text
                    
                    # Find author
                    authors = [author_str.split('a')[0].strip()]
                    
                    # Append post only if its new
                    if last_seen == None or pub_date > last_seen:
                    
                        # Append new article to list
                        posts.append({
                            'headline' : headline,
                            'headline_img' : image,
                            'subtitle' : subtitle,
                            'link' : url,
                            'published' : pub_date,
                            'source' : self.sources[source_signature]['source'],
                            'authors' : authors,
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
            
            html = response.text

            # Parse the HTML with Beautiful Soup
            soup = BeautifulSoup(html, 'html.parser')

            # Find the parent div
            parent_div = soup.find('div', {'class': 'tiles'})

            # Find all child divs with articles
            child_divs = parent_div.find_all('article')

            # Get urls of new posts
            posts = []
            suc = 0
            failed = 0
            for div in child_divs:
                
                # Mandatory try functionality
                try:
                    # Find date in post and extract it by removing author info
                    extracted_date = div.find('time', {'class': 'tile_meta__posted'})['datetime']
                    
                    # Convert date to datetime object
                    pub_date = datetime.datetime.strptime(extracted_date,"%Y-%m-%dT%H:%M:%S%z") #2023-01-01T16:53:14+01:00
                    
                    # Find url
                    url = div.find('h3', {'class': 'tile_title'})
                    url = url.findChildren("a" , recursive=False)[0]['href']
                    
                    # Find headline
                    headline = div.find('h3', {'class': 'tile_title'})
                    headline = headline.findChildren('a' , recursive=False)[0]
                    headline = headline.findChildren('span' , recursive=False)[0].text
                    
                    # Find image
                    image = div.find('img')['src']
                    image = image.split("&w=")[0] + "&w=600"
                    
                    # Find subtitle (doesnt have one)
                    subtitle = ""
                    
                    # Find authors
                    authors = [div.find('cite',{'class':'tile_meta__author'}).find('a').text]
                    
                    # Append post only if its new
                    if last_seen == None or pub_date > last_seen:
                    
                        # Append new article to list
                        posts.append({
                            'headline' : headline,
                            'headline_img' : image,
                            'subtitle' : subtitle,
                            'link' : url,
                            'published' : pub_date,
                            'source' : self.sources[source_signature]['source'],
                            'authors' : authors,
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
            parent_div = xmltodict.parse(response.content)

            # Find all child divs with articles
            child_divs = parent_div['rss']['channel']['item']

            # Get urls of new posts
            posts = []
            suc = 0
            failed = 0
            for i in child_divs:
                
                # Mandatory try functionality
                try:
 
                    article_headline = i['title']
                    article_subtitle = i['description']
                    article_url = i['link']
                    print("HERE1")
                    print(i['pubDate'])
                    
                    # THIS DOESNT WORK
                    date = i['pubDate'].replace(":"," ").replace("-",' ')
                    article_publish_date = datetime.datetime.strptime("2023-01-26T06:05:00+01:00","%Y %m %dT%H %M% %S%z")
                    
                    print("HERE2")
                    article_authors = i['author'].split(',')
                    article_image = i['enclosure']['@url']
                    
                    print(article_publish_date)
                    
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
                