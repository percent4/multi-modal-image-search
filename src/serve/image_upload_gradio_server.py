# -*- coding: utf-8 -*-
# @place: Pudong, Shanghai
# @file: image_upload_gradio_server.py
# @time: 2024/2/4 23:41
import json
from datetime import datetime as dt

import requests
import gradio as gr
from PIL import Image
from io import BytesIO
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


def insert_es_data(url, title, desc, tag):
    doc = {
        "url": url,
        "title": title,
        "description": desc,
        "tag": tag,
        "insert_time": dt.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    es_client.index(index="image-search", document=doc)
    print("insert into es successfully!")


def get_image_desc(image_url, image_tag):
    # load image
    image = load_image(image_url)
    # get image title and description
    url = "http://model_url:50075/img_desc"
    payload = json.dumps({"url": image_url})
    headers = {'Content-Type': 'application/json'}
    response = requests.request("POST", url, headers=headers, data=payload)
    result = response.json()
    # insert into es
    insert_es_data(url=image_url, tag=image_tag, title=result["title"], desc=result["desc"])
    return image, result["title"], result["desc"]


with gr.Blocks() as demo:
    with gr.Row():
        with gr.Column():
            checkout_group = gr.CheckboxGroup(choices=["LLaVA 1.6"], value="LLaVA 1.6", label='models')
            user_input = gr.TextArea(lines=5, placeholder="Enter the url of an image", label="image url")
            tags = gr.TextArea(lines=1, placeholder="Enter the tags of an image", label="image tag")
        with gr.Column():
            image_box = gr.inputs.Image()
            title_output = gr.TextArea(lines=1, label='image title')
            desc_output = gr.TextArea(lines=5, label='image description')
            submit = gr.Button("Submit")
    submit.click(fn=get_image_desc,
                 inputs=[user_input, tags],
                 outputs=[image_box, title_output, desc_output])

demo.launch()
