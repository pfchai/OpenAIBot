# -*- coding: utf-8 -*-

import os
import re
import json
import logging

import openai
import tiktoken

from .prompt import Prompt
from .conversation_manager import ConversationManager


ENGINE = os.environ.get('GPT_ENGINE') or 'text-davinci-003'
ENCODER = tiktoken.get_encoding('gpt2')


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class GPT3ChatBot():

    def __init__(self, api_key: str = None, engine: str = None, proxy: str = None):
        openai.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        openai.proxy = proxy or os.environ.get("OPENAI_API_PROXY")
        self.engine = engine or ENGINE

        self.max_token = 4000
        self.prompt = Prompt(max_token=self.max_token)
        self.conversation_manager = ConversationManager()

    def _get_completion(self, prompt: str, temperature: float = 0.5, stream: bool = False):
        return openai.Completion.create(
            engine=self.engine,
            prompt=prompt,
            temperature=temperature,
            stop=['\n\n\n'],
            stream=stream
        )

    def parse_completion(self, completion: dict) -> str:
        if completion.get('choices') is None:
            raise Exception('ChatGPT API returned no choices')

        if len(completion['choices']) == 0:
            raise Exception('ChatGPT API returned no choices')

        if completion['choices'][0].get('text') is None:
            raise Exception('ChatGPT API returned no text')

        response = re.sub(r'<\|im_end\|>', '', completion['choices'][0]['text'])

        completion['choices'][0]['text'] = response
        return response

    def ask(self, query, temperature: float = 0.5, conversation_id: str = None, user: str = 'User'):
        if conversation_id is None:
            history = []
        else:
            history = self.conversation_manager.get_conversation(conversation_id)

        prompt, history = self.prompt.encode(query, history, user)

        completion = None
        try:
            logger.debug('请求 OpenAI 接口 %s', prompt)
            completion = openai.Completion.create(
                engine=self.engine,
                prompt=prompt,
                temperature=temperature,
                max_tokens=self.max_token - len(prompt),
                stop=['\n\n\n'],
                stream=False
            )
            logger.debug('OpenAI 接口返回 %s', json.dumps(completion, ensure_ascii=False))
        except Exception as e:
            logger.error('OpenAI 接口返回异常，%s', e, exc_info=True)
            return ''

        response = self.parse_completion(completion)
        if conversation_id is not None:
            history.append([query, response])
            self.conversation_manager.add_conversation(conversation_id, history)

        return response


class AsyncGPT3ChatBot(GPT3ChatBot):

    async def ask(self, query, temperature: float = 0.5, conversation_id: str = None, user: str = 'User'):
        if conversation_id is None:
            history = []
        else:
            history = self.conversation_manager.get_conversation(conversation_id)

        prompt, history = self.prompt.encode(query, history, user)

        completion = None
        try:
            logger.debug('请求 OpenAI 接口 %s', prompt)
            completion = openai.Completion.create(
                engine=self.engine,
                prompt=prompt,
                temperature=temperature,
                max_tokens=self.max_token - len(prompt),
                stop=['\n\n\n'],
                stream=False
            )
            logger.debug('OpenAI 接口返回 %s', json.dumps(completion, ensure_ascii=False))
        except Exception as e:
            logger.error('OpenAI 接口返回异常，%s', e, exc_info=True)
            return ''

        response = self.parse_completion(completion)
        if conversation_id is not None:
            history.append([query, response])
            self.conversation_manager.add_conversation(conversation_id, history)

        return response
