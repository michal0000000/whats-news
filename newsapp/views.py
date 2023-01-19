import hashlib
import datetime
import pytz
import traceback

from .logger.logger import log
from .logger.logger_sink import LoggerSink

from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.core import paginator
from django.template.loader import render_to_string
from django.contrib import messages
from django.template import RequestContext
from django.db.models import Count

from newsapp.models import MembershipToken
from newsapp.models import Article, Author, Source, Tag, UpcomingFeatures
from newsapp.models import UpcomingFeatures, UpcomingFeaturesForm

from . import scraper
from . import utils



"""TODO:
- implement tags
- quote of the day on login screen
- connect twitter account and see live scrolling feed of cool threads regarding that topic (like stocks)
- implement categories (that are above tags and are assigned manually)
- add some feature on the right (like hottest tags?)
- hover on profile picture should show subscription expiration
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
    
    # Fetch upcoming features
    upcoming_features_objects = UpcomingFeatures.objects.filter(visible=True).annotate(v_count=Count('votes')).order_by('-v_count')
    upcoming_features = []
    for feature in upcoming_features_objects:
        
        # Dont add the same feature twice
        if feature not in upcoming_features:
            
            # Add feature to list
            upcoming_features.append(feature.get_upcoming_features_data())
        
    # Set first feature to be "first" so it can be opened on frontend
    upcoming_features[0]['first'] = True

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
        
        # Create form for submitting new functionality
        new_func_form = UpcomingFeaturesForm()
        
        # Create context for page
        context = {
            'articles': article_page,
            'features' : upcoming_features,
            'new_func_form' : new_func_form,
            'unbiased' : 'false'
        }
        
        # Check for unbiased mode
        unbiased = request.GET.get('u','')
        if unbiased == 'true':
            context['unbiased'] = 'true'
        
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
    
    # Fetch upcoming features
    upcoming_features_objects = UpcomingFeatures.objects.filter(visible=True)
    upcoming_features = []
    for feature in upcoming_features_objects:
        upcoming_features.append(feature.get_upcoming_features_data())
    
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
            'features' : upcoming_features
        }
        
        print(f'context : {context}')
        
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

# TODO: implement bot check where a user can add only 5 functions within 5 minutes
# TODO: split form entries by visible status in administration
def submit_new_func(request):
    
    # If not post request, return forbidden
    if request.method != 'POST':
        return HttpResponse(status=403)
    
    # Validate POST data
    form = UpcomingFeaturesForm(request.POST)
    try:
        if form.is_valid():
            
            # Extract data from form
            func_title = form.cleaned_data['title']
            func_desc = form.cleaned_data['description']
            
            # Insert new feature into database
            new_func_request = UpcomingFeatures(title=func_title,description=func_desc)
            new_func_request.save()
            
            # Fetch current user to set as default vote
            try:
                first_vote = MembershipToken.objects.get(id=request.session['user'])
                new_func_request.votes.add(first_vote)
            except Exception as e:
                log(f"ERR: submit_new_func() - Couldn't add user {str(request.session['user'])} as first vote. Traceback: {traceback.print_exc()}",LoggerSink.NEWS)
            
            # Send success message
            messages.success(request,'Nice! Dík za feedback.')
            return redirect(news)
        else:
            print(str(form.errors))
            return HttpResponse(status=400)
    except Exception as e:
        log(f"ERR: submit_new_func() - Problem validating form. Traceback: {traceback.print_exc()}",LoggerSink.NEWS)
        return HttpResponse(status=400)

def vote_for_new_func(request):
    
    # If not post request, return forbidden
    if request.method != 'POST':
        return HttpResponse(status=403)
    
    try:
        # Validate form data
        choice = request.POST['feature-choice'][0]
        if type(choice) == str and choice != '':
            
            # Give choice to feature that user voted for
            give_vote_to = UpcomingFeatures.objects.get(id=choice)
            voter = MembershipToken.objects.get(id=request.session['user'])
            
            # Check if user has voted already
            if give_vote_to.votes.filter(pk=voter.pk).exists():
                messages.error(request,'Sry, už si hlasoval.')
            else:
                
                # If user hasn't voted yet, add vote
                give_vote_to.votes.add(voter)
                messages.success(request,'Nice! Dík za feedback.')
                    
            return redirect(news)
            
    # Handle errors
    except Exception as e:
        log(f"ERR: vote_for_new_func() - Problem validating form. Traceback: {traceback.print_exc()}",LoggerSink.NEWS)
        return HttpResponse(status=403)

# Function that handles refreshing feed with new articles
def fetch_new_articles(request):

    # Get last visit of user to determine what articles are new
    current_user = MembershipToken.objects.get(id=request.session['user'])
    current_user_last_visit = current_user.last_visit

    # Fetch new articles that arent displayed on feed yet
    new_articles = Article.objects.filter(added__gt = current_user_last_visit)
    
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