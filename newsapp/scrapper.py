from bs4 import BeautifulSoup
import requests

"""
SME: https://www.sme.sk/najnovsie
DENNIKN: https://dennikn.sk/najnovsie
ZEMAVEK: https://zemavek.sk/najnovsie-spravy 
"""

"""
TODO:
- scrape with proxy rotation
"""

def get_new_links_from_sme():
    
    # Send a request to the website and retrieve the HTML
    url = 'https://www.sme.sk/najnovsie'
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
        url = div.find('a', {'class' : 'media-image'})['href']
        posts.append(url)
        
    return posts

def get_new_links_from_dennikn():
    
    # Send a request to the website and retrieve the HTML
    url = 'https://dennikn.sk/najnovsie'
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

def get_new_links_from_zemavek():
    
    # Send a request to the website and retrieve the HTML
    url = 'https://zemavek.sk/najnovsie-spravy'
    headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'}
    response = requests.get(url,allow_redirects=True)
    html = response.text

    # Parse the HTML with Beautiful Soup
    soup = BeautifulSoup(html, 'html.parser')
    
    print(soup)

    # Find the parent div
    parent_div = soup.find('div', {'class': 'kt_archivecontent'})

    # Find all child divs with articles
    child_divs = soup.find_all('article', {'class': 'postclass'})
    
    print(child_divs)
    
    # Get urls of new posts
    posts = []
    for div in child_divs:
        url = div.find('a')['href']
        posts.append(url)
        
    return posts