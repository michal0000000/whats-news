from bs4 import BeautifulSoup
from threading import Thread

import requests
import re
import datetime
import time
import signal

from newsapp.models import Article
from newsapp.models import Author
from newsapp.models import Source

DEBUG = True

SME = 'https://www.sme.sk/najnovsie?f=bez-sportu'
DENNIKN = 'https://dennikn.sk/najnovsie'

"""
TODO:
- implement logging
- scrape with proxy rotation
- adding and extracting Tags from Articles
- Source adding and handling
- platform recognition in scrape_articles_from_queue()
- create script that runs on startups that checks if needed classes have changed on news websites
- proper starting and terminating of threads
- make sure articles are printed in correct order
"""

""" SCRAPER CLASS """
class WhatsNewsScraper():
    
    def __init__(self):   
        self.queue_filler_running = False
        self.article_extrator_running = False
        self.__running = False
        self.__new_article_queue = []
        
        #signal.signal(signal.SIGINT,self.stop_scraper)
        
    # Override run() method
    def start_scraper(self):
        
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
            last_scrape = Article.objects.latest('published').published
        else:
            last_scrape = datetime.datetime.now() - datetime.timedelta(days = 300)
        
        # While scraper hasn't been stopped
        while self.__running == True:
            
            # Get new links from one publisher
            links = self.get_front_page_links_from_sme()
            
            # Filter out only new articles
            for link in links:
                if link['published'] > last_scrape:
                    
                    # Append new link to queue
                    self.__new_article_queue.append(link)
                    
                    # Change last scrape time
                    last_scrape = link['published']
            
            # Wait x mins before checking new articles
            print('Waiting before checking new articles.')
            if DEBUG == False:
                    time.sleep(120)
            else:
                time.sleep(3)
            
        # Change state of queue_filler process
        self.queue_filler_running = False
        
        # Signal successfull function stop when self.__running changes to False
        return True

    def scrape_articles_from_queue(self):
        
        while self.__running == True:
            
            # Get oldest article in queue
            print('Fetching article from queue.')
            article_link = self.get_article_from_queue()
            
             # If queue is empty, wait 2 mins and try again
            if article_link == None:        
                print('No new articles, sleeping...')
                
                # Wait x amount of time depending of debug mode
                if DEBUG == False:
                    time.sleep(120)
                else:
                    time.sleep(3)
                    
                # Poll for articles again
                continue
            
            # Scrape article data
            # TODO -> add platform recognition for multiple platform support
            print(article_link['url'])
            article_data = self.scrape_article_from_sme_links(article_link['url'])
            
            # If article was succesfully extracted
            if article_data != False:
                
                # Handle Source
                try:
                    source = Source.objects.get(name='sme.sk')
                except:
                    source = None
                    print('No such Source found. Adding None as Source.')
                
                
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
                
                # Handle Article
                article_object = Article(
                    headline = article_data['headline'],
                    headline_img = article_data['image'],
                    excerpt = article_data['excerpt'], 
                    subtitle = article_data['subtitle'],
                    content = article_data['content'],
                    source = None,
                    link = article_data['link'],
                    published = article_data['published'],
                    paywall = article_data['paywall'],
                    img_is_video = article_data['img_is_video']
                )
                print(str(article_object))
                
                # Save new article to database
                article_object.save()
                
                # Add authors to article
                for author in author_objects:
                    article_object.authors.add(author)
                
                # Print progress into terminal
                headline = article_object.headline
                print(f'Article "{headline[:int(len(headline)/3)]}..." addeed to DB!')
                
                # Remove article from queue
                self.__new_article_queue.remove(article_link)
                
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

    """ GET LINKS FROM _____ """

    def get_front_page_links_from_sme(self):
        """Gets all links from front page."""

        # Send a request to the website and retrieve the HTML
        url = SME
        response = requests.get(url)
        html = response.text

        # Parse the HTML with Beautiful Soup
        soup = BeautifulSoup(html, 'html.parser')

        # Find the parent div
        parent_div = soup.find('div', {'class': 'my-m'})

        # Find all child divs with articles
        child_divs = parent_div.find_all('div', {'class': 'media'})

        # Get urls of new posts
        posts = []
        for div in child_divs:
            
            # Find date in post and extract it by removing author info
            date_str = div.find('small', {'class': 'media-bottom'}).text
            author_str = div.find('address',{'class':'media-author'}).text
            extracted_date = date_str.replace(author_str,'').strip()
            
            # Convert date to datetime object
            pub_date = datetime.datetime.strptime(extracted_date, '%d. %b %Y, o %H:%M')
            url = div.find('a', {'class': 'media-image'})['href']
            
            # Append new article to list
            posts.append({'published':pub_date,'url':url})

        # Reverse order of links to start with oldest
        posts.reverse()

        return posts

    def get_new_links_from_dennikn(self):

        # Send a request to the website and retrieve the HTML
        url = DENNIKN
        response = requests.get(url)
        html = response.text

        # Parse the HTML with Beautiful Soup
        soup = BeautifulSoup(html, 'html.parser')

        # Find the parent div
        parent_div = soup.find('div', {'class': 'tiles'})

        # Find all child divs with articles
        child_divs = parent_div.find_all('article', {'class': 'tile'})

        # Get urls of new posts
        posts = []
        for div in child_divs:
            url = div.find('a')['href']
            posts.append(url)

        return posts

    """ SCRAPE ARTICLES FROM _____ """

    def scrape_article_from_sme_links(self,url):
        
        try:
            # Define source
            article_source = 'sme.sk'
            article_link = url
            article_img_is_video = False

            # Define unsupported domains
            unsupported_domains = ['sportnet.sme.sk']

            # Check if domain is supported
            url = self.verify_domain(url, unsupported_domains)

            # Return "None" if unsupported url
            if url == None:
                return None

            # Fetch html of article
            response = requests.get(url)
            html = response.text

            # Parse the HTML with Beautiful Soup
            soup = BeautifulSoup(html,features='lxml')

            # Find div containing article
            article = soup.find('div', {'class': 'left-panel'})

            # Find article title
            article_title = soup.find('h1').text

            # Find article image
            article_image = None
            try:
                article_image = soup.find(
                    'div', {'class': 'article-main-img'}).find('img')['src']
            except:
                pass
            try:
                article_image = soup.find(
                    'div', {'class': 'wideform-perex-photo'}).find('img')['src']
            except:
                pass

            # Check if article image is a video
            if article_image == None:
                try:
                    article_image = soup.find_all('iframe')[0]
                    article_image['style'] = 'width:300px; height:200px'
                    article_img_is_video = True
                except:
                    pass

            # Find article rubric
            article_rubtic = soup.find('h1')['data-article-rubric']

            # Find article publish date
            article_published = soup.find('h1')['data-publish-date']
            article_published = datetime.datetime.strptime(article_published, '%Y%m%d')

            # Find authors
            article_authors = []
            author_data = soup.find('div', {'class': 'pr-m'}).find_all('a')
            for author in author_data:
                article_authors.append(author.text)

            # Get article data
            article_data = soup.find('article').find_all('p')

            # Return None if content wasn't found
            if len(article_data) < 3:
                return None

            # Find article content
            article_content = ''
            for p in article_data:
                article_content += str(p) + '\n'

            # Create exerpt from first few lines
            article_exerpt = ''
            for i in range(0, 3):
                article_exerpt += str(article_data[i])
                
            # Find subtitle
            try:
                article_subtitle = soup.find('p', {'class': 'perex'}).text
            except:
                article_subtitle = article_exerpt

            # Find paywall
            article_paywall = False
            find_paywall = soup.find_all('div', {'class': 'editorial-promo'})
            if len(find_paywall) > 0:
                article_paywall = True

            # Return None if article is a quiz
            if 'kvíz' in article_content.lower():
                return None

            # Return result
            result = {
                'headline': article_title,
                'image': article_image,
                'excerpt': article_exerpt,
                'subtitle': article_subtitle,
                'content': article_content,
                'source': article_source,
                'authors': article_authors,
                'link': article_link,
                'published': article_published,
                'paywall': article_paywall,
                'img_is_video': article_img_is_video
            }
            return result
        except Exception as e:
            print(e)
            return False

    """ UTIL FUNCTIONS """

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

#scraper = WhatsNewsScraper()
#scraper.start_scraper()