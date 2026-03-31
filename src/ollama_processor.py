#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一的文本处理器和 Ollama 客户端
通过配置驱动，支持不同的处理任务
"""

from ollama import chat
from config import (
    DEFAULT_MODEL, DEFAULT_THINK, STREAM_BUFFER_SIZE,
    PROCESSOR_CONFIGS
)
from content_splitter import split_content_by_chapters


def chat_streaming(model: str, messages: list, think: bool = DEFAULT_THINK, show_progress: bool = True) -> str:
    """
    流式获取内容并使用缓冲区方式显示

    Args:
        model: Ollama 模型名称
        messages: 消息列表
        think: 是否启用思考模式
        show_progress: 是否显示进度

    Returns:
        完整的响应内容
    """
    try:
        full_content = ""
        buffer = ""
        char_count = 0

        for chunk in chat(model=model, messages=messages, stream=True, think=think):
            content = chunk['message']['content']
            buffer += content
            full_content += content
            char_count += len(content)

            if show_progress:
                # 检查缓冲区中的字符数量是否达到了配置的大小
                while len(buffer) >= STREAM_BUFFER_SIZE:
                    # 提取前 STREAM_BUFFER_SIZE 个字符进行打印
                    to_print = buffer[:STREAM_BUFFER_SIZE]
                    display_text = to_print.replace('\n', ' ')
                    print(f"\r[进度] 已生成 {char_count} 字符: {display_text[-50:]}", end='', flush=True)

                    # 更新缓冲区，保留剩余未打印的字符
                    buffer = buffer[STREAM_BUFFER_SIZE:]

        # 循环结束后，如果缓冲区里还有剩余的内容，则全部打印出来
        if buffer and show_progress:
            print(f"\r[完成] 分析完成,共生成 {char_count} 字符{' ' * 50}")
        elif buffer:
            print(buffer, end='\r', flush=True)

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
    生成章节总结并保存到文件

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

    summaries = []
    config = PROCESSOR_CONFIGS['chapter']
    processor = TextProcessor(config['role'], config['prompt_template'])

    for idx, chapter in enumerate(chapters, 1):
        print(f"[章节 {idx}/{len(chapters)}] {chapter['title']}")
        summary = processor.process_content(chapter['content'], chapter_title=chapter['title'])
        summaries.append({
            'title': chapter['title'],
            'summary': summary
        })

    # 保存结果
    all_summaries = ""
    for item in summaries:
        all_summaries += f"{item['title']}\n\n"
        all_summaries += f"{item['summary']}\n\n"
        all_summaries += "=" * 60 + "\n\n"

    save_to_txt(all_summaries, output_file, "章节总结")
    print(f"[完成] 共生成 {len(summaries)} 个章节总结，已保存至：{output_file}")


__all__ = [
    'chat_streaming',
    'TextProcessor',
    'generate_and_save_chapter_summaries',
]
