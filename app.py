# -*- coding: utf-8 -*-

import logging
from logging.config import dictConfig

from flask import Flask
from flask import request, jsonify

from .platform.feishu.server import ChatGPTServer as FeishuChatGPTBot
from .platform.wework.server import ChatGPTServer as WeworkChatGPTBot


dictConfig({
    'version': 1,
    'formatters': {
        'default': {
            'format': '%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'default'
        }
    },
    'root': {
        'level': 'DEBUG',
        'handlers': ['console'],
    }
})


feishu_bot = FeishuChatGPTBot()
wework_bot = WeworkChatGPTBot()

app = Flask(__name__)
app.config['timeout'] = 120
app.logger.setLevel(logging.DEBUG)


@app.route('/feishu', methods=['GET', 'POST'])
def feishu_server():
    if request.method == 'POST':
        app.logger.info(request)
        res = feishu_bot.handle(request)
        app.logger.info(res)
        if isinstance(res, str):
            return res
        else:
            return jsonify(res)

    return '<p>Hello, World!</p>'


@app.route('/wework', methods=['GET', 'POST'])
def wework_server():
    if request.method == 'POST':
        app.logger.info(request)
        res = wework_bot.handle(request)
        app.logger.info(res)
        if isinstance(res, str):
            return res
        else:
            return jsonify(res)
    else:
        return wework_bot.client.vertify_url(request)
