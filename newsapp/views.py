import hashlib
import datetime
import pytz

from django.shortcuts import render,redirect
from django.http import HttpResponse

from newsapp.models import MembershipToken
from newsapp.models import Article, Author, Source, Tag

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
    articles = Article.objects.all().order_by('published')[:25]
    
    # Fetch feed-specific data for each article
    articles_feed_data = []
    for article in articles:
        
        # Get article data from db
        single_article_data = article.get_feed_data()
        print(single_article_data)
        
        """TODO:
            - deal with video article pictures
        """
        
        # Get names of authors
        authors = []
        for author in single_article_data['authors']:
           authors.append(str(author)) 
        
        # Get author count
        author_count = len(authors)
        
        # Create authors string
        authors_string = ''
        if author_count > 2:
            
            # Add names of first two authors
            authors_string = ', '.join(authors[:2])
            
            # Append count of the rest of authors
            authors_string += f' +{ author_count - 2 }'
        
        # If there are only 2 authors
        else:
            
            # Join them with a semicolin
            authors_string = ', '.join(authors)
            
        # Replace authors list from DB with string
        single_article_data['authors'] = authors_string
        
        # Append processed data to final list 
        articles_feed_data.append(single_article_data)
    
    # Render news feed
    return render(request,'news.html',{'articles':articles_feed_data})

def logout(request):
    
    # Delete cookie
    response = redirect(login)
    response.delete_cookie('dont_even_try_to_bruteforce')
    
    # Create new session id and preserve data
    request.session.cycle_key()
    
    return response
    