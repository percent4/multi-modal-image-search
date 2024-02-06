本项目使用LLaVA 1.6多模态模型实现以文搜图和以图搜图功能。

### 多模态模型

LLaVA 1.6

Github网址：https://github.com/haotian-liu/LLaVA/tree/main

DEMO网址：https://llava.hliu.cc/

### 实现原理

待补充

### 图片上传

src/serve/image_upload_gradio_server.py

![image-search-图片上传.png](https://s2.loli.net/2024/02/06/bJCqkv4LVgminpy.png)

### 使用文字搜图

src/serve/image_search_server.py

- 单个短语

![image-search-单个短语.png](https://s2.loli.net/2024/02/06/wZPxnagSDf5H2sv.png)

- 多个短语

![image-search-多个短语.png](https://s2.loli.net/2024/02/06/BGANMebhZQwnUOc.png)

### 以图搜图

![image-search-以图搜图1.png](https://s2.loli.net/2024/02/06/ZFPMJTvtgYna31f.png)

![image-search-以图搜图2.png](https://s2.loli.net/2024/02/06/B8NlIKtx5vJzgSV.png)

![image-search-以图搜图3.png](https://s2.loli.net/2024/02/06/Mx2954wd3RDUzZ8.png)
