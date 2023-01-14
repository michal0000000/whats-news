from newsapp.models import Article

def prepare_article_data_for_feed(articles):
    
    # Fetch feed-specific data for each article
    articles_feed_data = []
    for article in articles:
        
        # Get article data from db
        single_article_data = article.get_feed_data()
        
        """TODO:
            - deal with video article pictures
        """
        
        # Get names of authors
        authors = []
        for author in single_article_data['authors']:
           authors.append(str(author))
           
        # TODO: Properly handle tags
        tags = []
        for tag in single_article_data['tags']:
            tags.append(str(tag))
        single_article_data['tags'] = tags
        
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
        
        # Reverse articles to get correct order in feed
        articles_feed_data.reverse()
        
    return articles_feed_data