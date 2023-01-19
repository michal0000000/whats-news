from django.contrib import admin

from newsapp.models import MembershipToken
from newsapp.models import Article
from newsapp.models import Source
from newsapp.models import Tag
from newsapp.models import UpcomingFeatures

class UpcomingFeaturesAdminDisplay(admin.ModelAdmin):
    list_display = ('id','title','submitted','visible')
    list_editable = ('visible',)
    
class SourceAdminDisplay(admin.ModelAdmin):
    list_display = ('display_name','scraping_link')
    
class ArticleAdminDisplay(admin.ModelAdmin):
    list_display = ('headline','source','added')
    
class MembershipTokenAdminDisplay(admin.ModelAdmin):
    list_display = ('id','username','valid_until','last_visit')

admin.site.register(MembershipToken,MembershipTokenAdminDisplay)
admin.site.register(Article,ArticleAdminDisplay)
admin.site.register(Source,SourceAdminDisplay)
admin.site.register(Tag)
admin.site.register(UpcomingFeatures,UpcomingFeaturesAdminDisplay)