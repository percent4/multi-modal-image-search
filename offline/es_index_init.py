# -*- coding: utf-8 -*-
# @place: Pudong, Shanghai
# @file: es_index_init.py
# @time: 2024/2/5 15:59
from elasticsearch import Elasticsearch

# 连接Elasticsearch
es_client = Elasticsearch("http://localhost:9200")

# 创建新的ES index
mapping = {
    'properties': {
        'url': {
            'type': 'text'
        },
        'tag': {
            'type': 'keyword'
        },
        'description': {
            'type': 'text',
            'analyzer': 'ik_smart',
            'search_analyzer': 'ik_smart'
        },
        'title': {
            'type': 'text'
        },
        "insert_time": {
            "type": "date",
            "format": "yyyy-MM-dd HH:mm:ss"
        },
        'ocr_result': {
            'type': 'text'
        }
    }
}

es_client.indices.create(index='image-search-ocr', ignore=400)
result = es_client.indices.put_mapping(index='image-search-ocr', body=mapping)
print(result)
