
import traceback
import requests
import datetime
import pytz
import urllib.parse
import xmltodict
import html
from bs4 import BeautifulSoup

from logger.logger import log
from logger.logger_sink import LoggerSink


def get_functions():
    
    scraping_functions = {
        
        ### SLOVAKIA ###
        'PRAVDA' : get_front_page_links_from_pravda,
        'SME' : get_front_page_links_from_sme,
        'DENNIKN' :get_front_page_links_from_dennikn,
        'AKTUALITY' : get_front_page_links_from_aktuality,
        'TA3' : get_front_page_links_from_ta3,
        
        ### EKONOMIKA ###
        'EURACTIV' : get_front_page_links_from_euractiv,
        
        ### RANDOM ###
        'HACKER-NEWS-NEWEST' : get_front_page_links_from_hacker_news,
        
        ### CYBERSECURITY ###
        'THREAT-POST' : get_front_page_links_from_threat_post,
        'SECURITY-MAGAZINE' : get_front_page_links_from_security_magazine,
               
    }
    
    return scraping_functions

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
                article_image = i['image:image']['image:url'].split('.jpg')[0] + '.jpg'
                
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
