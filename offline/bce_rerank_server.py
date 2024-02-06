# -*- coding: utf-8 -*-
# @place: Pudong, Shanghai
# @file: bce_rerank_server.py
# @time: 2024/2/6 17:06
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from operator import itemgetter
from sentence_transformers import CrossEncoder


app = FastAPI()
# init rerank model
model = CrossEncoder('/data-ai/usr/lmj/models/bce-reranker-base_v1', max_length=512)


class SentencePair(BaseModel):
    text1: str
    text2: str


class Sentences(BaseModel):
    texts: list[SentencePair]


@app.get('/')
def home():
    return 'hello world'


@app.post('/rerank')
def get_embedding(sentence_pairs: Sentences):
    scores = model.predict([[pair.text1, pair.text2] for pair in sentence_pairs.texts]).tolist()
    result = [[scores[i], sentence_pairs.texts[i].text1, sentence_pairs.texts[i].text2] for i in range(len(scores))]
    sorted_result = sorted(result, key=itemgetter(0), reverse=True)
    return {"result": sorted_result}


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=50074)
