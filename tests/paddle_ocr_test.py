# -*- coding: utf-8 -*-
# @place: Pudong, Shanghai
# @file: paddle_ocr_test.py
# @time: 2024/2/8 13:54
import requests
import json
import cv2
import base64


def cv2_to_base64(image):
    data = cv2.imencode('.jpg', image)[1]
    return base64.b64encode(data.tobytes()).decode('utf8')


def image_ocr(image_path):
    data = {'images': [cv2_to_base64(cv2.imread(image_path))]}
    headers = {"Content-type": "application/json"}
    url = "http://localhost:50076/predict/ch_pp-ocrv3"
    r = requests.post(url=url, headers=headers, data=json.dumps(data))
    return r.json()["results"]


if __name__ == '__main__':
    image_path_test = "/Users/admin/PycharmProjects/multi-modal-image-search/docs/bank.jpeg"
    res = image_ocr(image_path=image_path_test)
    import pprint
    pprint.pprint(res)
