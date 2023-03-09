# -*- coding: utf-8 -*-

import requests


class YDLGPTBot():

    def __init__(self, url, app_id, scene) -> None:
        self.url = url
        self.app_id = app_id
        self.scene = scene
        self.headers = {'Content-Type': 'application/json'}

    def ask(self, text, sender_id='', chat_id=''):

        body = {
            'botDTO': {
                'appId': self.app_id,
                'userId': sender_id,
                'conversationId': chat_id,
                'input': text,
                'scene': self.scene,
            }
        }

        response = requests.post(self.url, headers=self.headers, json=body)
        res_data = response.json()
        reply_text = res_data['data']['aiSide']
        return reply_text