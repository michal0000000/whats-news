from bs4 import BeautifulSoup
import requests
import re
import datetime

SME = 'https://www.sme.sk/najnovsie?f=bez-sportu'
DENNIKN = 'https://dennikn.sk/najnovsie'

"""
TODO:
- scrape with proxy rotation
- threading: https://docs.python.org/3/library/threading.html
"""

""" GET LINKS FROM _____ """


def get_new_links_from_sme():

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
        url = div.find('a', {'class': 'media-image'})['href']
        posts.append(url)

    return posts


def get_new_links_from_dennikn():

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


def scrape_articles_from_sme_links(url):

    # Define source
    article_source = 'sme.sk'
    article_source_url = url
    article_img_is_video = False

    # Define accepted domains
    accepted_domains = ['domov.sme.sk']

    # Check if domain is correct
    url = verify_domain(url, accepted_domains)

    # Return "None" if unsupported url
    if url == None:
        return None

    # Fetch html of article
    response = requests.get(url)
    html = response.text

    # Parse the HTML with Beautiful Soup
    soup = BeautifulSoup(html)

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

    # Find subtitle
    article_subtitle = soup.find('p', {'class': 'perex'}).text

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
        'author': article_authors,
        'source_url': article_source_url,
        'published': article_published,
        'paywall': article_paywall,
        'img_is_video': article_img_is_video
    }
    return result


""" UTIL FUNCTIONS """


def verify_domain(url, accepted_domains):
    # Compile the regular expression
    pattern = re.compile(r"^(?:https?:\/\/)?(?:[^@\n]+@)?([^:\/\n]+)")

    # Search for the domain in the URL
    match = pattern.search(url)

    # Get the domain from the match object
    domain = match.group(1)

    # Filter out unwanted domains
    found = False
    for dom in accepted_domains:
        if domain == dom:
            found = True
    if found == False:
        return None

    return url
