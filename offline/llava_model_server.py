# -*- coding: utf-8 -*-
# @place: Pudong, Shanghai
# @file: llava_model_server.py
# @time: 2024/2/18 15:45
import torch

from llava.constants import IMAGE_TOKEN_INDEX, DEFAULT_IMAGE_TOKEN, DEFAULT_IM_START_TOKEN, DEFAULT_IM_END_TOKEN
from llava.conversation import conv_templates, SeparatorStyle
from llava.model.builder import load_pretrained_model
from llava.utils import disable_torch_init
from llava.mm_utils import process_images, tokenizer_image_token, get_model_name_from_path

from PIL import Image

import requests
from PIL import Image
from io import BytesIO
from transformers import TextStreamer
from pydantic import BaseModel
import uvicorn
from fastapi import FastAPI


# Model
disable_torch_init()

model_path = "/data-ai/usr/lmj/models/llava-v1.6-34b"
model_name = get_model_name_from_path(model_path)
tokenizer, model, image_processor, context_len = load_pretrained_model(model_path, None, model_name, False, False, device="cuda")


def load_image(image_file):
    if image_file.startswith('http://') or image_file.startswith('https://'):
        response = requests.get(image_file)
        image = Image.open(BytesIO(response.content)).convert('RGB')
    else:
        image = Image.open(image_file).convert('RGB')
    return image


def model_infer(image_file, inp):
    if "llama-2" in model_name.lower():
        conv_mode = "llava_llama_2"
    elif "mistral" in model_name.lower():
        conv_mode = "mistral_instruct"
    elif "v1.6-34b" in model_name.lower():
        conv_mode = "chatml_direct"
    elif "v1" in model_name.lower():
        conv_mode = "llava_v1"
    elif "mpt" in model_name.lower():
        conv_mode = "mpt"
    else:
        conv_mode = "llava_v0"

    conv = conv_templates[conv_mode].copy()
    if "mpt" in model_name.lower():
        roles = ('user', 'assistant')
    else:
        roles = conv.roles

    image = load_image(image_file)
    image_size = image.size
    # Similar operation in model_worker.py
    image_tensor = process_images([image], image_processor, model.config)
    if type(image_tensor) is list:
        image_tensor = [image.to(model.device, dtype=torch.float16) for image in image_tensor]
    else:
        image_tensor = image_tensor.to(model.device, dtype=torch.float16)

    if image is not None:
        # first message
        if model.config.mm_use_im_start_end:
            inp = DEFAULT_IM_START_TOKEN + DEFAULT_IMAGE_TOKEN + DEFAULT_IM_END_TOKEN + '\n' + inp
        else:
            inp = DEFAULT_IMAGE_TOKEN + '\n' + inp
        conv.append_message(conv.roles[0], inp)
        image = None
    else:
        # later messages
        conv.append_message(conv.roles[0], inp)
    conv.append_message(conv.roles[1], None)
    prompt = conv.get_prompt()

    input_ids = tokenizer_image_token(prompt, tokenizer, IMAGE_TOKEN_INDEX, return_tensors='pt').unsqueeze(0).to(model.device)
    stop_str = conv.sep if conv.sep_style != SeparatorStyle.TWO else conv.sep2
    keywords = [stop_str]
    streamer = TextStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)

    with torch.inference_mode():
        output_ids = model.generate(
            input_ids,
            images=image_tensor,
            image_sizes=[image_size],
            do_sample=True,
            temperature=0.1,
            max_new_tokens=1024,
            streamer=streamer,
            use_cache=True)

    outputs = tokenizer.decode(output_ids[0, 1:-1]).strip()
    conv.messages[-1][-1] = outputs
    print("\n", {"prompt": prompt, "outputs": outputs}, "\n")
    return outputs


app = FastAPI()


class ImageInput(BaseModel):
    url: str
    ocr_result: str


@app.get('/')
def home():
    return 'hello world'


@app.post('/img_desc')
def image_desc(image_input: ImageInput):
    title_string = "请为这张图片生成一个中文标题。" if not image_input.ocr_result else f'这张图片中的文字为"{image_input.ocr_result}"。请为这张图片生成一个中文标题。'
    title_output = model_infer(image_input.url, title_string)
    desc_string = "请详细描述这张图片中的内容。" if not image_input.ocr_result else f'这张图片中的文字为"{image_input.ocr_result}"。请详细描述这张图片中的内容。'
    desc_output = model_infer(image_input.url, desc_string)
    return {"url": image_input.url, "title": title_output, "desc": desc_output}


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=50075)
