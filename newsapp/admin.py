from django.contrib import admin

from newsapp.models import MembershipToken
from newsapp.models import Article
from newsapp.models import Source
from newsapp.models import Tag

admin.site.register(MembershipToken)
admin.site.register(Article)
admin.site.register(Source)
admin.site.register(Tag)