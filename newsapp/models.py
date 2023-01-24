
from django.utils.timezone import now
from django.db import models
from django import forms

# TODO: research GDPR, if neccessary dont store PI info (i.e. email)
class MembershipToken(models.Model):
    
    id = models.BigAutoField(primary_key=True)
    hashed_token = models.CharField(max_length=64) # sha256
    username = models.CharField(max_length=64,unique=True)
    email = models.CharField(max_length=64,unique=True)
    valid_until = models.DateTimeField()
    last_visit = models.DateTimeField(default=now)
    
    def __str__(self):
        return str(self.id)
    
    def set_last_visit(self,datetime):
        if self.last_visit < datetime:
            self.last_visit = datetime
            return True
        else:
            return False
    
    def check_token(self,submitted_token):
        return self.hashed_token == submitted_token
    
    class Meta:
        app_label = 'newsapp'
    
    """TODO:
        - def valid()
    """
 
class Author(models.Model):
    
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=50)
    
    def __str__(self):
        return self.name
    
class Source(models.Model):
    
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=50)              # SME
    display_name = models.CharField(max_length=50)      # Dennik Sme
    pfp = models.CharField(max_length=512,default='static/default_source.png')              # pfp link         # homepage link
    scraping_link = models.CharField(max_length=512)    # scraping link
    active = models.BooleanField(default=False)
    
    def __str__(self):
        return self.name
    
class Tag(models.Model):
    
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=50)
    
    def __str__(self):
        return self.title
    
class Article(models.Model):
    
    id = models.BigAutoField(primary_key=True)
    headline = models.CharField(max_length=256)
    headline_img = models.CharField(max_length=512,null=True)
    subtitle = models.TextField()
    link = models.CharField(max_length=512) 
    published = models.DateField(blank=True)
    added = models.DateTimeField(default=now)
    source = models.ForeignKey(Source,on_delete=models.CASCADE,null=True)
    authors = models.ManyToManyField(Author)
    tags = models.ManyToManyField(Tag)
    
    # Return id of post
    def __str__(self):
        return self.headline
    
    # Get data needed for news feed page
    def get_feed_data(self):
        return {
            "id" : self.id,
            "headline" : self.headline,
            "image" : self.headline_img,
            "link" : self.link,
            "subtitle" : self.subtitle, 
            "published" : self.published,
            "added" : self.added,
            "source_display_name" : self.source.display_name,
            "source_pfp" : self.source.pfp,
            "source_link" : self.source.scraping_link,
            "authors" : self.authors.all(),
            "tags" : self.tags.all(),
        }

class UpcomingFeaturesForm(forms.Form):
    title = forms.CharField(label="Chytľavý názov", max_length=256)
    description = forms.CharField(label="Frajerský popis", max_length=512)
      
class UpcomingFeatures(models.Model):
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=256)
    description = models.CharField(max_length=512,null=True)
    visible = models.BooleanField(default=False)
    votes = models.ManyToManyField(MembershipToken,default=None)
    submitted = models.DateField(default=now)
    
    def __str__(self):
        return str(self.id)
    
    def get_upcoming_features_data(self):
        return {
            'id' : self.id,
            'title' : self.title,
            'desc' : self.description,
            'votes' : self.votes.count(),
            'first' : False
        }
        