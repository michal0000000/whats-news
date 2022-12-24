import scrapper
import datetime

links = scrapper.get_new_links_from_sme()

with open('test.html','w+') as f:
    f.write('''
        <!DOCTYPE html>
        <html lang="sk">
        <body>
    ''')

for l in links:
    article = scrapper.scrape_articles_from_sme_links(l)
    if article != None:
        
        if article['image'] == None:
            article['image'] = '/home/michal00/Desktop/my_projects/news/static/images/index.png'
    
        if article['img_is_video'] == False and article['image'] != None:
            img = f'''<img class="article-image" src="{article['image']}" width="300px">'''
        elif article['img_is_video'] == True and article['image'] != None:
            img = f'''
                <div class="article-video" width="300px">
                    {article['image']}
                <div>
            '''
    
        with open('test.html','a+') as f:
            f.write(f'''
                <div class="news-article">
                ''' +
                
                img
                
                + f'''
                <h2 class="article-headline"> 
                    <a href="{article['source_url']}">{article['headline']}</a>
                </h2>
                <div class="article-excerpt">
                    <h3>{article['subtitle']}</h3>
                </div>
                <div class="article-meta">
                <span class="article-author">{ ', '.join(article['author']) }</span>
                <span class="article-date">{article['published'].strftime('%d %b, %Y')}</span>
                </div>
            </div>
            ''')
        
with open('test.html','a+') as f:
    f.write('''
        </body>
        </html>
    ''')