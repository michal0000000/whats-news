"""news URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path

from . import views

urlpatterns = [
    path('', views.news),
    path('new_posts/',views.fetch_new_articles),
    path('submit_new_func/',views.submit_new_func),
    path('vote_for_new_func/',views.vote_for_new_func),
    path('account_settings/',views.account_settings),
    
    path('login/',views.login),
    path('register/',views.register),
    path('logout/',views.logout),
    
    path('insert_posts/',views.insert_dummy_articles),
]

