from models import Article
from models import Tag


# Return new posts since "since_post"
def post_scroll_up(since_post):
    
    # Query database to get newest articles
    articles = Article.objects.filter(id__gte=since_post)[:50] # MAKE THIS DATE
    
    # Get only data neccessary for feed
    article_data = [article.get_feed_data() for article in articles]
    
    return article_data

# Return older posts from "last_post"
def post_scroll_down(last_post):
    articles = Article.objects.filter(id__lte=last_post)[:50] # MAKE THIS DATE