# %%
## Importation
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
from datetime import datetime



# %%
## request for site mainpage and category pages

abcsite = 'https://www.abc.net.au'
init = requests.get(abcsite+'/news/')
f = open("news/abc/mainpage"+str(datetime.now()).replace(':','-')+".html", "w")
f.write(init.text)
f.close()

s = BeautifulSoup(init.text,'lxml')
abc_cate=s.find_all('a',class_='_3cShj _2p6Xq')
abc_cates_href =[]
abc_cates = []
for i in abc_cate:
    if i['href'] not in abc_cates_href:
        abc_cates.append({'name':i.text,'href':i['href'],'mainpage':requests.get(abcsite+i['href'])})
##print (abc_cates)

# %%
## get site categories
for i in abc_cates:
    currentsoup = BeautifulSoup(i['mainpage'].text,'lxml')
    current_cate_article = currentsoup.find_all('a',class_='_2VA9J u0kBv _3CtDL _1_pW8 _3Fvo9 VjkbJ')



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


