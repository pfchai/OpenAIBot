# -*- coding: utf-8 -*-

import os
import time
import json
import logging

import requests

from .WXBizMsgCrypt import WXBizMsgCrypt


logger = logging.getLogger(__name__)


class Client():
    def __init__(self):
        self.token = os.getenv('WEWORK_TOKEN')
        self.encoding_aes_key = os.getenv('WEWORK_ENCODING_AES_KEY')
        self.corp_id = os.getenv('WEWORK_CORP_ID')
        self.secret = os.getenv('WEWORK_SECRET')
        self.agentid = int(os.getenv('WEWORK_AGENTID'))

        self.access_token = ''
        self.expiry_time = time.time()

        self.wxcpt = WXBizMsgCrypt(self.token, self.encoding_aes_key, self.corp_id)
        self.update_access_token()

    def vertify_url(self, request):
        logger.info('request for vertify url')
        logger.info(request.args)

        msg_signature = request.args.get('msg_signature')
        timestamp = request.args.get('timestamp')
        nonce = request.args.get('nonce')
        echo_str = request.args.get('echostr')

        ret, echo_str = self.wxcpt.VerifyURL(msg_signature, timestamp, nonce, echo_str)
        if ret != 0:
            logger.error('ERR: Vertify URL ret ', ret)

        return echo_str

    def update_access_token(self):
        logger.debug('更新 access_token')

        url = f'https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={self.corp_id}&corpsecret={self.secret}'
        response = requests.request('GET', url)
        data = response.json()

        self.expiry_time = data['expires_in'] + time.time() - 10
        self.access_token = data['access_token']

        logger.debug('access_token 更新成功')
        return

    def decrypt_msg(self, request):
        msg_signature = request.args.get('msg_signature')
        timestamp = request.args.get('timestamp')
        nonce = request.args.get('nonce')

        ret, msg = self.wxcpt.DecryptMsg(request.data, msg_signature, timestamp, nonce)
        if ret != 0:
            logger.error('decrypt msg error')
            return None

        return msg

    def encrypt_msg(self, resp_data, req_nonce, timestamp):
        #  timestamp = time.time()
        ret, encrypted_msg = self.wxcpt.EncryptMsg(resp_data, req_nonce, timestamp)
        if ret != 0:
            return None

        return encrypted_msg

    def send_msg(self, content: str, to_user):
        if time.time() > self.expiry_time:
            self.update_access_token()

        data = {
            'touser': to_user,
            'msgtype': 'text',
            'agentid': self.agentid,
            'text': {
                'content': content
            },
            'safe': 0,
            'enable_id_trans': 0,
            'enable_duplicate_check': 0,
            'duplicate_check_interval': 1800
        }

        logger.debug('--' * 20)
        logger.debug('\n'+json.dumps(data, ensure_ascii=False))

        url = f'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={self.access_token}&debug=1'
        response = requests.request('POST', url, data=json.dumps(data))

        res_data = response.json()
        if res_data['errcode'] != 0:
            logger.error('send message error: %s', res_data['errmsg'])

        logger.debug(response.text)
        return response
