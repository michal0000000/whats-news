from datetime import datetime,timedelta
import pytz
import re
import traceback
import configparser
import os

from newsapp.models import Article
from newsapp.models import Category
from newsapp.models import Source

from django.conf import settings

def update_category_config(new_category):
    
    try:
        config = configparser.ConfigParser()
        config['category-settings'] = {
            'display_title': new_category.display_title,
            'active': new_category.active,
            'order': new_category.order
        }
        
        category_path = os.path.join('categories',new_category.title)
        
        with open(os.path.join(category_path,'category.conf'),'w') as configfile:
            config.write(configfile)

        return True
    except Exception as e:
        return False

def update_source_config(new_source):
    try:
        config = configparser.ConfigParser()
        config['source'] = {
            'name': new_source.name,
            'display_name': new_source.display_name,
            'scraping_link': new_source.scraping_link,
            'active' : new_source.active,
            'pfp' : new_source.pfp
        }
        
        category_path = os.path.join('categories',new_source.category.title)
        sources_path = os.path.join(category_path,'sources')
        
        with open(os.path.join(sources_path,new_source.name+'.nws'),'w') as configfile:
            config.write(configfile)

        return True
    except Exception as e:
        return False

def create_new_source(source_name,val,category_object):
    
    return Source(
        name = source_name,
        display_name = val['display_name'],
        scraping_link = val['scraping_link'],
        active = val['active'],
        category = category_object,
        pfp = val['icon'] if val.get('icon') != None else None
    )

def sync_categories(category_obj,category_dict): 
    """ Synchronizes categories and returns True if all went well """
    
    try: 
        if category_obj.title != category_dict['title'] or \
            category_obj.display_title != category_dict['display_title'] or \
            category_obj.active != category_dict['active'] or \
            category_obj.order != category_dict['order']:
                
            category_obj.title = category_dict['title']
            category_obj.display_title = category_dict['display_title']
            category_obj.active = category_dict['active']
            category_obj.order = category_dict['order']
            
            category_obj.save()
        return True
        
    except:
        return False

def sync_source(source_obj,source_dict,category_object):
    """ Synchronizes sources and returns True if all went well """
      
    try: 
        if source_obj.name != source_dict['name'] or \
            source_obj.display_name != source_dict['display_name'] or \
            source_obj.scraping_link != source_dict['scraping_link'] or \
            source_obj.active != source_dict['active'] or \
            source_obj.category.title != category_object.title or \
            source_obj.pfp != source_dict['icon']:
                
            source_obj.name = source_dict['name']
            source_obj.display_name = source_dict['display_name']
            source_obj.scraping_link = source_dict['scraping_link']
            source_obj.active = source_dict['active']
            source_obj.category = category_object
            source_obj.pfp = source_dict['icon']
            
            source_obj.save()
        return True
        
    except:
        return False

def format_member_preference(member_preference):
    """ Prepares memebr preference for front end display """

    # Handle each preference
    result = []

    for pref in member_preference:

        # Format 'checked' html input attrib
        checked = 'checked' if pref.display_in_feed else ''
        
        # Format source pic source
        src_pfp = 'http://' + settings.ALLOWED_HOSTS[0] + ':8000/' + pref.sources.pfp
    
        # Check if source is globally active
        if pref.sources.active == True:
            result.append((
                pref.id,
                pref.sources.display_name,
                src_pfp,
                pref.sources.category.display_title,
                checked
            ))
                
    return result

def get_category_data_for_menu_display(current,unbiased):
    """ Fetches active categories in formatted way """
    categories = Category.objects.filter(active=True).order_by('order')
    result = []
    for cat in categories:
        result.append({
            'display_name' : cat.display_title,
            'url' : cat.title,
            'unbiased' : unbiased,
            'current' : True if current == cat.title else False
        })   
    return result

def prepare_article_data_for_feed(articles):
    # Fetch feed-specific data for each article
    articles_feed_data = []
    for article in articles:
        
        # Get article data from db
        single_article_data = article.get_feed_data()
        
        # Get names of authors
        authors = []
        for author in single_article_data['authors']:
           authors.append(str(author))
           
        # TODO: Properly handle tags
        tags = []
        for tag in single_article_data['tags']:
            tags.append(str(tag))
        single_article_data['tags'] = tags
        
        # Get author count
        author_count = len(authors)
        
        # Create authors string
        authors_string = ''
        if author_count > 2:
            
            # Add names of first two authors
            authors_string = ', '.join(authors[:2])
            
            # Append count of the rest of authors
            authors_string += f' +{ author_count - 2 }'
        
        # If there are only 2 authors
        else:
            
            # Join them with a semicolin
            authors_string = ', '.join(authors)
            
        # Replace authors list from DB with string
        single_article_data['authors'] = authors_string
        
        # Format date
        single_article_data['published'] = single_article_data['published'] \
            .replace(tzinfo=pytz.timezone('Europe/Bratislava'))
            
        # Create abbreviation for recent articles
        abbreviation = ''
        if single_article_data['published'].date() == datetime.now().date():
            abbreviation = 'dnes'
        elif single_article_data['published'].date() == datetime.now().date() - timedelta(days = 1):
            abbreviation = 'včera'
            
        # If article is up to two days old, make it shorter
        result_published = ''
        if abbreviation != '':
            time_published = datetime.strftime(
                single_article_data['published'],
                '%H:%M'
            )
            result_published = abbreviation + ' o ' + time_published
        # If article is older than two days
        else:
            result_published = datetime.strftime(
                single_article_data['published'],
                '%d.%m.%Y o %H:%M'
            )
            
        # Assign formatted pub date
        single_article_data['published'] = result_published
        
        # Append processed data to final list 
        articles_feed_data.append(single_article_data)
        
        # Reverse articles to get correct order in feed
        articles_feed_data.reverse()
        
    return articles_feed_data

def validate_email(email):
    """ Checks if string is a valid email address """
    if email == None:
        return False
    pat = '^[a-zA-Z0-9-_]+@[a-zA-Z0-9]+\.[a-z]{1,3}$'
    validation_result = True if re.match(pat,email) else False
    return validation_result