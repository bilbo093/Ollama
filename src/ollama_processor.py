#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一的文本处理器和 Ollama 客户端
通过配置驱动，支持不同的处理任务
"""

from ollama import chat
import difflib
from config import (
    DEFAULT_MODEL, DEFAULT_THINK, STREAM_BUFFER_SIZE,
    PROCESSOR_CONFIGS
)
from content_splitter import split_content_by_chapters


def chat_streaming(model: str, messages: list, think: bool = DEFAULT_THINK) -> str:
    """
    流式获取内容并使用缓冲区方式显示
    内置复读检测和安全阈值保护,自动处理复读场景

    Args:
        model: Ollama 模型名称
        messages: 消息列表
        think: 是否启用思考模式

    Returns:
        完整的响应内容
    """
    # 提取输入长度
    input_length = _get_input_length(messages)
    safety_threshold = max(input_length * 20, 2000) if input_length > 0 else 0

    # 第一次尝试:长度阈值检测
    result = _stream_chat(model, messages, think, safety_threshold, use_similarity=False)

    # 如果第一次失败(输出过长),重试使用相似度检测
    if safety_threshold > 0 and len(result) >= safety_threshold:
        print(f"\n[重试] 检测到输出过长,使用相似度检测重新生成...")
        result = _stream_chat(model, messages, think, safety_threshold, use_similarity=True)

    return result


def _get_input_length(messages: list) -> int:
    """从 messages 中提取用户输入的长度"""
    return sum(len(msg.get('content', '')) for msg in messages if msg.get('role') == 'user')


def _stream_chat(model: str, messages: list, think: bool, safety_threshold: int, use_similarity: bool) -> str:
    """
    流式聊天(带复读检测)

    Args:
        model: 模型名称
        messages: 消息列表
        think: 思考模式
        safety_threshold: 长度阈值
        use_similarity: 是否使用相似度检测

    Returns:
        完整响应
    """
    try:
        full_content = ""
        buffer = ""
        char_count = 0
        last_buffer = ""
        repeat_count = 0

        for chunk in chat(model=model, messages=messages, stream=True, think=think):
            content = chunk['message']['content']
            buffer += content
            full_content += content
            char_count += len(content)

            # 相似度复读检测(第二次尝试使用)
            if use_similarity and len(buffer) > 50:
                similarity = difflib.SequenceMatcher(None, buffer[-200:], last_buffer).ratio()
                if similarity >= 0.6:
                    repeat_count += 1
                    print(f"\r[复读检测] 相似度: {similarity:.2f}, 次数: {repeat_count}/5", end='', flush=True)
                    if repeat_count >= 5:
                        print(f"\n[警告] 检测到模型复读,已中断")
                        break
                else:
                    repeat_count = 0
                last_buffer = buffer[-200:]

            # 长度阈值检测(第一次尝试使用)
            elif safety_threshold > 0 and len(full_content) > safety_threshold:
                print(f"\n[警告] 检测到输出过长,已中断")
                break

            # 缓冲输出
            while len(buffer) >= STREAM_BUFFER_SIZE:
                to_print = buffer[:STREAM_BUFFER_SIZE]
                print(f"\r[进度] {char_count} 字符: {to_print[-50:].replace(chr(10), ' ')}", end='', flush=True)
                buffer = buffer[STREAM_BUFFER_SIZE:]

        # 输出剩余内容
        if buffer:
            print(buffer[-50:].replace(chr(10), ' '), end='', flush=True)

        return full_content
    except Exception as e:
        print(f"\n[错误] {e}")
        return ""


class TextProcessor:
    """统一的文本处理器"""

    def __init__(self, role, prompt_template):
        """
        初始化处理器

        Args:
            role: 系统角色配置
            prompt_template: 提示词模板
        """
        self.role = role
        self.prompt_template = prompt_template

    def process_content(self, content, **kwargs):
        """
        处理内容

        Args:
            content: 输入内容
            **kwargs: 模板参数（如 chapter_title）

        Returns:
            str: 处理结果
        """
        # 构建提示词
        prompt = self.prompt_template.format(content=content, **kwargs)

        # 构建消息
        messages = [self.role, {'role': 'user', 'content': prompt}]

        # 调用 Ollama（始终使用流式）
        result = chat_streaming(model=DEFAULT_MODEL, messages=messages)

        return result


def generate_and_save_chapter_summaries(content: str, output_file: str):
    """
    生成章节总结并保存到文件（流式写入，每处理完一个章节就写入）

    Args:
        content: 文档内容
        output_file: 输出文件路径

    Returns:
        None
    """
    from file_io import save_to_txt

    # 按章节分割内容
    chapters = split_content_by_chapters(content)
    print(f"[信息] 识别到 {len(chapters)} 个章节")

    config = PROCESSOR_CONFIGS['chapter']
    processor = TextProcessor(config['role'], config['prompt_template'])

    # 初始化文件（写入标题，覆盖模式）
    save_to_txt("", output_file, "章节总结", mode='w')

    # 逐个处理章节并追加写入
    for idx, chapter in enumerate(chapters, 1):
        print(f"[章节 {idx}/{len(chapters)}] {chapter['title']}")
        summary = processor.process_content(chapter['content'], chapter_title=chapter['title'])

        # 立即追加写入当前章节
        chapter_content = f"\n\n{chapter['title']}\n\n{summary}\n\n"
        save_to_txt(chapter_content, output_file, "", mode='a')

    print(f"[完成] 共生成 {len(chapters)} 个章节总结，已保存至：{output_file}")


__all__ = [
    'chat_streaming',
    'TextProcessor',
    'generate_and_save_chapter_summaries',
]
