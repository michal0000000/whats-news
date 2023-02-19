from django.contrib import admin

from newsapp.models import MembershipToken, MemberPreference
from newsapp.models import Article
from newsapp.models import Source
from newsapp.models import Tag
from newsapp.models import UpcomingFeatures
from newsapp.models import Category

class UpcomingFeaturesAdminDisplay(admin.ModelAdmin):
    list_display = ('id','title','submitted','visible')
    list_editable = ('visible',)
    
class SourceAdminDisplay(admin.ModelAdmin):
    list_display = ('display_name','scraping_link','category','active')
    list_editable = ('active',)
    
class ArticleAdminDisplay(admin.ModelAdmin):
    list_display = ('headline','source','published','added')
    
class MembershipTokenAdminDisplay(admin.ModelAdmin):
    list_display = ('id','username','valid_until','last_visit')
    
class CategoryAdminDisplay(admin.ModelAdmin):
    list_display = ('id','title','display_title','active')
    list_editable = ('active',)

"""
class PreferencesDisplay(admin.ModelAdmin):
    list_display = ('id','title','display_title','active')
"""

admin.site.register(MembershipToken,MembershipTokenAdminDisplay)
admin.site.register(Article,ArticleAdminDisplay)
admin.site.register(Source,SourceAdminDisplay)
admin.site.register(Tag)
admin.site.register(UpcomingFeatures,UpcomingFeaturesAdminDisplay)
admin.site.register(Category,CategoryAdminDisplay)
#admin.site.register(MemberPreference,PreferencesDisplay)