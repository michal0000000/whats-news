from django.db.models.signals import post_save
from django.dispatch import receiver
from newsapp.models import Category,Source
from newsapp.utils import update_category_config, update_source_config

from logger.logger import log
from logger.logger_sink import LoggerSink

import traceback

@receiver(post_save, sender=Category)
def update_category_signal(sender, instance, **kwargs):
    """ Changes config file values whenever a category setting gets changes during runtime """
    
    result = update_category_config(instance)
    if not result:
        log(f"ERR: Couldn't write change to category {instance.title}: \n" + str(traceback.print_exc()),LoggerSink.SOURCES)
        
@receiver(post_save, sender=Source)
def update_source_signal(sender, instance, **kwargs):
    """ Changes config file values whenever a source setting gets changes during runtime """
    """ Note: It IS NOT possible to change the sources category this way """
    
    result = update_source_config(instance)
    if not result:
        log(f"ERR: Couldn't write change to source {instance.name}: \n" + str(traceback.print_exc()),LoggerSink.SOURCES)
