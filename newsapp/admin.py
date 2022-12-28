from django.contrib import admin

from newsapp.models import MembershipToken
from newsapp.models import Article


admin.site.register(MembershipToken)
admin.site.register(Article)