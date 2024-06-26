# -*- coding: utf-8 -*-
"""Scrapper.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1iQmz16QE3XFad8ytf4ETdp31BczS9a16

# Breaking Bad : Web scrapping summaries from [Fandom.com](https://breakingbad.fandom.com/wiki/Breaking_Bad_(TV_series))
<img src = 'src/imgs/BreakingBadNewImage.png' width = 30%>

### Breaking Bad Summary




**Breaking Bad** is an American crime drama television series created and produced by Vince Gilligan.

## Synopsis

Set and filmed in Albuquerque, New Mexico, the series follows Walter White (Bryan Cranston), an underpaid, overqualified, and dispirited high-school chemistry teacher who is struggling with a recent diagnosis of stage-three lung cancer. Walt turns to a life of crime and partners with a former student, Jesse Pinkman (Aaron Paul), to produce and distribute crystal meth to secure his family's financial future before he dies, while navigating the dangers of the criminal underworld.

## Airing Information

- **Network:** AMC
- **Original Run:** January 20, 2008 – September 29, 2013
- **Seasons:** 5
- **Total Episodes:** 62



### The Plan

1. Will generate link to each episode in the series.
2. Once linkes are populated, 'll iterate over it to get,
    - Character names and
    - episode summary.
3. Combine each seasons episode summary into one file.
4. Save the summary of each summary in separate files,
    - ie for 6 seasons, we'll have total 6 summary files.

# 1. Importing libraries
"""

import os
import re
import time

import shutil
import requests

import numpy as np
import pandas as pd
from tqdm import tqdm

from bs4 import BeautifulSoup as bs

from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.core.utils import ChromeType
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromiumService

# Ensuring empty directory is created

if os.path.isdir('data'):
    shutil.rmtree('data')
os.makedirs('data/summaries')

"""# 2. Getting started with scrapping"""

# Parsing website skelton to bs4 object

BASE_URL = 'https://breakingbad.fandom.com'

r = requests.get(BASE_URL + '/wiki/Category:Seasons_(Breaking_Bad)')

soup = bs(r.content, 'lxml')

"""# 3. Generating links of seasons main page"""

# Generating links to each seasons web page

all_items_S = soup.find_all('div', class_ = 'category-page__members-wrapper')[-1]
season_list = all_items_S.find_all('li', class_ = 'category-page__member')

season_link = []

for season in season_list:
    season_link.append((season.find('a').get('title'), BASE_URL + season.find('a').get('href')))

for sea, link in season_link:
    print(f'{sea} :: {link}')

"""# 4. Defining helper functions"""

# https://pypi.org/project/webdriver-manager/

def call_webdriver():

    return webdriver.Chrome(service = ChromiumService(ChromeDriverManager(chrome_type = ChromeType.CHROMIUM).install()))

def get_summmary(episode_link, season_name):

    driver = call_webdriver()
    driver.minimize_window()
    driver.get(episode_link)
    time.sleep(5)
    all_para = driver.find_elements(By.XPATH, '//*[@id="mw-content-text"]/div/h3[1]//following::p')

    with open(f'data/summaries/{season_name}.txt', 'a') as file:
        for para in all_para:
            if para.aria_role =='paragraph':
                file.write(para.text + '\n')

    # list_para = [para.text for para in all_para if para.aria_role =='paragraph']
    driver.close()
    # return list_para

def get_starring(episode_link):

    r = requests.get(episode_link)
    soup = bs(r.content, 'lxml')

    starring_block = soup.find('div', class_ = 'tabber wds-tabber')
    charactres_class = starring_block.find_all('div', class_ = 'wds-tab__content')

    starrings = [ch.text for char in charactres_class for ch in char.select('li')]

    return starrings

"""# 5. Gathering each episodes summary and character names"""

episode_links, characters = {}, {}

