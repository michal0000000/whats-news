
import traceback
from bs4 import BeautifulSoup
import requests
import datetime
import pytz
import re

from .logger.logger import log
from .logger.logger_sink import LoggerSink

from newsapp.models import LastScrape

# TODO
"""
- implement heartbeat for each source
    - heartbeat function will also add Sources to DB if theyre new
    - "Source" model gets fetched from DB on class init
        the model dictates wether each source should be scraped or not
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
        'source' : <source_signature>,   # e.g. 'SME'
        'authors' : ['Ben Dover', 'Moe Lester'],
    }
"""

class SourceHandler():
    
    def __init__(self) -> None:
        
        self.sources = {
            'PRAVDA' : {
                'link': 'https://spravy.pravda.sk/',
                'scrape' : self.get_front_page_links_from_pravda,
                'active': None}, # Determined by heartbeat function
            
            'SME' : {
                'link': 'https://www.sme.sk/najnovsie?f=bez-sportu/', 
                'scrape' : self.get_front_page_links_from_sme,
                'active': None}, # Determined by heartbeat function
            
            'DENNIKN' : {
                'link': 'https://dennikn.sk/najnovsie/',
                'scrape' : self.get_front_page_links_from_dennikn,
                'active': None}, # Determined by heartbeat function
        }

    def get_front_page_links_from_sme(self):
        """Gets all links from front page."""
        
        # Mandatory variables
        source_signature = 'SME'
        source_link = self.sources[source_signature]['link']
        
        # Get last scrape time
        """
        try:
            last_scrape = LastScrape.objects.get(name=source_signature)
        except Exception as e:
            
            # If source is new, add it to database
            new_source = LastScrape(name=source_signature,link=SOURCES[source_signature]['link'])
            new_source.save()
            last_scrape = new_source.last_scrape
        """

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
                    
                    # Append new article to list
                    posts.append({
                        'headline' : headline,
                        'headline_img' : image,
                        'subtitle' : subtitle,
                        'link' : url,
                        'published' : pub_date,
                        'source' : source_signature,
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
            
            return posts
        
        # Mandatory except handler
        except Exception as e:
            log(f"{source_signature} - Failed fetching, reason: {e}",LoggerSink.SOURCES)
            log(f"{traceback.print_exc()}",LoggerSink.SOURCES)
            return False

    def get_front_page_links_from_dennikn(self):
        
        # Mandatory variables
        source_signature = 'DENNIKN'
        source_link = self.sources[source_signature]['link']

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
                    
                    # Append new article to list
                    posts.append({'published':pub_date,'link':url, 'headline':headline,'source':source_signature})
                    
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
            
            return posts
        
        # Mandatory except handler
        except Exception as e:
            log(f"{source_signature} - Failed fetching, reason: {e}",LoggerSink.SOURCES)
            log(f"{traceback.print_exc()}",LoggerSink.SOURCES)
            return False

    def get_front_page_links_from_pravda(self):
        
        # Mandatory variables
        source_signature = 'PRAVDA'
        source_link = self.sources[source_signature]['link']

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
                    
                    # Append new article to list
                    posts.append({'published':pub_date,'link':url, 'headline':headline,'source':source_signature})
                    
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
            
            return posts
        
        # Mandatory except handler
        except Exception as e:
            log(f"{source_signature} - Failed fetching, reason: {e}",LoggerSink.SOURCES)
            log(f"{traceback.print_exc()}",LoggerSink.SOURCES)
            return False
        
    def verify_domain(self, url, unsupported_domains):
        # Compile the regular expression
        pattern = re.compile(r"^(?:https?:\/\/)?(?:[^@\n]+@)?([^:\/\n]+)")

        # Search for the domain in the URL
        match = pattern.search(url)

        # Get the domain from the match object
        domain = match.group(1)

        # Filter out unwanted domains
        found = False
        for dom in unsupported_domains:
            if domain == dom:
                return None

        return url