import os
import configparser
import traceback

from django.core.exceptions import MultipleObjectsReturned

from logger.logger import log
from logger.logger_sink import LoggerSink

from newsapp.models import Category,Source

import newsapp.scraping_functions as sfs
from newsapp.utils import sync_source, create_new_source

class SourceHandler():
    
    def __init__(self) -> None:
        
        # Signalizes handles is ready to work
        self._ready = False
        
        all_cats = Source.objects.all()
        for cat in all_cats:
            log(cat.name)
        
        self.sfs = sfs.get_functions()
        self.sources = self.refresh_sources()
        
        log("ready to mingle")
         
        self._ready = True
        
    

    def refresh_sources(self, categories=None):
        """ Refreshes categories to memory and to database, can also be used for a specific category """
        
        # Lock thread
        self._ready = False
        
        # Check if categories are list or None
        if type(categories) == list or categories == None:
            pass
        else:
            return {}
        
        category_dict = {}
        config = configparser.ConfigParser(allow_no_value=True)
        
        # Refresh all categories if none are specified
        if categories == None:
            categories = os.listdir('categories/')
        
        # Iterate over all folders in "categories/" directory
        for category in categories:
            
            # Initialize category DB object for later usage
            category_object = None
            
            # Check if category exists in filesystem
            try:
                category_path = os.path.join('categories', category)
            except:
                log(f"ERR: No category {os.path.join('categories', category)}.",LoggerSink.SOURCES)
                continue
            
            #log(f'{category_path} - {os.path.isdir(category_path)} / {os.path.join(category_path, "sources")} - {os.path.isdir(os.path.join(category_path, "sources"))}')
            
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
                        category_dict[category]['active'] = bool(category_dict[category]['active'])
                        
                            
                        # Try to fetch category, if error add it to database
                        try:
                            does_cat_exist = Category.objects.get(title=category)
                            
                            # Assign for usage during source creation
                            category_object = does_cat_exist
                            
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
                            
                            # Assign for usage during source creation
                            category_object = install_cat
                            
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
                            source['name'] = source_name
                            source['category'] = category
                            source['active'] = bool(source['active'])
                            
                            if self.sfs.get(source_name):
                                source['scrape'] = self.sfs[source_name]
                            else:
                                log(f"ERR: Scrape function couldn't be loaded for {source_name}.",LoggerSink.SOURCES)
                                del category_dict[category]
                                continue
                            
                            # Try to fetch source, if error add it to database
                            try:
                                does_src_exist = Source.objects.get(name=source_name)
                                category_dict[category]['sources'][source_name]['source'] = does_src_exist
                                # Check if source in DB matches config
                                if not sync_source(does_src_exist,source,category_object) or not does_src_exist.active:
                                    del category_dict[category]['sources'][source_name]
                                    continue
                                
                            # If multiple sources get returned delete all of them and create a new one    
                            except MultipleObjectsReturned as e:
                                Source.objects.filter(name=source_name).delete()
                                
                                # Add new version of source to DB
                                val = category_dict[category]['sources'][source_name]
                                new_source = create_new_source(source_name,val,category_object)
                                new_source.save()
                                category_dict[category]['sources'][source_name]['source'] = new_source
                            
                            # If source doesn't exist in DB, create it
                            except:                                
                                val = category_dict[category]['sources'][source_name]
                                new_source = create_new_source(source_name,val,category_object)
                                new_source.save()
                                category_dict[category]['sources'][source_name]['source'] = new_source
                                log(f"INFO: Added new source to DB - {key}.",LoggerSink.SOURCES)
                                log(traceback.print_exc())
                        
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
            for category,data in self.sources.items():
                for source,info in self.sources[category]['sources'].items():
                    if info['active'] == True:
                        
                        result_of_scrape = info['scrape'](info)
                        
                        if result_of_scrape != False:
                            info['last_seen'] = result_of_scrape[0]
                            yield result_of_scrape[1]
        else:
            yield []