for season, link in tqdm(season_link):

    r = requests.get(link)

    soup = bs(r.content, 'lxml')
    episodes = ['https://breakingbad.fandom.com' + x.find('a').get('href') for x in soup.select('#gallery-0 div.thumb')]

    season = season.split(' (')[0].replace(' ', '_')
    episode_links[season] = episodes

    characts = []

    for episode in episodes:
        get_summmary(episode, season)
        characts.append(get_starring(episode))

    characters[season] = list(np.concatenate(characts))

print(f'Number of episodes recoreded   :: {np.concatenate(list(episode_links.values())).shape[0]}')

"""# 6. Processing obtained character name info."""

# Saving episodes link to a text file for future needs

with open('data/season_nd_episode_links.txt', 'w') as file:
        file.write(str(episode_links))

Season_1 = ['Season_1'] * len(characters['Season_1'])
Season_2 = ['Season_2'] * len(characters['Season_2'])
Season_3 = ['Season_3'] * len(characters['Season_3'])
Season_4 = ['Season_4'] * len(characters['Season_4'])
Season_5A = ['Season_5A'] * len(characters['Season_5A'])
Season_5B = ['Season_5B'] * len(characters['Season_5B'])

seas = Season_1 + Season_2 + Season_3 + Season_4 + Season_5A + Season_5B

chars = characters['Season_1'] + characters['Season_2'] + characters['Season_3'] + characters['Season_4'] + characters['Season_5A'] + characters['Season_5B']

character_df = pd.DataFrame({'Season' : seas, 'Characters' : chars})
character_df.to_csv('data/character_df.csv', index = False)
character_df.head()

print('Number of Characters recorded per season'); print('-' * 40)
character_df.Season.value_counts(sort = False)

# Cleaning character_df : Removing and stripping unwanted characters

character_df.Characters = character_df.Characters.apply(lambda x : re.sub(u'\xa0', u' ', x).strip()) # https://stackoverflow.com/a/11566398
character_df.Characters = character_df.Characters.apply(lambda x : re.sub(r'\t', ' ', x).strip())
character_df.Characters = character_df.Characters.apply(lambda x : x.split(' as ')[-1].strip())
character_df.Characters = character_df.Characters.apply(lambda x : re.sub(r'^as\s', ' ', x).strip())

for idx in [19, 20, 32, 1230]:
    print(character_df.iloc[idx][1])

# Processing character names

character_df.Characters = character_df.Characters.apply(lambda x : re.sub(r'#\d*', ' ', x).strip()) # Removing '#' from name
character_df.Characters = character_df.Characters.apply(lambda x : re.sub(r'\(.*\)', ' ', x).strip()) # Removing '()' and text inside those
character_df.Characters = character_df.Characters.apply(lambda x : re.sub(r'CarWash Patron', 'Car Wash Patron', x).strip())
character_df.Characters = character_df.Characters.apply(lambda x : re.sub('\s+', ' ', x).strip()) # Removing unwanted extra white spaces

print(f'Total number of characters\t\t:: {len(character_df.Characters)}')
print(f'Total number of unique characters\t:: {character_df.Characters.nunique()}')

character_df.head()

character_df.to_csv('data/character_df_cleaned.csv', index = False)
character_df.tail()

"""# 7. Next is What ?

- We have generated summaries all seasons using web scrapping in this part.
- In the next part file [Relationship_Finder.ipynb](https://github.com/jishnukoliyadan/the_breaking_bad_network/blob/master/Relationship_Finder.ipynb), we will try to find the relationsship between characters using `spaCy` and `NetworkX` libraries.

# References

References
- Official documentations of all libraries
- [Fandom](https://www.fandom.com/)
- [Kaggle : data-collection-web-scrapping-tutorial](https://www.kaggle.com/code/jishnukoliyadan/data-collection-web-scrapping-tutorial)
- [DataCamp - A Network Analysis of Game of Thrones](https://www.datacamp.com/projects/76)

Query Resolution
- [GeeksforGeeks](https://www.geeksforgeeks.org/)
- [Stack Overflow](https://stackoverflow.com/)
    
Image Credits
- [IMDb.com](https://www.imdb.com/)
"""