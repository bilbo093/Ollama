#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一的 LLM 客户端
使用 OpenAI 兼容协议，兼容 Ollama / llama.cpp / OpenAI / DeepSeek 等所有服务
"""

import difflib
import json
import requests
from typing import Optional
from config import (
    STREAM_BUFFER_SIZE,
    BASE_URL, API_KEY, MODEL_NAME,
)


class LLMClient:
    """统一的 LLM 客户端，使用 OpenAI 兼容协议"""

    def __init__(self):
        self._full_content = ""
        self._buffer = ""
        self._char_count = 0
        self._last_buffer = ""
        self._repeat_count = 0

    def _build_request(self, messages: list) -> tuple:
        """构建 OpenAI 兼容的请求参数"""
        base_url = BASE_URL.rstrip('/')
        url = f"{base_url}/v1/chat/completions"
        payload = {
            "model": MODEL_NAME or "default",
            "messages": messages,
            "stream": True,
        }
        headers = {"Content-Type": "application/json"}
        if API_KEY:
            headers["Authorization"] = f"Bearer {API_KEY}"
        return url, payload, headers

    def _reset_state(self):
        self._full_content = ""
        self._buffer = ""
        self._char_count = 0
        self._last_buffer = ""
        self._repeat_count = 0

    def _parse_line(self, line: str) -> Optional[str]:
        """解析单行 SSE 数据，返回 None 表示结束信号"""
        line_stripped = line.strip()
        if line_stripped.startswith('data: '):
            json_str = line_stripped[6:]
        elif line_stripped.startswith('data:'):
            json_str = line_stripped[5:]
        else:
            json_str = line_stripped

        if not json_str or json_str == '[DONE]':
            return ''

        chunk_data = json.loads(json_str)

        choices = chunk_data.get('choices', [])
        if not choices:
            return ''
        choice = choices[0]
        if choice.get('finish_reason') == 'stop':
            return None
        delta = choice.get('delta')
        if not delta:
            return ''
        return delta.get('content', '') or ''

    def _check_repeat(self) -> bool:
        """检查复读，返回是否应中断"""
        if len(self._buffer) > 50:
            similarity = difflib.SequenceMatcher(None, self._buffer[-200:], self._last_buffer).ratio()
            if similarity >= 0.6:
                self._repeat_count += 1
                print(f"\r[复读检测] 相似度: {similarity:.2f}, 次数: {self._repeat_count}/5", end='', flush=True)
                if self._repeat_count >= 5:
                    print(f"\n[警告] 检测到模型复读,已中断")
                    return True
            else:
                self._repeat_count = 0
            self._last_buffer = self._buffer[-200:]
        return False

    def chat(self, messages: list) -> str:
        """
        发送消息并流式返回完整响应

        Args:
            messages: 消息列表，格式为 [{'role': 'system', 'content': ...}, {'role': 'user', 'content': ...}]

        Returns:
            str: 完整的响应内容
        """
        if not messages:
            raise ValueError("messages 不能为空")

        self._reset_state()
        url, payload, headers = self._build_request(messages)

        try:
            response = requests.post(url, json=payload, headers=headers, stream=True, timeout=300)
            response.raise_for_status()
            response.encoding = 'utf-8'

            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue
                if line.strip() == '[DONE]':
                    break

                try:
                    content = self._parse_line(line)
                    if content is None:
                        break
                    if content:
                        self._buffer += content
                        self._full_content += content
                        self._char_count += len(content)
                    if self._check_repeat():
                        break
                    while len(self._buffer) >= STREAM_BUFFER_SIZE:
                        to_print = self._buffer[:STREAM_BUFFER_SIZE]
                        print(f"\r[进度] {self._char_count} 字符: {to_print[-50:].replace(chr(10), ' ')}", end='', flush=True)
                        self._buffer = self._buffer[STREAM_BUFFER_SIZE:]
                except (KeyError, IndexError, json.JSONDecodeError):
                    continue

            if self._buffer:
                print(self._buffer[-50:].replace(chr(10), ' '), end='', flush=True)

        except requests.exceptions.RequestException as e:
            print(f"\n[错误] API 请求失败: {e}")
            print(f"[提示] 请确认 LLM 服务已启动: {BASE_URL}")
            raise

        return self._full_content


# 模块级单例（便捷访问）
_client = None


def chat(messages: list) -> str:
    """模块级便捷函数，使用默认 LLMClient"""
    global _client
    if _client is None:
        _client = LLMClient()
    return _client.chat(messages)


__all__ = ['LLMClient', 'chat']
