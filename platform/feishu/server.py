# -*- coding: utf-8 -*-

import os
import re
import json
import logging

import openai

from .client import Client
from ...bot.gpt3.gpt3_chat_bot import GPT3ChatBot as Chatbot


logger = logging.getLogger(__name__)
API_KEY = os.getenv('OPENAI_API_KEY')
openai.api_key = API_KEY


class BaseServer():

    def handle(self):
        """
        处理消息
        """
        raise NotImplementedError


class EchoServer(BaseServer):

    def __init__(self):
        self.is_valid_message = False

        self.client = Client()

        self.message_ids = set()

    def handle_p2p(self, message):
        """
        单聊消息处理
        """
        msg = message['event']['message']
        msg_content = json.loads(msg['content'])
        msg_text = msg_content['text']

        self.client.reply_text(msg['message_id'], msg['chat_id'], '收到消息：' + msg_text)
        return 'success'

    def handle_group(self, message):
        """
        处理群消息
        """
        msg = message['event']['message']
        msg_content = json.loads(msg['content'])

        at_key = self.client.is_be_at(msg)
        if at_key is False:
            return 'ignore group message'

        msg_text = msg_content['text'].replace(at_key + ' ', '')
        self.client.reply_text(msg['message_id'], msg['chat_id'], '收到消息：' + msg_text)
        return 'success'

    def handle(self, request):
        if self.is_valid_message:
            if not self.client.valid(request):
                logger.info('received message is invalid')

        received_message = self.client.parse_message(request)
        logger.debug(received_message)
        if not received_message:
            logger.error('received message is None')

        # 飞书认证逻辑
        if 'challenge' in received_message:
            return {'challenge': received_message['challenge']}

        r_event = received_message['event']
        msg = r_event['message']
        msg_id = msg['message_id']

        # 重复消息忽略
        if msg_id in self.message_ids:
            return 'ignore'
        else:
            self.message_ids.add(msg_id)

        # 判断是单聊还是群消息
        if msg['chat_type'] == 'p2p':
            return self.handle_p2p(received_message)
        elif msg['chat_type'] == 'group':
            return self.handle_group(received_message)
        else:
            return 'not support chat_type'


class ChatGPTServer(BaseServer):

    def __init__(self):
        super().__init__()
        self.chatbot = Chatbot()
        self.support_image_generation = True
        self.is_valid_message = False

        self.client = Client()

        self.message_ids = set()

    def ask(self, text, sender_id=None):
        if text == 'Brazil':
            self.chatbot.reset()
            return 'bot is reset'

        response = self.chatbot.ask(text, conversation_id=sender_id)
        logger.debug('chatgpt response', response)

        return response

    def process(self, message, msg_text):
        event = message['event']
        msg = event['message']
        sender_id = event['sender']['sender_id']['open_id']

        if msg_text.startswith('作图 '):
            if self.support_image_generation is False:
                self.client.reply_text(msg['message_id'], msg['chat_id'], '暂不提供AI作图能力')
                return 'success'

            prompt = re.sub(r'^作图 ', '', msg_text)
            try:
                response = openai.Image.create(prompt=prompt, n=1, size='512x512')
            except Exception as e:
                logger.error(e)
                return 'generate image error'

            img_url = response['data'][0]['url']
            self.client.reply_img(msg['message_id'], msg['chat_id'], img_url)
            return 'success'

        chatgpt_res_text = '获取chatgpt回复消息失败'
        try:
            chatgpt_res_text = self.ask(msg_text, sender_id=sender_id)
        except Exception as e:
            logger.error(e)
            self.client.reply_text(msg['message_id'], msg['chat_id'], '服务出了点问题，请重试')
            return 'error'

        self.client.reply_text(msg['message_id'], msg['chat_id'], chatgpt_res_text)
        return 'success'

    def handle_p2p(self, message):
        """
        单聊消息处理
        """
        event = message['event']
        msg = event['message']

        msg_content = json.loads(msg['content'])
        msg_text = msg_content['text']
        return self.process(message, msg_text)

    def handle_group(self, message):
        """
        处理群消息
        """

        event = message['event']
        msg = event['message']

        msg_content = json.loads(msg['content'])

        at_key = self.client.is_be_at(msg)
        if at_key is False:
            return 'ignore group message'

        msg_text = msg_content['text'].replace(at_key + ' ', '')
        return self.process(message, msg_text)

    def handle(self, request):
        if self.is_valid_message:
            if not self.client.valid(request):
                logger.info('received message is invalid')

        received_message = self.client.parse_message(request)
        logger.debug(received_message)
        if not received_message:
            logger.error('received message is None')

        # 飞书认证逻辑
        if 'challenge' in received_message:
            return {'challenge': received_message['challenge']}

        r_event = received_message['event']
        msg = r_event['message']
        msg_id = msg['message_id']

        # 重复消息忽略
        if msg_id in self.message_ids:
            return 'ignore'
        else:
            self.message_ids.add(msg_id)

        # 判断是单聊还是群消息
        if msg['chat_type'] == 'p2p':
            return self.handle_p2p(received_message)
        elif msg['chat_type'] == 'group':
            return self.handle_group(received_message)
        else:
            return 'not support chat_type'
