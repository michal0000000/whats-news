import hashlib
import datetime
import pytz

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
- sidebar with upcoming features, user can click to vote or submit new feature (wont be published before review)
- quote of the day on login screen
- menu should contain different feeds: Slovensko, Tech, Kyberbezpecnost, Zahranicie, Ekonomika
- connect twitter account and see live scrolling feed of cool threads regarding that topic (like stocks)
"""

POSTS_PER_PAGE = 4

def login(request):
    
    # Code to create first hash
    #expiry = datetime.datetime.now(tz=pytz.UTC) + datetime.timedelta(days=14)
    #hashed = hashlib.sha256('gayfrog'.encode('utf-8')).hexdigest()
    #token = MembershipToken(hashed_token=hashed,username='mike2',email='miccheck@12.sk',valid_until=expiry)
    #token.save()
    
    if request.method == 'POST':
        
        # Get token and hash it
        raw_token = request.POST['token']
        hashed_token = hashlib.sha256(raw_token.encode('utf-8')).hexdigest()
        
        # Handle login
        try:
            
            # Get user with matching hash
            user = MembershipToken.objects.get(hashed_token=hashed_token)
            
            # Create session variable with current user id
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
    articles = Article.objects.all().order_by('-published')
    
    # Set last visit
    time_of_visit = datetime.datetime.now().replace(tzinfo=pytz.UTC)
    token = MembershipToken.objects.get(id=request.session['user'])
    result_of_new_visit_time = token.set_last_visit(time_of_visit)
    
    
    # Handle bad request
    if result_of_new_visit_time == False:
        return HttpResponse(status=400)

    # Fetch GET parameter from request
    page = int(request.GET.get('page',1))
    
    # Create Paginator object with X articles per page
    p = paginator.Paginator(articles,POSTS_PER_PAGE)
    
    try:
        # If next page exists, fetch articles
        article_page = p.page(page)
        article_page = utils.prepare_article_data_for_feed(article_page)
    except paginator.EmptyPage:
        
        # If last page has been reached, create empty page with no articles
        article_page = paginator.Page([], page, p)

    # If user is requesting full page (page 1)
    if request.META.get('HTTP_X_REQUESTED_WITH') != 'XMLHttpRequest':
        
        # Create context for page
        context = {
            'articles': article_page,
        }
        
        # Render page
        return render(request,
                      'news.html',
                      context)
        
    # If user is requesting next page of articles and not the whole page
    else:
        content = ''
        
        # Render each post from template to string
        for article in article_page:
            content += render_to_string('news-item.html',
                                        {'article': article},
                                        request=request)
            
        # Serve new articles as Json
        return JsonResponse({
            "content": content,
            "end_pagination": True if page >= p.num_pages else False,
        })
    
    
    
    
    "-------------------------------------------------------"
    
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
    
    # Set last visit
    time_of_visit = datetime.datetime.now().replace(tzinfo=pytz.UTC)
    token = MembershipToken.objects.get(id=request.session['user'])
    result_of_new_visit_time = token.set_last_visit(time_of_visit)
    
    # Handle bad request
    if result_of_new_visit_time == False:
        return HttpResponse(status=400)
    
    # Fetch feed data
    for post in posts:
        posts_data.append(post.get_feed_data())
    posts = posts_data

    # Fetch GET parameter from request
    page = int(request.GET.get('page',1))
    
    # Create Paginator object with X posts per page
    p = paginator.Paginator(posts,POSTS_PER_PAGE)
    
    try:
        # If next page exists, fetch articles
        post_page = p.page(page)
    except paginator.EmptyPage:
        
        # If last page has been reached, create empty page with no articles
        post_page = paginator.Page([], page, p)

    # If user is requesting full page (page 1)
    if request.META.get('HTTP_X_REQUESTED_WITH') != 'XMLHttpRequest':
        
        # Create context for page
        context = {
            'posts': post_page,
        }
        
        # Render page
        return render(request,
                      'posts.html',
                      context)
        
    # If user is requesting next page of articles and not the whole page
    else:
        content = ''
        
        # Render each post from template to string
        for post in post_page:
            content += render_to_string('post-item.html',
                                        {'post': post},
                                        request=request)
            
        # Serve new articles as Json
        return JsonResponse({
            "content": content,
            "end_pagination": True if page >= p.num_pages else False,
        })

# Function that handles refreshing feed with new articles
def fetch_new_articles(request):

    # Get last visit of user to determine what articles are new
    current_user = MembershipToken.objects.get(id=request.session['user'])
    current_user_last_visit = current_user.last_visit
    
    print(f"last_visit: {current_user_last_visit}")

    # Fetch new articles that arent displayed on feed yet
    new_articles = Article.objects.filter(added__gt = current_user_last_visit)
    
    print(f"new_articles: {new_articles}")
    
    # Handle no new articles
    if len(new_articles) == 0:
        return HttpResponse(status=204)
    
    else:
        
        # Fetch feed data for new articles
        processed_new_articles = utils.prepare_article_data_for_feed(new_articles)
        
        # Set new last visit
        time_of_visit = datetime.datetime.now().replace(tzinfo=pytz.UTC)
        
        try:
            
            # Check if last visit is older than current visit
            if current_user.last_visit < time_of_visit:
                current_user.last_visit = time_of_visit
                current_user.save()
            else:
                raise Exception("ERR: fetch_new_articles(): Time of visit is smaller than last visit!")
        except Exception as e:
            
            # Handle bad request
            return HttpResponse(status=400)
        
        print(f"returning: {processed_new_articles}")
        
        # Send new articles to frontend
        return JsonResponse({"data" : processed_new_articles})
        
def insert_dummy_articles(request):
    
    source = Source.objects.get(name='sme')
    
    for i in range(1,4):
        article_object = Article(
            headline = f"Dummy post {i}",
            headline_img = "static/images/index.png",
            excerpt = "Something has happend and YOU should know about it.", 
            subtitle = "Something has happend and YOU should know about it.",
            content = "",
            link = "",
            source = source,
            published = datetime.datetime.now().replace(tzinfo=pytz.UTC),
            paywall = True,
            img_is_video = False,
        )
        article_object.save()
    
    return HttpResponse("<h1>Done.</h1>")