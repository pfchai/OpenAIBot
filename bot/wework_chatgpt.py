# -*- coding: utf-8 -*-

import os
import logging
from concurrent.futures import ThreadPoolExecutor

import requests

from .wework import WeworkBot


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


thread_pool = ThreadPoolExecutor(max_workers=16)


class WeworkChatGPTBot(WeworkBot):
    def __init__(self):
        super().__init__()
        self.chatgpt_url = os.getenv('CUSTOM_CHATGPT_URL')

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

        self.send_msg(reply_text, from_user)

    def handle_p2p(self, tree, request):
        """
        单聊消息处理
        """

        content = tree.find('Content').text
        to_user = tree.find('ToUserName').text
        from_user = tree.find('FromUserName').text

        thread_pool.submit(self.ask, content, to_user, from_user)

        return ''
