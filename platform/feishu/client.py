# -*- coding: utf-8 -*-

import os
import json
import time
import hashlib
import logging

import requests
from requests_toolbelt import MultipartEncoder

from .tool import AESCipher


logger = logging.getLogger(__name__)


class Client():
    def __init__(self):

        self.app_id = os.getenv('FEISHU_APP_ID')
        self.app_secret = os.getenv('FEISHU_APP_SECRET')
        self.encrypt_key = os.getenv('FEISHU_ENCRYPT_KEY')
        self.is_valid_message = False

        self.tenant_access_token = ''
        self.expiry_time = time.time()

        self.id_map = {}
        self.message_ids = set()
        self.update_tenant_access_token()
        self.get_bot_info()

        self.cipher = AESCipher(self.encrypt_key)

    def _valid_message(self, request):
        headers = request.headers
        timestamp = headers['X-Lark-Request-Timestamp']
        nonce = headers['X-Lark-Request-Nonce']

        bytes_b1 = (timestamp + nonce + self.encrypt_key).encode('utf-8')
        bytes_b = bytes_b1 + request.data
        h = hashlib.sha256(bytes_b)
        signature = h.hexdigest()

        return request.headers['X-Lark-Signature'] == signature

    def get_bot_info(self):
        """
        获取机器人信息
        """
        url = 'https://open.feishu.cn/open-apis/bot/v3/info'
        headers = {
            'Authorization': 'Bearer {}'.format(self.tenant_access_token),
            'Content-Type': 'application/json; charset=utf-8'
        }
        response = requests.request('GET', url, headers=headers)
        data = response.json()
        logger.debug('获取bot信息成功')
        logger.debug('--' * 20)
        logger.debug(data)

        self.bot_open_id = data.get('bot', {}).get('open_id')
        return data

    def update_tenant_access_token(self):
        logger.debug('更新 tenant_access_token')

        url = 'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal'
        headers = {
            'Content-Type': 'application/json; charset=utf-8'
        }
        body = {
            'app_id': self.app_id,
            'app_secret': self.app_secret,
        }
        response = requests.request('POST', url, headers=headers, data=json.dumps(body))
        data = response.json()

        self.expiry_time = data['expire'] + time.time() - 10
        self.tenant_access_token = data['tenant_access_token']

        logger.debug('tenant_access_token 更新成功')
        return

    def upload_img(self, image, image_file_type='file'):
        """ 上传图片 """

        url = 'https://open.feishu.cn/open-apis/im/v1/images'
        if image_file_type == 'file':
            form = {'image_type': 'message', 'image': (open(image, 'rb'))}
        elif image_file_type == 'net':
            _response = requests.get(image)
            form = {'image_type': 'message', 'image': _response.content}
        else:
            logger.error('不支持的图片文件类型')
            return

        multi_form = MultipartEncoder(form)
        headers = {
            'Authorization': 'Bearer {}'.format(self.tenant_access_token),
            'Content-Type': multi_form.content_type
        }
        response = requests.request("POST", url, headers=headers, data=multi_form)
        logger.debug(response.content)

        data = response.json()
        return data.get('data', {}).get('image_key')

    # 判断机器人是否被 @
    def is_be_at(self, msg):
        for mention in msg.get('mentions', []):
            if mention['id']['open_id'] == self.bot_open_id:
                return mention['key']
        return False

    def _reply(self, message_id, data):
        if time.time() > self.expiry_time:
            self.update_tenant_access_token()

        url = 'https://open.feishu.cn/open-apis/im/v1/messages/{}/reply'.format(message_id)
        headers = {
            'Authorization': 'Bearer {}'.format(self.tenant_access_token),
            'Content-Type': 'application/json; charset=utf-8'
        }

        logger.debug('--' * 20)
        logger.debug('\n'+json.dumps(data, ensure_ascii=False))

        response = requests.request('POST', url, headers=headers, data=json.dumps(data))

        logger.debug(response.text)
        return response

    def parse_message(self, request):
        content = request.json
        if 'encrypt' in content:
            decrypt_str = self.cipher.decrypt_string(content['encrypt'])
            content = json.loads(decrypt_str)
        return content

    def reply_text(self, message_id, chat_id, text):
        if time.time() > self.expiry_time:
            self.update_tenant_access_token()

        data = {
            'receive_id': chat_id,
            'content': json.dumps({'text': text}),
            'msg_type': 'text',
        }
        return self._reply(message_id, data)

    def reply_img(self, message_id, chat_id, image):
        if time.time() > self.expiry_time:
            self.update_tenant_access_token()

        if image.startswith('http'):
            image_file_type = 'net'
        else:
            image_file_type = 'file'

        img_key = self.upload_img(image, image_file_type=image_file_type)
        logger.info('image upload, key = %s', img_key)

        data = {
            'receive_id': chat_id,
            'content': json.dumps({'image_key': img_key}),
            'msg_type': 'image',
        }
        return self._reply(message_id, data)

    def handle_p2p(self, message):
        """
        单聊消息处理
        """
        msg = message['event']['message']
        msg_content = json.loads(msg['content'])
        msg_text = msg_content['text']

        self.reply_text(msg['message_id'], msg['chat_id'], '收到消息：' + msg_text)
        return 'success'

    def handle_group(self, message):
        """
        处理群消息
        """
        msg = message['event']['message']
        msg_content = json.loads(msg['content'])

        at_key = self.is_be_at(msg)
        if at_key is False:
            return 'ignore group message'

        msg_text = msg_content['text'].replace(at_key + ' ', '')
        self.reply_text(msg['message_id'], msg['chat_id'], '收到消息：' + msg_text)
        return 'success'

    def handle(self, request):
        if self.is_valid_message:
            if not self.valid(request):
                logger.info('received message is invalid')

        received_message = self.parse_message(request)
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
