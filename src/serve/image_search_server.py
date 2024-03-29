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
from uuid import uuid4

# 连接Elasticsearch
es_client = Elasticsearch("http://localhost:9200")


def load_image(image_file):
    if image_file.startswith('http://') or image_file.startswith('https://'):
        response = requests.get(image_file)
        image = Image.open(BytesIO(response.content)).convert('RGB')
    else:
        image = Image.open(image_file).convert('RGB')

    return image


# check if url is already in es
def is_image_in_es(url):
    dsl = {
        'query': {
            'match': {
                'url': url
            }
        },
        "size": 5
    }
    search_result = es_client.search(index='image-search-ocr', body=dsl)
    if search_result['hits']['hits']:
        url_result = {_['_source']['url']: _['_id'] for _ in search_result['hits']['hits']}
        if url in url_result:
            print("the url is already in ElasticSearch!")
            return True, url_result[url]
    print("the url is not in ElasticSearch!")
    return False, None


def get_image_desc(image_url):
    image_exists, _id = is_image_in_es(image_url)
    if image_exists:
        result = es_client.get(index="image-search-ocr", id=_id)
        print("get image info by ElasticSearch!")
        return result["_source"]["title"], result["_source"]["description"]
    else:
        # get image title and description
        url = "http://localhost:50075/img_desc"
        payload = json.dumps({"url": image_url})
        headers = {'Content-Type': 'application/json'}
        response = requests.request("POST", url, headers=headers, data=payload)
        result = response.json()
        print("get image info by LLaVA model!")
        return result["title"], result["desc"]


def insert_es_data(url, title, desc):
    image_exists, _id = is_image_in_es(url)
    if not image_exists:
        doc = {
            "url": url,
            "title": title,
            "description": desc,
            "tag": "search",
            "insert_time": dt.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        es_client.index(index="image-search-ocr", document=doc)
        print(f"insert {url} into es successfully!")


def get_rerank_result(text_list):
    url = "http://localhost:50074/rerank"
    payload = json.dumps({
        "texts": [
            {
                "text1": text[0],
                "text2": text[1]
            }
            for text in text_list
        ]
    })
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    print("rerank result: ")
    for _ in response.json()['result']:
        print(_)
    return response.json()['result']


def image_search_by_http(query_str):
    result = []
    # 对image的title进行全文检索
    image_title, image_desc = get_image_desc(query_str)
    print("image info: ", repr(image_title), repr(image_desc))
    insert_es_data(query_str, image_title, image_desc)
    dsl = {
        'query': {
            'match': {
                'description': image_desc
            }
        },
        "size": 10
    }
    search_result = es_client.search(index='image-search-ocr', body=dsl)
    if search_result['hits']['hits']:
        es_search_result = {_['_source']['description'][:200]: _['_source']['url'] for _ in
                            search_result['hits']['hits']}
        desc_title_dict = {_['_source']['description'][:200]: _['_source']['title'] for _ in
                           search_result['hits']['hits']}
        # get title rerank result
        text_list = [[image_desc[:200], key] for key in es_search_result.keys()]
        rerank_result = get_rerank_result(text_list=text_list)
        # get at most 5 similar images
        i = 0
        for record in rerank_result:
            score, image_desc, other_desc = record
            if image_desc != other_desc and score > 0.4:
                i += 1
                result.append([es_search_result[other_desc], desc_title_dict[other_desc]])
                if i > 4:
                    break
    return result


def image_search_by_text(query_str):
    result = []
    # 对query进行全文搜索
    queries = query_str.split()
    dsl = {
        "query": {
            "bool": {
                "must": [
                    {"match": {"description": _}} for _ in queries
                ]
            }
        },
        "size": 5
    }
    search_result = es_client.search(index='image-search-ocr', body=dsl)
    if search_result['hits']['hits']:
        result = [[_['_source']['url'], _['_source']['title']] for _ in search_result['hits']['hits']]
    print('search result: ', result)
    return result


def image_search(query):
    user_image_image = None
    if query.startswith("http"):
        user_image_image = query
        result = image_search_by_http(query)
    else:
        result = image_search_by_text(query)

    images = [load_image(record[0]) for record in result]
    if len(images) >= 3:
        images = images[:3]
    else:
        for _ in range(3 - len(images)):
            images.append(None)
    return user_image_image, images[0], images[1], images[2]


if __name__ == '__main__':
    with gr.Blocks() as demo:
        with gr.Row():
            with gr.Column(scale=0.3):
                user_input = gr.TextArea(lines=1, placeholder="Enter search word", label="Search")
                user_input_image = gr.Image()
            with gr.Column(scale=0.2):
                search_image1 = gr.Image(type='pil', height=200)
                search_image2 = gr.Image(type='pil', height=200)
                search_image3 = gr.Image(type='pil', height=200)
                submit = gr.Button("Search")
        submit.click(fn=image_search,
                     inputs=user_input,
                     outputs=[user_input_image, search_image1, search_image2, search_image3])
    demo.launch(server_name="0.0.0.0", server_port=7680)
