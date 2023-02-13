# -*- coding: utf-8 -*-

import os
import re
import json
import logging

import openai
from revChatGPT.Official import Chatbot

from .feishu import FeishuBot


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


API_KEY = os.getenv('OPENAI_API_KEY')
openai.api_key = API_KEY


class FeishuChatGPTBot(FeishuBot):
    def __init__(self, app_id, app_secret, encrypt_key):
        super().__init__(app_id, app_secret, encrypt_key)
        self.chatbot = Chatbot(api_key=API_KEY)
        self.support_image_generation = True

    def ask(self, text, sender_id=None):
        if text == 'Brazil':
            self.chatbot.reset()
            return 'bot is reset'

        response = self.chatbot.ask(text, conversation_id=sender_id)
        logger.debug('chatgpt response', response)

        reply_text = response['choices'][0]['text']
        return reply_text

    def process(self, message, msg_text):
        event = message['event']
        msg = event['message']
        sender_id = event['sender']['sender_id']['open_id']

        if msg_text.startswith('作图 '):
            if self.support_image_generation is False:
                self.reply_text(msg['message_id'], msg['chat_id'], '暂不提供AI作图能力')
                return 'success'

            prompt = re.sub(r'^作图 ', '', msg_text)
            try:
                response = openai.Image.create(prompt=prompt, n=1, size='512x512')
            except Exception as e:
                logger.error(e)
                return 'generate image error'

            img_url = response['data'][0]['url']
            self.reply_img(msg['message_id'], msg['chat_id'], img_url)
            return 'success'

        chatgpt_res_text = '获取chatgpt回复消息失败'
        try:
            chatgpt_res_text = self.ask(msg_text, sender_id=sender_id)
        except Exception as e:
            logger.error(e)
            self.reply_text(msg['message_id'], msg['chat_id'], '服务出了点问题，请重试')
            return 'error'

        self.reply_text(msg['message_id'], msg['chat_id'], chatgpt_res_text)
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

        at_key = self.is_be_at(msg)
        if at_key is False:
            return 'ignore group message'

        msg_text = msg_content['text'].replace(at_key + ' ', '')
        return self.process(message, msg_text)
