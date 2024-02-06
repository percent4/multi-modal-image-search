# -*- coding: utf-8 -*-
# @place: Pudong, Shanghai
# @file: es_index_init.py
# @time: 2024/2/5 15:59
from elasticsearch import Elasticsearch

# 连接Elasticsearch
es_client = Elasticsearch([{'host': 'localhost', 'port': 9200}])

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
        }
    }
}

es_client.indices.create(index='image-search', ignore=400)
result = es_client.indices.put_mapping(index='image-search', body=mapping)
print(result)
