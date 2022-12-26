import hashlib
import datetime
import pytz

from . import scraper

from django.shortcuts import render,redirect
from django.http import HttpResponse

from newsapp.models import MembershipToken

def login(request):
    
    """ ADD USER TO DB  
    try:
        # Code to create first hash
        expiry = datetime.datetime.now(tz=pytz.UTC) + datetime.timedelta(days=14)
        hashed = hashlib.sha256('gayfrog'.encode('utf-8')).hexdigest()
        token = MembershipToken(hashed_token=hashed,username='mike',valid_until=expiry)
        token.save()
        print("Saved.")
    except Exception as e:
        print(e)
    """
    
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
    
    return render(request,'news.html')

def logout(request):
    
    # Delete cookie
    response = redirect(login)
    response.delete_cookie('dont_even_try_to_bruteforce')
    
    # Create new session id and preserve data
    request.session.cycle_key()
    
    return response
    