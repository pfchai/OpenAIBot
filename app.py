# -*- coding: utf-8 -*-

import os
import logging

from flask import Flask
from flask import request, jsonify

#  from .bot.feishu import FeishuBot
from .bot.feishu_chatgpt import FeishuChatGPTBot


logging.basicConfig(level=logging.DEBUG)

# logger = logging.getLogger(__name__)

# formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
# stream_handler = logging.StreamHandler()
# stream_handler.setLevel(logging.INFO)
# stream_handler.setFormatter(formatter)
# logger.addHandler(stream_handler)


APP_ID = os.getenv('APP_ID')
APP_SECRET = os.getenv('APP_SECRET')
ENCRYPT_KEY = os.getenv('ENCRYPT_KEY')

#  bot = FeishuBot(app_id=APP_ID, app_secret=APP_SECRET, encrypt_key=ENCRYPT_KEY)
bot = FeishuChatGPTBot(app_id=APP_ID, app_secret=APP_SECRET, encrypt_key=ENCRYPT_KEY)

app = Flask(__name__)
app.config['timeout'] = 120
app.logger.setLevel(logging.DEBUG)


@app.route('/', methods=['GET', 'POST'])
def hello_world():
    if request.method == 'POST':
        print(request)
        res = bot.handle(request)
        print(res)
        if isinstance(res, str):
            return res
        else:
            return jsonify(res)

    return '<p>Hello, World!</p>'


if __name__ == '__main__':
    handler = logging.FileHandler('flask.log', encoding='UTF-8')
    handler.setLevel(logging.DEBUG)
    logging_format = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(lineno)s - %(message)s')
    handler.setFormatter(logging_format)
    app.logger.addHandler(handler)
    app.run()
