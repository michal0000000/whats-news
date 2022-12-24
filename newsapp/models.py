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

class Article(models.Model):
    headline = models.CharField(max_length=256)
    headline_img = models.ImageField()
    excerpt = models.TextField() # Subtitle or first paragrapth
    subtitle = models.TextField()
    content = models.TextField()
    source = models.CharField(max_length=256) # CHANGE TO MANY-TO-MANY
    author = models.CharField(max_length=128) # CHANGE TO MANY-TO-MANY
    source_url = models.TextField() 
    source_pfp = models.ImageField() # CHANGE TO MANY-TO-MANY
    published = models.DateField()
    paywall = models.BooleanField() # Eg. paid news like SME.SK
    
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
            "author" : self.author,
            "source_pfp": self.source_pfp, # THIS WILL BE A PHOTO
            "published" : self.published,
            "paywall" : self.paywall
        }
    
class Tag(models.Model):
    title = models.CharField(max_length=50)
    
class Article_Tags(models.Model):
    
    # Create Many-To-Many relation
    article = models.ForeignKey(Article,on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag,on_delete=models.CASCADE)
    
