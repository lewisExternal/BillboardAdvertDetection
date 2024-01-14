import sqlite3 as sl
import pandas as pd 
import requests 
import streamlit as st 
from datetime import datetime  
import os 
from itertools import islice
import asyncio 
import numpy as np 

from PIL import Image
import io

# local imports 
from config import BATCH_SIZE, TEST_SPLIT_FRAC, VALIDATE_SPLIT_FRAC

if os.getenv('DOCKER_RUNNING',False):
    filepath = '/output/'
else:
    filepath= '../output/'

def create_database_table():
    try:
        con = sl.connect(f'{filepath}image-data.db', check_same_thread=False)
        with con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS URLS (
                    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    url TEXT,
                    query TEXT,
                    processed INTEGER
                );
            """)
            con.execute("""
                CREATE TABLE IF NOT EXISTS IMAGES (
                    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    url TEXT,
                    data BLOB
                );
            """)
        print('Database connected. ')
        return con
    except Exception as e:
        print(e)

con = create_database_table()

def insert_reccords_pandas(df):
    df.to_sql('URLS', con, if_exists='append', index=False, index_label='id')
    con.commit()

def execute_sql(sql):
    df = pd.read_sql(sql,con)
    return df 

def dedupe_urls(df):
    database_df = execute_sql("SELECT * FROM URLS")
    merged_df = df.merge(database_df, how='left', on='url', suffixes=('', '_historical'))
    filtered_df = merged_df[merged_df['query_historical'].isnull()][['id','url','query','processed']]
    return filtered_df 

def insert_reccords(con, data, table):
    if table == 'IMAGES': 
        sql = 'INSERT INTO IMAGES (url, data) values(?, ?)'
    else:
         sql = 'INSERT INTO URLS (url, query, processed) values(?, ?, ?)'
    with con:
        con.executemany(sql, data)

def show_img(img_data):
    image = Image.open(io.BytesIO(img_data))
    image.show() 

def save_iamge_data_v2_helper(df):
    for index, data in df.iterrows():
        try:
            url = data['url']
            img_data = requests.get(url, timeout=15).content
            yield (url, img_data)
        except Exception as e:
            print(e)
        pass 

def update_processed_urls(data):
    try:
        unprocessed_df = execute_sql("SELECT * FROM URLS WHERE processed = 0")
        processed_df = execute_sql("SELECT * FROM URLS WHERE processed = 0")
        st.write(f"BEFORE: unprocessed URLs {unprocessed_df.shape[0]}")
        st.write(f"BEFORE: processed URLs {processed_df.shape[0]}")
        urls = [item[0] for item in data]
        st.write(f'URLs to process {len(urls)}')
        with con:
            url_str = "".join([f"'{url}'," for url in urls])[:-1]
            con.execute(f"""
                UPDATE URLS 
                SET processed = 1
                WHERE
                    url in ({url_str})
            """)
        st.write(f"AFTER: unprocessed URLs {unprocessed_df.shape[0]}")
        st.write(f"AFTER: processed URLs {processed_df.shape[0]}")
    except Exception as e:
        print(e)

def print_database_processed_helper(unprocessed_df, processed_df, label):
    st.write(f"{label}: unprocessed URLs {unprocessed_df.shape[0]}")
    st.write(f"{label}: processed URLs {processed_df.shape[0]}")

def query_database_processed_helper():
    unprocessed_df = execute_sql("SELECT * FROM URLS WHERE processed = 0")
    processed_df = execute_sql("SELECT * FROM URLS WHERE processed = 1")
    return unprocessed_df, processed_df

def update_processed_urls_batch(data):
    try:
        urls = [item[0] for item in data]
        # st.write(f'URLs to process {len(urls)}')
        with con:
            url_str = "".join([f"'{url}'," for url in urls])[:-1]
            con.execute(f"""
                UPDATE URLS 
                SET processed = 1
                WHERE
                    url in ({url_str})
            """)
    except Exception as e:
        print(e)


def create_image_directory():
    now = datetime.now()
    time_stamp = now.strftime("%Y%m%d%H%M%S")
    try: 
        file_path = f"{filepath}{time_stamp}/"
        os.makedirs(file_path+f'/train', exist_ok = True)
        os.makedirs(file_path+f'/test', exist_ok = True)
        os.makedirs(file_path+f'/validate', exist_ok = True)
        st.write(f'Directory created: {file_path}')
        return file_path
    except Exception as e:
        print(e)
    return ''

def save_iamge_data_all(df):
    data = [x for x in save_iamge_data_v2_helper(df)]
    insert_reccords(con, data, 'IMAGES')
    update_processed_urls(data)
    st.write(f'Number of URLs processed ')

def batcher(iterable, batch_size):
    iterator = iter(iterable)
    while batch := list(islice(iterator, batch_size)):
        yield batch

def get_image_data(url):
    return url, requests.get(url, timeout=15).content

async def process_batch():
    if 'batch' in st.session_state:
        tasks = []
        for url in st.session_state.batch:
            tasks.append(asyncio.create_task(asyncio.to_thread(get_image_data,url)))
        result = await asyncio.gather(*tasks)
        return result

def save_iamge_data_batch(df):
    urls = list(df.url.unique())
    for batch in list(batcher(urls, BATCH_SIZE)):
        st.session_state['batch'] = batch
        images = asyncio.run(process_batch())
        insert_reccords(con, images, 'IMAGES')
        update_processed_urls_batch(images)

def image_save_to_dir_helper(file_path,df):
    for index, data in df.iterrows():
        with open(f"{file_path}{data['id']}_image.jpg", 'wb') as f: 
            f.write(data['data'])

def export_images_and_save(file_path,images):
    images.drop_duplicates('data',inplace=True)

    train, validate, test = np.split(images.sample(frac=1, random_state=42), [int((1-(TEST_SPLIT_FRAC+VALIDATE_SPLIT_FRAC))*len(images)), \
                                                                              int((1-(TEST_SPLIT_FRAC))*len(images))])
    st.write(f"Dataset splits: ")
    st.write(f"train: {train.shape[0]} | validate: {validate.shape[0]} | test: {test.shape[0]}")
    image_save_to_dir_helper(file_path+f'train/',train)
    image_save_to_dir_helper(file_path+f'test/',test)
    image_save_to_dir_helper(file_path+f'validate/',validate)

if __name__ =="__main__":
    pass 