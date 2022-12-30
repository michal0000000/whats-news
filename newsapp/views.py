import hashlib
import datetime

from .logger.logger import log
from .logger.logger_sink import LoggerSink

from django.shortcuts import render,redirect
from django.http import HttpResponse, JsonResponse
from django.core import paginator
from django.template.loader import render_to_string

from newsapp.models import MembershipToken
from newsapp.models import Article, Author, Source, Tag

from . import scraper
from . import utils

"""TODO:
- implement new news fetching
- implement pagination
- add nonce for each pagination or new news fetch
- sidebar with upcoming features, user can click to vote
"""

def login(request):
    
    # Code to create first hash
    #expiry = datetime.datetime.now(tz=pytz.UTC) + datetime.timedelta(days=14)
    #hashed = hashlib.sha256('gayfrog'.encode('utf-8')).hexdigest()
    #token = MembershipToken(hashed_token=hashed,username='mike',valid_until=expiry)
    #token.save()
    
    if request.method == 'POST':
        
        # Get token and hash it
        raw_token = request.POST['token']
        hashed_token = hashlib.sha256(raw_token.encode('utf-8')).hexdigest()
        
        # Handle login
        try:
            
            # Get user with matching hash
            user = MembershipToken.objects.get(hashed_token=hashed_token)
            
            # Create session variable with current user
            request.session['user'] = str(user)
            
            # Redirect to news page
            return redirect(news)
        
        except:
            pass
    
    return render(request,'login.html')

def news(request):
    
    # Redirect to login page if user not logged in
    if request.session.get('user') == None:
        return redirect(login)
    
    # Fetch latest articles from database
    articles = Article.objects.all().order_by('published')[:10]
    
    # Prepare data for feed
    articles_feed_data = utils.prepare_article_data_for_feed(articles)
    
    # Render news feed
    return render(request,'news.html',{'articles':articles_feed_data})

def logout(request):
    
    # Delete cookie
    response = redirect(login)
    
    # Create new session id and preserve data
    request.session.cycle_key()
    
    return response
    
def show_pages(request):
    
    # Get a list of all the posts
    posts = Article.objects.all().order_by('-published')
    posts_data = []
    for post in posts:
        posts_data.append(post.get_feed_data())
    posts = posts_data

    page = int(request.GET.get('page',1))

    
    p = paginator.Paginator(posts,4)
    
    try:
        post_page = p.page(page)
    except paginator.EmptyPage:
        post_page = paginator.Page([], page, p)

    
    if request.META.get('HTTP_X_REQUESTED_WITH') != 'XMLHttpRequest':
        context = {
            'posts': post_page,
        }
        return render(request,
                      'posts.html',
                      context)
    else:
        content = ''
        for post in post_page:
            content += render_to_string('post-item.html',
                                        {'post': post},
                                        request=request)
        return JsonResponse({
            "content": content,
            "end_pagination": True if page >= p.num_pages else False,
        })
        
def fetch_new_articles(request):
    
    last_article_from_feed = request.GET.get('last_article_time')
    
    if last_article_from_feed == None:
        return HttpResponse(400)
    else:
        last_article_from_feed = datetime.datetime.strptime(last_article_from_feed,"%Y-%m-%dT%H-%M-%S%z")
        
        new_articles = Article.objects.filter(added__gt = last_article_from_feed)
        
        if len(new_articles) == 0:
            return HttpResponse(204)
        else:
            
            processed_new_articles = utils.prepare_article_data_for_feed(new_articles)
            
            JsonResponse({"data" : processed_new_articles})
        
        
