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
import sqlalchemy as sa



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
        except [requests.HTTPError, requests.ConnectionError,requests.ConnectTimeout]:
            error_logger.exception('Fetching ABC NEWS mainpage receiving '+str(mainpage))
            mainpage= None
            time.sleep(5)
        except TimeoutError:
            error_logger.exception()
            sys.exit('Fetching ABC News mainpage failed 5 times')
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
    abc_cates_df = abc_cates_df.drop_duplicates()
    abc_mainpage_news_df = abc_mainpage_news_df.drop_duplicates()

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
    newspage = None
    ct = -1
    while newspage is None:
        ct+=1
        try:
            if ct>=5:
                raise TimeoutError(f'Fetching news content page  {abcsite}{href} failed: 5 times')
            newspage = requests.get(abcsite+href)
            newspage.raise_for_status() # If not 200 raise httperror
        except [requests.HTTPError,requests.ConnectionError, requests.ConnectTimeout] as inst:
            print(inst)
            error_logger.exception(f'Fetching news content page  {abcsite}{href} failed:  ')
            # Access error, return null
        except TimeoutError:
            error_logger.exception('Fetching mainpage failed 5 times')
            return None
        else:
            f = open("news/abc/newspage/"+teaser[:10]+str(datetime.now()).replace(':','-')+".html", "w")
            f.write(newspage.text)
            f.close()
            return newspage
        time.sleep(5)

def analyse_news_content_page(newspage):
    try:
        newssoup = BeautifulSoup(newspage.text,'lxml')
        news_title = newssoup.find('h1').text
        news_time = newssoup.find(class_="_1EAJU _1NECW _2L258 _14LIk _3pVeq hmFfs _2F43D")['datetime']
        news_date = news_time[:10]
        news_body = newssoup.find('div', id = 'body')
        news_body.find_all(class_='r6CUb u0kBv _3CtDL _1_pW8 _3Fvo9')
        news_topics = []
        for i in news_body.find_all(class_='r6CUb u0kBv _3CtDL _1_pW8 _3Fvo9'):
            news_topics.append({'Label':i.text,'Link':i['href']})
        news_content = ''
        for i in news_body.find_all('p'):
            news_content+= i.text+'\n'
        return news_title, news_topics, news_time, news_date, news_content
    except:
        error_logger.exception('Failed to analyse news_content')
        sys.exit()

def fetch_all_news():
    
    return


def store_to_database(name,df):
    try:
        debug_logger.info('Saving scrapped data into database')
        engine = sa.create_engine(
        f"postgresql+psycopg2://{cf['user']}:{cf['password']}@{cf['host']}:{cf['port']}/{cf['database']}",
        isolation_level="SERIALIZABLE",
    )
        df.to_sql(name,con = engine,if_exists = 'replace',index_label='sub_id')
    except:
        error_logger.exception()
    return



# %%
if __name__== '__main__':
    c = configparser.ConfigParser()
    c.read('config/1kindtask.ini')
    c.sections()
    cf = c['postgredb']
    error_count = 0
    #fetch ABC News Mainpage
    mainpage = fetch_abc_news_main_page()   
    #generate dataframes from mainpage
    abc_categories_df, abc_mainpage_news_df = analyse_main_page(mainpage)
    # fetch news contents, analyse and store into dataframe
    abc_mainpage_news_pages = []
    for ind,row in abc_mainpage_news_df.iterrows():
        time.sleep(0.5)
        abc_mainpage_news_pages.append(fetch_abc_news_content_page(row['teaser'],row['href']))
    
    abc_news_pages = abc_mainpage_news_pages
    abc_news_titles = []
    abc_news_topics = []
    abc_news_times = []
    abc_news_dates = []
    abc_news_contents = []
    abc_news_topics_list = []
    for i in abc_news_pages:
        news_title, news_topics, news_time, news_date, news_content = analyse_news_content_page(i)
        for j in news_topics:
            if j not in abc_news_topics_list:
                abc_news_topics_list.append(j) 
        time.sleep(0.5)
        abc_news_titles.append(news_title)
        abc_news_topics.append(news_topics)
        abc_news_dates.append(news_date)
        abc_news_times.append(news_time)
        abc_news_contents.append(news_content)
    
    abc_mainpage_news_df['title'] = abc_news_titles
    abc_mainpage_news_df['topics'] = abc_news_topics
    abc_mainpage_news_df['time'] = abc_news_times
    abc_mainpage_news_df['content'] = abc_news_contents
    store_to_database('news',abc_mainpage_news_df)
    store_to_database('topics',pd.DataFrame(abc_news_topics_list))




        


