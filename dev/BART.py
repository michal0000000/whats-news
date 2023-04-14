from bs4 import BeautifulSoup
import requests
import datetime
import pytz
import traceback

from logger.logger import log, LoggerSink

def get_front_page_links_from_bart(source):
        
    # Mandatory variables
    source_signature = 'BART'
    source_link = source['scraping_link']
    last_seen = source['last_seen']

    # Mandatory try handler
    try:
        # Send a request to the website and retrieve the HTML
        response = requests.get(source_link)

        # Find the parent div
        html_feed = BeautifulSoup(response.content, 'html.parser')
        
        # Find all child divs with articles
        articles = html_feed.find_all('div',class_='post-container')

        # Get urls of new posts
        posts = []
        suc = 0
        failed = 0
        for soup in articles:
            
            # Mandatory try functionality
            try:

                # Handle title, desc and link
                headline_element = soup.find('a', class_='post-title')
                article_headline = headline_element.find('h2').text.strip
                article_url = headline_element['href']
                
                # Handle description
                article_subtitle = soup.find('div', class_='post-content').p.text.strip() or ''
                
                # Handle pub date
                date = soup.find('a', class_='post-meta-date')
                date = date.strip()
                article_publish_date = datetime.datetime.strptime(date,'%d.%m-%Y')
                article_publish_date = article_publish_date.replace(tzinfo=pytz.timezone('Europe/Bratislava'))
                
                # Handle Authors
                article_authors = [soup.find('a', class_='bypostauthor').text.strip()] \
                    or ['bart.sk']
                
                # Handle headline image
                article_image_el = soup.find('img', class_='wp-post-image')
                article_image = None
                for source in article_image.split(', '):
                    if source.endswith('150w'):
                        article_image = source.split(' ')[0]
                        break
                if article_image == None:
                    article_image = article_image_el['src']
                
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
                        'source' : source['source'],
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
            return False
        
        # If at least some went through, meaning scraping is working
        last_seen = datetime.datetime.now(tz=pytz.timezone('Europe/Bratislava'))
        return last_seen,posts
    
    # Mandatory except handler
    except Exception as e:
        log(f"{source_signature} - Failed fetching, reason: {e}",LoggerSink.SOURCES)
        log(f"{traceback.print_exc()}",LoggerSink.SOURCES)
        return False
    
sources = {'TRUBAN' : { 
                'link' : 'https://blog.bart.sk/',
                #'icon' : 'static/images/pravda-logo_20x20.png',
                'scrape' : get_front_page_links_from_bart,
                'last_seen' : None, # <Datetime object> - gets updated each time a successful scrape happens
                'display_name' : 'Dennik Pravda',
                #'category' : Category.objects.get(title='sk'),
                'active' : True},
                'source': 'dummy_data'}

print(sources['TRUBAN']['scrape'](sources['TRUBAN']))