
import traceback
from bs4 import BeautifulSoup
import requests
import datetime
import pytz
import re

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

class SourceHandler():
    
    def __init__(self) -> None:
        
        self.sources = {
            'PRAVDA' : {
                'link': 'https://spravy.pravda.sk/',
                'scrape' : self.get_front_page_links_from_pravda,
                'last_seen': None, # <Datetime object> - gets updated each time a successful scrape happens
                'display_name' : 'Dennik Pravda',
                'active' : True},
            
            'SME' : {
                'link': 'https://www.sme.sk/najnovsie?f=bez-sportu/', 
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
        }
        
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
                    log(f"Adding new source to DB - {key}.",LoggerSink.SOURCES)
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
                    log(f"Error adding new source {key}:",LoggerSink.SOURCES)
                    log(f"{traceback.print_exc()}",LoggerSink.SOURCES)
        
        log(f"All sources initiated.",LoggerSink.SOURCES)

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
                    image = image.find('img')['src']
                    
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
                log(f"{source_signature} - Failed scraping {failed}/{failed+suc}, reason: {traceback.print_exc()}",LoggerSink.SOURCES)
            
            #
            # Mandatory handling of result
            #
            
            # If scraping of all articles failed, indicating scraping error
            if failed+suc == failed:
                return []
            
            # If at least some went through, meaning scraping is working
            self.sources[source_signature]['last_seen'] = datetime.datetime.now()
            return posts
        
        # Mandatory except handler
        except Exception as e:
            log(f"{source_signature} - Failed fetching, reason: {e}",LoggerSink.SOURCES)
            log(f"{traceback.print_exc()}",LoggerSink.SOURCES)
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
                    image = div.find('figure', {'class':'title_figure'}).find('img')['src']
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
            self.sources[source_signature]['last_seen'] = datetime.datetime.now()
            return posts
        
        # Mandatory except handler
        except Exception as e:
            log(f"{source_signature} - Failed fetching, reason: {e}",LoggerSink.SOURCES)
            log(f"{traceback.print_exc()}",LoggerSink.SOURCES)
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
            
            html = response.text

            # Parse the HTML with Beautiful Soup
            soup = BeautifulSoup(html, 'html.parser')

            # Find the parent div
            parent_div = soup.find('section', {'id': 'box-rubrika-clanky-listing'})

            # Find all child divs with articles
            child_divs = parent_div.find_all('div',{'class':'article-listing'})

            # Get urls of new posts
            posts = []
            suc = 0
            failed = 0
            for div in child_divs:
                
                # Mandatory try functionality
                try:
                    # Find date in post and extract it by removing author info
                    extracted_date = div.find('span', {'class': 'article-added-info-date'}).text
                    extracted_date = extracted_date.split(', aktualiz')[0]
                    
                    # Convert date to datetime object
                    extracted_date = extracted_date + '+10:00'
                    pub_date = datetime.datetime.strptime(extracted_date,"%d.%m.%Y %H:%M%z") #"%Y-%m-%dT%H:%M:%S%z"
                    
                    # Find url
                    single_article = div.find('h3')
                    url = single_article.findChildren("a" , recursive=False)[0]['href']
                    url = self.sources[source_signature]['link'] + url
                    
                    # Find headline
                    headline = single_article.findChildren('a' , recursive=False)[0].text
                    
                    # Find image
                    image = div.find('img')['src']
                    
                    # Find subtitle
                    subtitle = div.find('p').text
                    
                    # Find authors
                    authors = ["Pravda"] # They dont publish authors on first page
                    
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
                log(f"{source_signature} - Failed scraping {failed}/{failed+suc}, reason: {traceback.print_exc()}", LoggerSink.SOURCES)
            
            #
            # Mandatory handling of result
            #
            
            # If scraping of all articles failed, indicating scraping error
            if failed+suc == failed:
                return []
            
            # If at least some went through, meaning scraping is working
            self.sources[source_signature]['last_seen'] = datetime.datetime.now()
            return posts
        
        # Mandatory except handler
        except Exception as e:
            log(f"{source_signature} - Failed fetching, reason: {e}",LoggerSink.SOURCES)
            log(f"{traceback.print_exc()}",LoggerSink.SOURCES)
            return []
    
    def get_new_articles(self):
        
        # Generate articles source by source
        for source,info in self.sources.items():
            if info['active'] == True:
                yield info['scrape']()
                