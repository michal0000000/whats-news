from django.db import models


class MembershipToken(models.Model):
    hashed_token = models.CharField(max_length=64,unique=True) # sha256
    username = models.CharField(max_length=64,unique=True)
    email = models.CharField(max_length=64,unique=True)
    valid_until = models.DateTimeField()
    
    def __str__(self):
        return self.username
    
    def check_token(self,submitted_token):
        return self.hashed_token == submitted_token
    
    """TODO:
        - def valid()
    """
 
class Author(models.Model):
    name = models.CharField(max_length=50)
    
    def __str__(self):
        return self.name
    
class Source(models.Model):
    
    name = models.CharField(max_length=50)              # sme.sk
    display_name = models.CharField(max_length=50)      # Dennik Sme
    pfp = models.CharField(max_length=512)              # pfp lunk
    link = models.CharField(max_length=512)             # homepage link
    scraping_link = models.CharField(max_length=512)    # scraping link
    
    def __str__(self):
        return self.name
    
class Tag(models.Model):
    title = models.CharField(max_length=50)
    
class Article(models.Model):
    headline = models.CharField(max_length=256)
    headline_img = models.CharField(max_length=512)
    subtitle = models.TextField()
    excerpt = models.TextField()
    content = models.TextField()
    link = models.CharField(max_length=512) 
    published = models.DateField()
    paywall = models.BooleanField() # Eg. paid news like SME.SK
    source = models.ForeignKey(Source,on_delete=models.CASCADE)
    authors = models.ManyToManyField(Author)
    tags = models.ManyToManyField(Tag)
    img_is_video = models.BooleanField(default=False)
    
    # Return id of post
    def __str__(self):
        return self.id
    
    # Get data needed for news feed page
    def get_feed_data(self):
        return {
            "id" : self.id,
            "headline" : self.headline,
            "image" : self.headline_img,
            "excerpt" : self.excerpt, 
            "published" : self.published,
            "paywall" : self.paywall,
            "source" : self.source,
            "authors" : self.author.all(),
            "tags" : self.tags.all(),
            "img_is_video" : self.img_is_video
        }