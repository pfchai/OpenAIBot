# -*- coding: utf-8 -*-

import os
import logging
import xml.etree.cElementTree as ET
from concurrent.futures import ThreadPoolExecutor

import requests

from .client import Client
from ...bot import GPT3ChatBot, YDLGPTBot


logger = logging.getLogger(__name__)

thread_pool = ThreadPoolExecutor(max_workers=16)


class BaseServer():

    def handle(self):
        raise NotImplementedError


class EchoServer(BaseServer):
    def __init__(self, config):
        self.client = Client(config)

    def handle_p2p(self, tree, request):
        """
        单聊消息处理
        """

        content = tree.find('Content').text
        to_user = tree.find('ToUserName').text
        from_user = tree.find('FromUserName').text
        create_time = tree.find('CreateTime').text
        # msg_type = tree.find('MsgType').text

        resp_data = f'to_user: {to_user}, from_user: {from_user}, create_time: {create_time}, content: {content}'

        self.client.send_msg(resp_data, from_user)
        return ''

    def handle(self, request):

        msg = self.client.decrypt_msg(request)
        if msg is None:
            return 'None msg'

        tree = ET.fromstring(msg)
        if not tree:
            return 'None'

        return self.handle_p2p(tree, request)


class ChatGPTServer(BaseServer):
    def __init__(self, config):
        self.client = Client(config)
        self.chatgpt_url = config['CUSTOM_CHATGPT_URL']

    def ask(self, content, to_user, from_user):
        headers = {'Content-Type': 'application/json'}
        body = {'botDTO': {
            'appId': 'yunjiaoqiwei',
            'userId': to_user,
            'conversationId': from_user,
            'input': content,
            'scene': 'psy-chat-bot-common'
        }}

        response = requests.post(self.chatgpt_url, headers=headers, json=body)
        res_data = response.json()
        logger.debug('chatgpt response', res_data)
        reply_text = res_data['data']

        self.client.send_msg(reply_text, from_user)

    def handle_p2p(self, tree, request):
        """
        单聊消息处理
        """

        content = tree.find('Content').text
        to_user = tree.find('ToUserName').text
        from_user = tree.find('FromUserName').text

        thread_pool.submit(self.ask, content, to_user, from_user)

        return ''

    def handle(self, request):

        msg = self.client.decrypt_msg(request)
        if msg is None:
            return 'None msg'

        tree = ET.fromstring(msg)
        if not tree:
            return 'None'

        return self.handle_p2p(tree, request)


class YDLGPTServer(BaseServer):
    def __init__(self, config):
        self.client = Client(config)
        self.chatbot = YDLGPTBot(url=config['CUSTOM_CHATGPT_URL'], app_id=config['YDL_APP_ID'], scene=config['YDL_SCENE'])

        self.chatgpt_url = config['CUSTOM_CHATGPT_URL']

    def ask(self, content, to_user, from_user):
        chatgpt_res_text = self.chatbot.ask(content, sender_id=to_user, chat_id=from_user)
        self.client.send_msg(chatgpt_res_text, from_user)

    def handle_p2p(self, tree, request):
        """
        单聊消息处理
        """

        content = tree.find('Content').text
        to_user = tree.find('ToUserName').text
        from_user = tree.find('FromUserName').text

        thread_pool.submit(self.ask, content, to_user, from_user)

        return ''

    def handle(self, request):

        msg = self.client.decrypt_msg(request)
        if msg is None:
            return 'None msg'

        tree = ET.fromstring(msg)
        if not tree:
            return 'None'

        return self.handle_p2p(tree, request)