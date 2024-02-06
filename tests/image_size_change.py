# -*- coding: utf-8 -*-
# @place: Pudong, Shanghai
# @file: image_size_change.py
# @time: 2024/2/6 21:54
import gradio as gr
from PIL import Image
import numpy as np


# 定义一个函数来调整图片尺寸并返回
def resize_image(image, width, height):
    # 将上传的图片转换为Pillow图像
    img = Image.fromarray(image.astype('uint8'), 'RGB')
    print(img.size)
    width = img.size[0]  # 获取宽度
    height = img.size[1]  # 获取高度
    resized_image = img.resize((int(width * 0.3), int(height * 0.3)))
    # 调整图片尺寸
    # resized_image = img.resize((int(width), int(height)))
    # 将Pillow图像转换回numpy数组以便Gradio可以显示
    return np.array(resized_image)


# 创建Gradio接口
iface = gr.Interface(fn=resize_image,
                     inputs=[gr.inputs.Image(shape=(200, 200)), gr.inputs.Slider(minimum=100, maximum=1000, default=200, label="Width"), gr.inputs.Slider(minimum=100, maximum=1000, default=200, label="Height")],
                     outputs=gr.Image(shape=(80, 80), type="numpy", label="Resized Image"),
                     description="Upload an image to resize it to your desired dimensions.")

# 启动应用
iface.launch()
