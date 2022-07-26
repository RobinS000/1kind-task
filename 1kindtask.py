# %%
## Importation

import sys
import configparser
import logging
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime
import re
import psycopg2 as pg



# %%
log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
c = configparser.ConfigParser()
c.read('config/1kindtask.ini')
cd = c['DEFAULT']
abcsite = cd['abcsite']
error_log_path = cd['log_path_warning']
debug_log_path = cd['log_path_debug']


def setup_logger(name, log_file, level):
    #Logger setup so can use different instance to log to different paths

    handler = logging.FileHandler(log_file)        
    handler.setFormatter(log_formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger
error_logger = setup_logger('error_logger',error_log_path+datetime.now().strftime('%Y-%m-%d')+'.log',logging.WARNING)
debug_logger = setup_logger('debug_logger',debug_log_path+datetime.now().strftime('%Y-%m-%d')+'.log',logging.DEBUG)

## request for site mainpage and category pages
def fetch_abc_news_main_page():
    mainpage = None
    error_count = -1
    while mainpage is None:
        error_count +=1
        print(error_count)
        if error_count>=5:
            raise TimeoutError('Fetching mainpage failed 5 times')
        try:
            abcnews = abcsite+'/news/'
            debug_logger.info(f'Fetching ABC news mainpage {abcnews}')
            mainpage = requests.get(abcnews)
            mainpage.raise_for_status() # Check for status code 200
        except [requests.HTTPError, requests.ConnectionError,requests.ConnectTimeout] as inst:
            print(inst)
            error_logger.exception('Fetching ABC NEWS mainpage receiving '+str(mainpage))
            mainpage= None
            time.sleep(5)
        except TimeoutError:
            error_logger.exception('Fetching mainpage failed 5 times')
            sys.exit('Fetching mainpage failed 5 times')
    f = open("news/abc/mainpage"+str(datetime.now()).replace(':','-')+".html", "w")
    f.write(mainpage.text)
    f.close()
    return mainpage
##print (abc_cates)

# %%
## get ABC News mainpage news and get ABC News categories
def analyse_main_page(mainpage):
    try:
        soup = BeautifulSoup(mainpage.text,'lxml')
        abc_cates=soup.find_all('a',class_='_3cShj _2p6Xq')
        abc_cates_href =[]
        abc_cates_label = []
        for i in abc_cates:
            if i['href'] not in abc_cates_href:
                abc_cates_label.append(i.text)
                abc_cates_href.append(i['href'])
        abc_cates_df = pd.DataFrame({
            'label' : abc_cates_label,
            'href' : abc_cates_href
        })
        abc_mainpage_news_teaser = []
        abc_mainpage_news_category = []
        abc_mainpage_news_href = []
        abc_mainpage_news_date = []
        abc_mainpage_news_sourcepage = []
        abc_mainpage_news_lists = [
            soup.find_all('a',class_='_3pM2c u0kBv _3CtDL _1_pW8 _3Fvo9 VjkbJ'),
            soup.find_all('a',class_='_2VA9J u0kBv _3CtDL _1_pW8 _3Fvo9 VjkbJ'),
            soup.find_all('a',class_='_37gvg u0kBv _3CtDL _1_pW8 _3Fvo9 VjkbJ')
        ]
        find_date = lambda x : x if x is None else x.group()
        find_category = lambda x: x if x is None else x.group(1)
        for i in abc_mainpage_news_lists:
            for j in i:
                abc_mainpage_news_teaser.append(j.text)
                abc_mainpage_news_href.append(j['href'])
                abc_mainpage_news_date.append(find_date(re.search('\\d{4}-\\d{2}-\\d{2}',j['href'])))
                abc_mainpage_news_category.append(find_category(re.search('/news/(.*)/\\d{4}-\\d{2}-\\d{2}',j['href'])))
                abc_mainpage_news_sourcepage.append('mainpage')

        abc_mainpage_news_df = pd.DataFrame({
            'teaser' : abc_mainpage_news_teaser,
            'href' : abc_mainpage_news_href,
            'date' : abc_mainpage_news_date,
            'category' : abc_mainpage_news_category,
            'sourcepage' : abc_mainpage_news_sourcepage
        })
    except:
        error_logger.exception('Analyse ABC mainpage failed ')
        sys.exit('Analyse ABC mainpage failed')

    return abc_cates_df, abc_mainpage_news_df


# %%
# fetch category pages
def fetch_abc_news_category_page(category):
    try:
        mainpage = requests.get(abcsite+'/news/'+category)
        mainpage.raise_for_status() # If not 200 raise exception
    except Exception as inst:
        print(inst)
        f = open(error_log_path+datetime.now().strftime('%Y-%m-%d')+'.txt', "a")
        f.write(datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')+'     Fetching ABC mainpage receiving '+str(inst))
        f.close()
        return None
        # Access error, return null
    f = open("news/abc/mainpage"+str(datetime.now()).replace(':','-')+".html", "w")
    f.write(mainpage.text)
    f.close()
    return mainpage


# %%
#fetch news content page
def fetch_abc_news_content_page(teaser,href):
    try:
        newspage = requests.get(abcsite+href)
        newspage.raise_for_status() # If not 200 raise httperror
    except [requests.HTTPError,requests.ConnectionError, requests.ConnectTimeout] as inst:
        print(inst)
        error_logger.exception(f'Fetching news content page for {teaser} at {abcsite}{href} failed:  ')
        return None
        # Access error, return null
    else:
        f = open("news/abc/newspage/"+teaser[:10]+str(datetime.now()).replace(':','-')+".html", "w")
        f.write(newspage.text)
        f.close()
        return newspage


    ##print (abc_cates)   
    for i in abc_cates:
        currentsoup = BeautifulSoup(i['mainpage'].text,'lxml')
        current_cate_articles = currentsoup.find_all('a',class_='_2VA9J u0kBv _3CtDL _1_pW8 _3Fvo9 VjkbJ')


def analyse_news_content_page(newscontent):
    return


def store_to_database():
    c = configparser.ConfigParser()
    c.read('config/1kindtask.ini')
    c.sections()
    cf = c['postgredb']
    conn = pg.connect(
        user = cf['user'],
        password = cf['password'],
        host = cf['host'],
        port = cf['port'],
        database = cf['database']
    )
    cursor = conn.cursor()
    # Print PostgreSQL details
    print("PostgreSQL server information")
    print(conn.get_dsn_parameters(), "\n")



# %%
if __name__== '__main__':
    error_count = 0
    #fetch ABC News Mainpage
    mainpage = fetch_abc_news_main_page()
    if mainpage is None:
        print('Fetch mainpage failed')
        sys.exit()
    
    #generate dataframes from mainpage
    #try:
    abc_categories_df, abc_mainpage_news_df = analyse_main_page(mainpage)
    print(abc_categories_df)
    print(abc_mainpage_news_df)
    abc_mainpage_news_pages = []
    for ind,row in abc_mainpage_news_df.iterrows():
        time.sleep(0.5)
        abc_mainpage_news_pages.append(fetch_abc_news_content_page(row['teaser'],row['href']))
        

    #except Exception as e:
    #    print(e.with_traceback)
    #    f = open("log/abc/errors/"+datetime.now().strftime('%Y-%m-%d')+'.txt', "a")
    #    f.write(datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')+'     Analysing ABC News mainpage failed, exit app')
    #    f.close()
    #    sys.exit('Analysing ABC News mainpage failed, exit app')

    #fetch news from categories
    #for i in abc_cates_df:
    #    print(i)




    #for i in abc_cates:
    #    currentsoup = BeautifulSoup(i['mainpage'].text,'lxml')
    #    current_cate_article = currentsoup.find_all('a',class_='_2VA9J u0kBv _3CtDL _1_pW8 _3Fvo9 VjkbJ')



# %%
testsoup = BeautifulSoup(abc_cates[0]['mainpage'].text,'lxml')
cate_news = testsoup.find_all('a',class_='_2VA9J u0kBv _3CtDL _1_pW8 _3Fvo9 VjkbJ')
abc_cates[0]



# %%
newsc = requests.get(abcsite+cate_news[0]['href'])
newssoup = BeautifulSoup(newsc.text,'lxml')

# %%
news_title = newssoup.find('h1').text
news_body = newssoup.find('div', id = 'body')
news_body.find_all(class_='r6CUb u0kBv _3CtDL _1_pW8 _3Fvo9')
news_topics = []
for i in news_body.find_all(class_='r6CUb u0kBv _3CtDL _1_pW8 _3Fvo9'):
    news_topics.append({'Label':i.text,'Link':i['href']})
news_body.find_all('p' or 'a')    


# %%
newssoup1 = BeautifulSoup(requests.get('https://www.abc.net.au/news/2022-07-22/new-york-washington-mayors-ask-biden-help-asylum-seekers/101262182').text,'lxml')
news_title1 = newssoup1.find('h1').text
news_body1 = newssoup1.find('div', id = 'body')
news_body1.find_all(class_='r6CUb u0kBv _3CtDL _1_pW8 _3Fvo9')
news_body1.find_all('p' or 'a')
newssoup1.find('h1')
newssoup1.find(class_='timestamp')

# %%
news_title1 = newssoup1.find('h1').text
news_body1 = newssoup1.find('div', id = 'body')
#news_author1 = news_body1.strong

news_time1 = newssoup1.find(class_="_1EAJU _1NECW _2L258 _14LIk _3pVeq hmFfs _2F43D")['datetime']
news_date1 = news_time1[:10]                       #datetime.date(datetime.strptime(news_time1,"%Y-%m-%dT%H:%M:%S.%fZ")).strftime('%Y-%m-%d')
news_body1.find_all(class_='r6CUb u0kBv _3CtDL _1_pW8 _3Fvo9')

news_topic1 = news_body1.find(class_='_2wDgl').find_all('a')
news_topics1 = []
for i in news_topic1:
    news_topics1.append({'Label':i.text,'Link':i['href']})
news_category1 = abc_cates[0]
news_content1 = ''
for i in news_body1.find_all('p'):
    news_content1 += i.text+'\n'
newssoup1.find('h1')
newssoup1.find(class_='timestamp')

# %%
news_content1 = ''
for i in news_body1.find_all('p'):
    news_content1 += i.text+'\n'
print(news_content1)


if __name__== '__Main__':
    error_count = 0
