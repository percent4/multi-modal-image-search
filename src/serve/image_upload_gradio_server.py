# -*- coding: utf-8 -*-
# @place: Pudong, Shanghai
# @file: image_upload_gradio_server.py
# @time: 2024/2/4 23:41
import json
import uuid
from datetime import datetime as dt
import cv2
import base64
import requests
import gradio as gr
from PIL import Image
from io import BytesIO
from elasticsearch import Elasticsearch
from urllib.request import urlretrieve

# 连接Elasticsearch
es_client = Elasticsearch("http://localhost:9200")


def load_image(image_file):
    if image_file.startswith('http://') or image_file.startswith('https://'):
        response = requests.get(image_file)
        image = Image.open(BytesIO(response.content)).convert('RGB')
    else:
        image = Image.open(image_file).convert('RGB')
    return image


def cv2_to_base64(image):
    data = cv2.imencode('.jpg', image)[1]
    return base64.b64encode(data.tobytes()).decode('utf8')


def image_ocr(image_url):
    # download image by url
    image_path = f'../data/{str(uuid.uuid4())}.jpg'
    urlretrieve(image_url, image_path)
    # get ocr result
    data = {'images': [cv2_to_base64(cv2.imread(image_path))]}
    headers = {"Content-type": "application/json"}
    url = "http://localhost:50076/predict/ch_pp-ocrv3"
    r = requests.post(url=url, headers=headers, data=json.dumps(data))
    if r.json()["results"]:
        return "\n".join([ocr_record["text"].strip() for ocr_record in r.json()["results"][0]["data"]])
    else:
        return ""


def insert_es_data(url, tag, title, desc, ocr_result):
    doc = {
        "url": url,
        "title": title,
        "description": desc,
        "tag": tag,
        "insert_time": dt.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ocr_result": ocr_result
        }
    es_client.index(index="image-search-ocr", document=doc)
    print("insert into es successfully!")


def get_image_desc(ocr_choice, image_url):
    if not ocr_choice:
        ocr_result = ""
    else:
        ocr_result = image_ocr(image_url=image_url)
        print("ocr result: ", repr(ocr_result))
    # load image
    image = load_image(image_url)
    # get image title and description
    url = "http://localhost:50075/img_desc"
    payload = json.dumps({"url": image_url, "ocr_result": ocr_result})
    headers = {'Content-Type': 'application/json'}
    response = requests.request("POST", url, headers=headers, data=payload)
    result = response.json()
    return image, ocr_result, result["title"], result["desc"]


with gr.Blocks() as demo:
    with gr.Row():
        with gr.Column():
            checkout_group = gr.CheckboxGroup(choices=["LLaVA 1.6"], value="LLaVA 1.6", label='models')
            ocr_group = gr.CheckboxGroup(choices=["PaddleOCR"], label='OCR')
            user_input = gr.TextArea(lines=5, placeholder="Enter the url of an image", label="image url")
            tags = gr.TextArea(lines=1, placeholder="Enter the tags of an image", label="image tag")
        with gr.Column():
            image_box = gr.Image()
            ocr_output = gr.TextArea(lines=2, label='OCR result')
            title_output = gr.TextArea(lines=1, label='image title')
            desc_output = gr.TextArea(lines=5, label='image description')
            submit = gr.Button("Submit")
            insert_data = gr.Button("Insert")
    submit.click(fn=get_image_desc,
                 inputs=[ocr_group, user_input],
                 outputs=[image_box, ocr_output, title_output, desc_output])
    insert_data.click(fn=insert_es_data,
                      inputs=[user_input, tags, title_output, desc_output, ocr_output])

demo.launch()
