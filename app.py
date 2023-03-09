# -*- coding: utf-8 -*-

import yaml
import logging
from logging.config import dictConfig

from flask import Flask
from flask import request, jsonify

from .platform.feishu import EchoServer as FeishuEchoServer
from .platform.feishu import ChatGPTServer as FeishuChatGPTServer
from .platform.feishu import YDLGPTServer as FeishuYDLGPTServer
from .platform.wework import EchoServer as WeworkEchoServer
from .platform.wework import ChatGPTServer as WeworkChatGPTServer


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


def create_server(app, feishu_bots, wework_bots):
    if feishu_bots:
        @app.route('/feishu/<name>', methods=['GET', 'POST'])
        def feishu_server(name):
            if name not in feishu_bots:
                return 'url error'
            
            if request.method == 'POST':
                app.logger.info(request)
                res = feishu_bots[name].handle(request)
                app.logger.info(res)
                if isinstance(res, str):
                    return res
                else:
                    return jsonify(res)

            return '<p>Hello, World!</p>'
    
    if wework_bots:
        @app.route('/wework/<name>', methods=['GET', 'POST'])
        def wework_server(name):
            if name not in wework_bots:
                return 'url error'
            
            if request.method == 'POST':
                app.logger.info(request)
                res = wework_bots[name].handle(request)
                app.logger.info(res)
                if isinstance(res, str):
                    return res
                else:
                    return jsonify(res)
            else:
                return wework_bots[name].client.vertify_url(request)


def create_bots():
    feishu_bots, wework_bots = {}, {}

    with open('config.yaml') as f:
        configs = yaml.load_all(f, Loader=yaml.FullLoader)
        for config in configs:
            if config['platform'] == 'feishu':
                if config['bot'] not in ('echo', 'chatgpt', 'ydl_gpt'):
                    raise

                if config['bot'] == 'echo':
                    feishu_bots[config['name']] = FeishuEchoServer(config)
                if config['bot'] == 'chatgpt':
                    feishu_bots[config['name']] = FeishuChatGPTServer(config)
                if config['bot'] == 'ydl_gpt':
                    feishu_bots[config['name']] = FeishuYDLGPTServer(config)

            if config['platform'] == 'wework':
                if config['bot'] not in ('echo', 'chatgpt'):
                    raise

                if config['bot'] == 'echo':
                    wework_bots[config['name']] = WeworkEchoServer(config)
                if config['bot'] == 'chatgpt':
                    wework_bots[config['name']] = WeworkChatGPTServer(config)

    return feishu_bots, wework_bots


app = Flask(__name__)
app.config['timeout'] = 120
app.logger.setLevel(logging.DEBUG)

feishu_bots, wework_bots = create_bots()
create_server(app, feishu_bots, wework_bots)