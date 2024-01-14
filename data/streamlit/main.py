import streamlit as st 
import requests
import re
import json
import os
import time
import pandas as pd 
from selenium import webdriver
import re, urllib.parse
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

import utils

def get_driver():
    """
    get selenium driver for gathering image links 
    """
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--window-size=1420,1080')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-dev-shm-usage')        
    driver = webdriver.Chrome(ChromeDriverManager().install(),chrome_options=chrome_options)
    return driver

def get_undetected_driver():
    driver = uc.Chrome(headless=True,use_subprocess=True)
    return driver 

def encode_search_term(text):
    '''
    translates a search term to how duck duck go expect 
    '''
    text = text.replace(' ', '+')
    return text

def scroll_page_to_the_end(driver):
    '''
    scroll driver to the end of the page   
    '''
    reached_page_end = False
    last_height = driver.execute_script("return document.body.scrollHeight")
    while not reached_page_end:
          driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
          time.sleep(2)
          new_height = driver.execute_script("return document.body.scrollHeight")
          if last_height == new_height:
                reached_page_end = True
          else:
                last_height = new_height

def image_search_using_selenium():
    '''
    search images from duck duck go and return dataframe   
    '''
    images_df = pd.DataFrame(columns=['url','query','processed'])
    try:
        driver = get_undetected_driver()
        driver.get(f'https://duckduckgo.com/?q={encode_search_term(st.session_state.search_term)}&kl=us-en&ia=images&iax=images&iaf=size%3ALarge%2Ctype%3Aphoto')
        scroll_page_to_the_end(driver)
        images = []
    except Exception as e:
        st.write(e)
        driver.quit()
        return images_df
    for result in driver.find_elements(By.CLASS_NAME, 'tile--img__media__i'):
        try:
            url = result.find_elements(By.TAG_NAME, 'img')[0].get_attribute('src')  
            images.append(url)
        except Exception as e:
            st.write(e)
    driver.quit()
    if len(images)>0:
        images_df = pd.DataFrame(images,columns=['url'])
        images_df['query'] = st.session_state.search_term
        images_df['processed'] = 0
    return images_df 

def app():
    st.title('Photo data collection')
    st.subheader('1. Get image data from URLs')
    st.session_state['search_term'] = st.text_input('Search term')
    if 'search_term' in st.session_state and st.session_state.search_term:
        if st.button('Search images'):
            with st.spinner('Running...'):
                st.session_state['image_urls_df'] = image_search_using_selenium()
                if st.session_state.image_urls_df.shape[0] > 0 and 'image_urls_df' in st.session_state:
                    image_urls_df_filtered = utils.dedupe_urls(st.session_state.image_urls_df)
                    utils.insert_reccords_pandas(image_urls_df_filtered)
    if 'image_urls_df' in st.session_state:
        st.write(f'Image URLs found: {st.session_state.image_urls_df.shape[0]}')
    
    st.subheader('2. Get image data from URLs and save to database')
    if st.button('Get image blobs'):
        with st.spinner('Running...'):
            st.session_state['image_urls_unprocessed'] =  utils.execute_sql("SELECT * FROM URLS WHERE processed = 0")
            st.write('*'*50)
            unprocessed_df_before, processed_df_before = utils.query_database_processed_helper()
            utils.save_iamge_data_batch(st.session_state['image_urls_unprocessed'] )
            unprocessed_df_after, processed_df_after= utils.query_database_processed_helper()
            utils.print_database_processed_helper(unprocessed_df_before, processed_df_before, 'BEFORE')
            utils.print_database_processed_helper(unprocessed_df_after, processed_df_after, 'AFTER')
        
    st.subheader('3. Export images to folder')
    if st.button('Export image blobs to file'):
        with st.spinner('Running...'):
            file_path = utils.create_image_directory()
            st.session_state['images'] = utils.execute_sql("SELECT * FROM IMAGES ")
            if 'images' in st.session_state and file_path:
                utils.export_images_and_save(file_path,st.session_state.images)
           
if __name__ =="__main__":
    app() 