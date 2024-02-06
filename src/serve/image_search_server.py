# -*- coding: utf-8 -*-
# @place: Pudong, Shanghai
# @file: image_search_server.py
# @time: 2024/2/6 10:36
import json
import requests
import gradio as gr
from PIL import Image
from io import BytesIO
from datetime import datetime as dt
from elasticsearch import Elasticsearch

# 连接Elasticsearch
es_client = Elasticsearch("http://localhost:9200")


def load_image(image_file):
    if image_file.startswith('http://') or image_file.startswith('https://'):
        response = requests.get(image_file)
        image = Image.open(BytesIO(response.content)).convert('RGB')
    else:
        image = Image.open(image_file).convert('RGB')
    return image


def get_image_desc(image_url):
    # get image title and description
    url = "http://35.89.147.116:50075/img_desc"
    payload = json.dumps({"url": image_url})
    headers = {'Content-Type': 'application/json'}
    response = requests.request("POST", url, headers=headers, data=payload)
    result = response.json()
    return result["title"], result["desc"]


def insert_es_data(url, title, desc):
    # check if url is already in es
    dsl = {
        'query': {
            'match': {
                'url': url
            }
        },
        "size": 10
    }
    search_result = es_client.search(index='image-search', body=dsl)
    if search_result['hits']['hits']:
        url_result = [_['_source']['url'] for _ in search_result['hits']['hits']]
        if url in url_result:
            print("the url is already in ElasticSearch!")
            return
    doc = {
        "url": url,
        "title": title,
        "description": desc,
        "tag": "search",
        "insert_time": dt.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    es_client.index(index="image-search", document=doc)
    print("insert into es successfully!")


def image_search(query):
    result = []
    if query.startswith("http"):
        # 对image的title进行全文检索
        image_title, image_desc = get_image_desc(query)
        print("image info: ", repr(image_title), repr(image_desc))
        insert_es_data(query, image_title, image_desc)
        dsl = {
            'query': {
                'match': {
                    'title': image_title
                }
            },
            "size": 3
        }
    else:
        # 对query进行全文搜索
        queries = query.split()
        dsl = {
              "query": {
                "bool": {
                  "must": [
                    {"match": {"description": _}} for _ in queries
                  ]
                }
              },
              "size": 3
        }
    search_result = es_client.search(index='image-search', body=dsl)
    if search_result['hits']['hits']:
        result = [_['_source']['url'] for _ in search_result['hits']['hits']]
    print('search result', result)
    images = [load_image(url) for url in result]
    return images


with gr.Blocks() as demo:
    with gr.Row():
        with gr.Column():
            user_input = gr.TextArea(lines=1, placeholder="Enter search word", label="Search")
        with gr.Column():
            image_box = gr.Gallery(label="image").style(height='auto', columns=4)
            submit = gr.Button("Search")
    submit.click(fn=image_search,
                 inputs=user_input,
                 outputs=image_box)

demo.launch()
