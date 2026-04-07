#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档处理器
基于 DocumentProvider 抽象层，按三种粒度处理文档：
  - 全文模式（full）：整个文档一次性送入 LLM
  - 章节模式（chapter）：按章节拆分后逐章送入 LLM
  - 段落模式（paragraph）：按段落拆分后逐段送入 LLM
"""

import os
import re
from typing import Tuple, Optional
from ollama_processor import chat
from config import PROCESSOR_CONFIGS
from file_io import save_to_txt
from content_splitter import is_table_of_contents
from document_provider import DocumentProvider


def is_ref_section(text: str) -> bool:
    """判断是否是参考文献章节"""
    return '参考文献' in text.strip()


def _skip_para(text: str) -> bool:
    """
    判断段落是否应该跳过

    Args:
        text: 段落文本

    Returns:
        bool: 是否跳过
    """
    text_stripped = text.strip()

    # 1. 跳过空段落
    if not text_stripped:
        return True

    # 2. 跳过过短的段落（少于50个字符）
    if len(text_stripped) < 50:
        return True

    # 3. 跳过纯 LaTeX 公式段落
    # 检查段落是否主要由 LaTeX 公式组成（以 $ 或 \(\) 或 \[\] 包围）
    latex_pattern = r'^\s*([$\[\]\\].*[$\[\]\\]|\\[a-zA-Z]+\{.*\}|\\[a-zA-Z]+\s)+\s*$'
    if re.match(latex_pattern, text_stripped):
        return True

    # 4. 跳过目录内容
    if is_table_of_contents(text):
        return True

    return False


def check_paragraph(paragraph_text: str) -> Tuple[str, str]:
    """
    检查单个段落,返回 Ollama 的原始输出
    复读检测和安全阈值由 Ollama 客户端自动处理

    Args:
        paragraph_text: 段落文本

    Returns:
        Tuple[str, str]: (Ollama 原始输出, 段落文本)
    """
    config = PROCESSOR_CONFIGS['paragraph']

    # 构建提示词
    prompt = config['prompt_template'].format(content=paragraph_text)

    # 构建消息
    messages = [config['role'], {'role': 'user', 'content': prompt}]

    # 调用 LLM API（流式显示），复读检测由客户端自动处理
    result = chat(messages).strip()

    return result, paragraph_text


def _parse_modified_text(ollama_result: str) -> str:
    """
    从 Ollama 输出中解析修改后的文本

    Ollama 返回格式(由 GRAMMAR_CHECKER_PROMPT 定义):
    #### 第一部分：修改后的文本
    ###MODIFIED_TEXT###
    {修改后的文本内容}

    #### 第二部分：修改说明
    ###MODIFIED_DESCRIPTION###
    {修改说明}

    Args:
        ollama_result: Ollama 返回的完整结果

    Returns:
        str: 修改后的文本，如果没有修改则返回空字符串
    """
    if not ollama_result:
        return ""

    # 检查是否有 ###MODIFIED_TEXT### 分隔符
    if "###MODIFIED_TEXT###" not in ollama_result:
        return ""

    # 提取 MODIFIED_TEXT 之后的第一段内容
    parts = ollama_result.split("###MODIFIED_TEXT###")
    if len(parts) <= 1:
        return ""

    modified_part = parts[1].strip()

    # 按换行符分割，取第一个非空段落
    lines = modified_part.split('\n')
    for line in lines:
        if line.strip():
            return line.strip()

    return ""


def _save_mods_to_txt(txt_file: str, para_idx: int, para_text: str, ollama_result: str):
    """
    将修改建议保存到 txt 文件（只添加格式化分隔线）

    Args:
        txt_file: txt 文件路径
        para_idx: 段落索引
        para_text: 原始段落文本
        ollama_result: Ollama 的原始输出
    """
    # 只保存前20个字方便用户定位段落
    preview = para_text[:20] + '...' if len(para_text) > 20 else para_text

    # 格式化内容，只添加分隔线
    content = f"{'=' * 60}\n"
    content += f"段落 {para_idx}\n"
    content += f"{'=' * 60}\n"
    content += f"原始内容（前20字）：{preview}\n"
    content += f"Ollama 输出：\n{ollama_result}\n"

    # 写入文件
    with open(txt_file, 'a', encoding='utf-8') as f:
        f.write(content)


def _parse_txt(txt_file: str) -> dict:
    """
    从 TXT 文件中解析段落修改记录

    TXT 格式(由 _save_modifications_to_txt 写入):
    ============================================================
    段落 N
    ============================================================
    原始内容（前20字）：{前20个字}
    Ollama 输出：
    {Ollama 完整返回内容}

    Args:
        txt_file: TXT 文件路径

    Returns:
        dict: 段落索引到修改后文本的映射 {para_idx: modified_text}
    """
    if not os.path.exists(txt_file):
        return {}

    modifications = {}

    with open(txt_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 使用正则表达式匹配每个段落块
    # 匹配保存时的实际格式
    para_pattern = re.compile(
        r'={60}\s*\n段落\s+(\d+)\s*\n={60}\s*\n'
        r'原始内容[^\n]*\n'
        r'Ollama\s*输出：(.*?)(?=\n={60}\s*\n段落\s+\d+\s*\n={60}|\Z)',
        re.DOTALL
    )

    matches = para_pattern.finditer(content)

    for match in matches:
        para_idx = int(match.group(1))
        ollama_output = match.group(2).strip()

        # 从 Ollama 输出中解析修改后的文本
        modified_text = _parse_modified_text(ollama_output)

        if modified_text:
            modifications[para_idx] = modified_text

    return modifications


def process_document(provider: DocumentProvider, output_txt: Optional[str] = None) -> Tuple[int, int]:
    """
    基于 DocumentProvider 的通用语法检查流程，支持任意文档格式

    Args:
        provider: 文档提供者实例（TxtDocumentProvider / DocxDocumentProvider / ...）
        output_txt: 语法检查结果 TXT 文件路径（可选）

    Returns:
        Tuple[int, int]: (总段落数, 修改的段落数)
    """
    paragraphs = provider.read_paragraphs()
    total_paragraphs = len(paragraphs)

    # 找到最后一个"参考文献"段落的位置，确定处理范围
    process_until = total_paragraphs
    for idx, text in enumerate(paragraphs):
        if is_ref_section(text.strip()):
            process_until = idx

    print(f"[信息] 处理范围：第 1 ~ {process_until} 段（共 {total_paragraphs} 段）")

    if output_txt:
        save_to_txt("", output_txt, title="", mode='w')

    modifications = {}

    for idx, para_text in enumerate(paragraphs[:process_until], 1):
        if _skip_para(para_text):
            continue

        print(f"\r[段落 {idx} / {total_paragraphs}] 开始检查...", end='', flush=True)
        ollama_result, original = check_paragraph(para_text)

        if output_txt and ollama_result:
            _save_mods_to_txt(output_txt, idx, original, ollama_result)

        corrected_text = _parse_modified_text(ollama_result)
        if corrected_text:
            modifications[idx] = corrected_text

    # 通过 provider 统一应用修改并保存
    output_path = provider.infer_output_path()
    modified_count = provider.apply_and_save(modifications, output_path)

    if output_txt:
        summary = (
            f"处理完成\n"
            f"总段落数：{total_paragraphs}\n"
            f"修改段落：{modified_count}\n"
            f"输出文件：{output_path}\n"
        )
        save_to_txt(summary, output_txt, title="=" * 80, mode='a')
        print(f"结果: {output_txt}")

    print(f"保存: {output_path}")
    return total_paragraphs, modified_count


def apply_txt_to_document(provider: DocumentProvider, txt_file: str) -> Tuple[int, int]:
    """
    从 TXT 文件解析修改记录并应用到文档，支持任意文档格式

    Args:
        provider: 文档提供者实例
        txt_file: TXT 文件路径（包含修改记录）

    Returns:
        Tuple[int, int]: (解析的修改记录数, 实际修改的段落数)
    """
    if not os.path.exists(txt_file):
        print(f"[错误] TXT 文件不存在：{txt_file}")
        return 0, 0

    modifications = _parse_txt(txt_file)
    if not modifications:
        print("[信息] 未找到任何修改记录")
        return 0, 0

    print(f"[信息] 解析到 {len(modifications)} 个段落修改记录")
    output_path = provider.infer_output_path()
    modified_count = provider.apply_and_save(modifications, output_path)

    print(f"保存: {output_path}")
    return len(modifications), modified_count


def apply_txt_to_document_with_output(
    provider: DocumentProvider, 
    txt_file: str, 
    output_path: str
) -> Tuple[int, int]:
    """
    从 TXT 文件解析修改记录并应用到文档，直接保存到指定路径
    **即使没有修改记录，也会生成一个和源文件相同的DOCX**

    Args:
        provider: 文档提供者实例
        txt_file: TXT 文件路径（包含修改记录）
        output_path: 输出文件路径（直接保存到该路径）

    Returns:
        Tuple[int, int]: (解析的修改记录数, 实际修改的段落数)
    """
    if not os.path.exists(txt_file):
        print(f"[错误] TXT 文件不存在：{txt_file}")
        return 0, 0

    modifications = _parse_txt(txt_file)
    
    if not modifications:
        print("[信息] 未找到任何修改记录，将生成与源文件相同的副本")
    
    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    modified_count = provider.apply_and_save(modifications, output_path)

    print(f"[完成] 已保存: {output_path}，修改 {modified_count} 个段落")
            
    return len(modifications), modified_count


__all__ = [
    'check_paragraph',
    'process_document',
    'apply_txt_to_document',
    'apply_txt_to_document_with_output',
    '_parse_modified_text',
]
