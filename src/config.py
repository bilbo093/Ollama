"""
项目配置文件
基础配置和处理器配置在此文件中定义
角色和提示词从 prompts/ 文件夹导入（内部使用）
"""
import os

# ==================== 后端配置 ====================
# LLM 服务地址，兼容 Ollama / llama.cpp / OpenAI / DeepSeek 等所有 OpenAI 兼容 API
# 直接修改此处即可，无需设置环境变量
BASE_URL = os.getenv('BASE_URL', 'http://127.0.0.1:8080')

# API Key（本地服务留空，云服务填写您的 API Key）
API_KEY = os.getenv('API_KEY', '')

# 模型名称（本地服务留空，云服务填写模型名称）
MODEL_NAME = os.getenv('MODEL_NAME', '')

# ==================== 流式输出配置 ====================
STREAM_BUFFER_SIZE = 30  # 缓冲区大小（字符数），降低以实现更流畅的流式输出

# ==================== 模型配置 ====================
# 注意：模型名称由 API 服务端决定，客户端不再指定
DEFAULT_THINK = False

# 从 prompts 模块导入角色和提示词配置（内部使用）
from prompts import (
    ACADEMIC_SUMMARIZER_ROLE,
    ACADEMIC_SUMMARIZER_PROMPT,
    CHAPTER_SUMMARIZER_ROLE,
    CHAPTER_SUMMARIZER_PROMPT,
    GRAMMAR_CHECKER_ROLE,
    GRAMMAR_CHECKER_PROMPT,
)

# ==================== 处理器配置 ====================
# 统一的处理器配置，所有处理器都通过配置驱动
# 三种处理粒度：全文 / 章节 / 段落
PROCESSOR_CONFIGS = {
    'full': {
        'role': ACADEMIC_SUMMARIZER_ROLE,
        'prompt_template': ACADEMIC_SUMMARIZER_PROMPT,
    },
    'chapter': {
        'role': CHAPTER_SUMMARIZER_ROLE,
        'prompt_template': CHAPTER_SUMMARIZER_PROMPT,
    },
    'paragraph': {
        'role': GRAMMAR_CHECKER_ROLE,
        'prompt_template': GRAMMAR_CHECKER_PROMPT,
    },
}

__all__ = [
    'BASE_URL',
    'API_KEY',
    'MODEL_NAME',
    'STREAM_BUFFER_SIZE',
    'DEFAULT_THINK',
    'PROCESSOR_CONFIGS',
]
