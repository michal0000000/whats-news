import os
import configparser

from logger.logger import log
from logger.logger_sink import LoggerSink

from newsapp.models import Category,Source

import newsapp.scraping_functions as sfs
from newsapp.utils import sync_source

class SourceHandler():
    
    def __init__(self) -> None:
        
        # Signalizes handles is ready to work
        self._ready = False
        self.sfs = sfs.get_functions()
        self.sources = self.refresh_sources()
        
        self._ready = True

    def refresh_sources(self, categories=None):
        """ Refreshes categories to memory and to database, can also be used for a specific category """
        
        # Lock thread
        self._ready = False
        
        # Check if categories are list or None
        if type(categories) != list or categories != None:
            return {}
        
        category_dict = {}
        config = configparser.ConfigParser(allow_no_value=True)
        
        # Refresh all categories if none are specified
        if categories == None:
            categories = os.listdir('categories/')
        
        # Iterate over all folders in "categories/" directory
        for category in categories:
            
            # Check if category exists in filesystem
            try:
                category_path = os.path.join('categories', category)
                log(f"ERR: No category named {category}.",LoggerSink.SOURCES)
            except:
                continue
            
            if os.path.isdir(category_path) and os.path.isdir(os.path.join(category_path, 'sources')):
                
                # Create a dictionary entry with the folder name as key
                category_dict[category] = {}
                
                # Check if category is properly configured and active
                try:
                    if os.path.exists(os.path.join(category_path, 'category.conf')):
                        
                        # Parse the category config file
                        config.read(os.path.join(category_path, 'category.conf'))
                        for key, value in config.items('source-settings'):
                            category_dict[category][key] = value
                        
                            
                        # Try to fetch category, if error add it to database
                        try:
                            does_cat_exist = Category.objects.get(title=category)
                            
                            # Check if category is active
                            if does_cat_exist.active == False:
                                
                                #
                                # Config files are the highet authority, DB should always mirror the configs
                                # therefore, change to inactive in neccessary
                                if does_cat_exist.active == True:
                                    does_cat_exist.active = False
                                    does_cat_exist.save()
                                
                                continue
                        
                        except:
                            
                            # Add category to database
                            install_cat = Category(
                                title = category,
                                display_title = category_dict[category]['display_title'],
                                active = True
                            )
                            install_cat.save()
                            log(f"INFO: Added new category to DB - {category}.",LoggerSink.SOURCES)
                        
                        # Break if category inactive
                        if bool(category_dict[category]['active']) == False:
                            continue
                        
                    else:
                        del category_dict[category]
                        continue
                except Exception as e:
                    log(f'WARN: Category "{category}" not properly configured: {e}',LoggerSink.SOURCES)
                
                # Iterate over each ".nws" file in the category folder
                category_dict[category]['sources'] = {}
                for source_file in os.listdir(os.path.join(category_path, 'sources')):    
                    try:
                    
                        if source_file.endswith('.nws'):
                            
                            # Parse the ".nws" file as a config file
                            config = configparser.ConfigParser()
                            config.read(os.path.join(category_path, 'sources', source_file))
                            
                            # Store the parsed config data in the dictionary
                            source_name = source_file.replace('.nws','')
                            category_dict[category]['sources'][source_name] = {}
                            source = category_dict[category]['sources'][source_name]
                            for key, value in config.items('source'):
                                source[key] = value
                            source['last_seen'] = None
                            source['source_name'] = None
                            
                            if self.sfs.get(source_name):
                                source['scrape'] = self.sfs[source_name]
                            else:
                                log(f"ERR: Scrape function couldn't be loaded for {source_name}.",LoggerSink.SOURCES)
                                del category_dict[category]
                                continue
                            
                            # Try to fetch source, if error add it to database
                            try:
                                does_src_exist = Source.objects.get(title=source_name)
                                
                                # Check if source in DB matches config
                                if sync_source(does_src_exist,source) == False or \
                                    does_src_exist.active == False:
                                    del category_dict[category]['sources'][source_name]
                                    continue
                            except:
                                val = category_dict[category]['sources'][source_name]
                                new_source = Source(
                                    name=source_name,
                                    display_name=val['display_name'],
                                    scraping_link = val['link'],
                                    active = val['active'],
                                    category = val['category'],
                                    pfp= val['icon'] if val.get('icon') != None else None
                                )
                                new_source.save()
                                log(f"INFO: Added new source to DB - {key}.",LoggerSink.SOURCES)
                        
                    except Exception as e:
                        try:
                            del category_dict[category]['sources'][source_name]
                        except:
                            pass
                        log(f'WARN: Source "{source_file}" in category "{category}" not properly configured: {e}',LoggerSink.SOURCES)
        
        # Unlock and return
        self._ready = True
        return category_dict
             
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