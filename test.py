import streamlit as st
# import streamlit.components.v1 as components
# from streamlit_option_menu import option_menu
# from st_aggrid import AgGrid, GridOptionsBuilder

# import time
# import io
import json
import os, sys

# import pandas as pd
# import numpy as np
# import plotly_express as px

from openai import OpenAI
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------
import time
import re
from urllib.parse import urlparse, urlunparse

import pandas as pd

from bs4 import BeautifulSoup


from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


# initialize session states
if 'keywords' not in st.session_state:
    st.session_state['keywords'] = False
    st.session_state['summary'] = False

# get api key
try:
    with open('../../openai_key.txt', 'r') as file:
        API_KEY = file.read().strip()
except:
    pass

try:
    client = OpenAI(api_key=API_KEY)
except:
    client = OpenAI(api_key=st.secrets["api_key"])


def sort_key(item):
    return not ('about' in item or 'story' in item or 'mission' in item or 'who-we' in item or 'vision' in item)


def url_parse(internal_hrefs):
    normalized_urls = set()
    for url in internal_hrefs:
        parsed_url  = urlparse(url)
        clean_url = urlunparse(parsed_url._replace(fragment=''))
        normalized_urls.add(clean_url)
    normalized_urls = list(normalized_urls)
    return normalized_urls


# @st.cache_resource
def get_driver():
    options = Options()
    options.add_argument('--disable-gpu')
    options.add_argument('--headless')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    options.add_experimental_option("detach", True)
    return webdriver.Chrome(options=options)


def get_summary(page_text):
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        response_format={ "type": "json_object" },
        messages=[
            {"role": "system", 
             "content": "This is the page text scraped off a startup website. Pull out the keywords and a 3-4 sentence summary of what this company does. Format it in json:"},
            {"role": "user", 
             "content": f'Extract from the following page text: [{page_text}]'}
        ]
        )
    return json.loads(completion.choices[0].message.content)


tab1, tab2 = st.tabs(['Search', 'URL'])

with tab1:
    test = st.text_input('test')
    st.write(test)
with tab2:
    # get user url input
    url = st.text_input('Enter url')

    # prepend http if not found in url
    if 'http' not in url:
        url = 'https://' + url

    st.session_state['message'] = st.empty()

    # button for scraping site
    if st.button('Scrape Site'):
    # set session state for loading messages


        driver = get_driver()
        driver.get(url)

        st.session_state['message'].text(f"Loading {url}...")

        # parse url
        time.sleep(2)
        url = driver.current_url
        # st.write(url)
        parsed_url = urlparse(url)
        hostname = parsed_url.hostname
        # st.write(hostname)

        # Use BeautifulSoup to parse and scrape
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        page_text = soup.get_text()

        # get anchor tags
        anchor_tags = driver.find_elements(By.TAG_NAME, "a")

        # Extract href attributes
        hrefs = [tag.get_attribute('href') for tag in anchor_tags if tag.get_attribute('href')]
        
        # drop duplicate hrefs
        hrefs = set(hrefs)

        # create list of internal hrefs
        internal_list = [f'{url}', hostname.split('.')[0]]
        internal_hrefs = [href for href in hrefs if all(include in href for include in internal_list)]
        internal_hrefs = url_parse(internal_hrefs)
        internal_hrefs = set(internal_hrefs)
        internal_hrefs = list(internal_hrefs)
        internal_hrefs = [href for href in internal_hrefs if 'about' in href or 'story' in href or 'mission' in href or 'who-we' in href or 'vision' in href]
        # internal_hrefs = sorted(internal_hrefs, key=sort_key)


        for url in internal_hrefs:
            st.session_state['message'].text(f"Loading {url}...")
            driver.get(url)
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            page_text += soup.get_text()

        # Close the browser
        driver.quit()

        # Display the scraped text
        # st.write(internal_hrefs)
        # st.write(page_text)

        st.session_state['message'].text(f"Extracting Keywords/Summary...")
        data = get_summary(page_text)
        # st.write(data)

        # st.markdown('### Summary:', unsafe_allow_html=True)
        # st.write(data['summary'])

        # st.markdown('### Keywords:', unsafe_allow_html=True)
        # st.write(data['keywords'])

        # st.session_state['message'].empty()
        st.session_state['keywords'] = data['keywords']
        st.session_state['summary'] = data['summary']
    
    if st.session_state['keywords']:
        st.markdown('### Summary:', unsafe_allow_html=True)
        st.write(st.session_state['summary'])

        st.markdown('### Keywords:', unsafe_allow_html=True)
        st.write(st.session_state['keywords'])

        st.session_state['message'].empty()