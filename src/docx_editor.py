#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DOCX 文件编辑器
逐段处理 DOCX 文件，直接应用语法检查结果
"""

import os
import re
from typing import Tuple, List, Dict
from docx import Document
from ollama_processor import chat_streaming
from config import DEFAULT_MODEL, PROCESSOR_CONFIGS
from file_io import save_to_txt
from content_splitter import is_table_of_contents, is_chapter_title


def is_references_section(text: str) -> bool:
    """
    判断是否是参考文献章节

    Args:
        text: 待判断的文本

    Returns:
        bool: 是否是参考文献章节
    """
    text = text.strip()
    references_patterns = [
        r'^参考文献',  # 参考文献
        r'^参考文献\s*\[\d+\]',  # 参考文献 [1]
        r'^References$',  # References
        r'^References\s*\[\d+\]',  # References [1]
        r'^BIBLIOGRAPHY',  # BIBLIOGRAPHY
    ]
    for pattern in references_patterns:
        if re.match(pattern, text, re.IGNORECASE):
            return True
    return False


def _should_skip_paragraph(text: str) -> Tuple[bool, str]:
    """
    判断段落是否应该跳过

    Args:
        text: 段落文本

    Returns:
        Tuple[bool, str]: (是否跳过, 跳过原因)
    """
    text_stripped = text.strip()

    # 1. 跳过空段落
    if not text_stripped:
        return True, "空段落"

    # 2. 跳过过短的段落（少于50个字符）
    if len(text_stripped) < 50:
        return True, "段落过短"

    # 3. 跳过纯 LaTeX 公式段落
    # 检查段落是否主要由 LaTeX 公式组成（以 $ 或 \(\) 或 \[\] 包围）
    latex_pattern = r'^\s*([$\[\]\\].*[$\[\]\\]|\\[a-zA-Z]+\{.*\}|\\[a-zA-Z]+\s)+\s*$'
    if re.match(latex_pattern, text_stripped):
        return True, "纯 LaTeX 公式"

    # 4. 跳过目录内容
    if is_table_of_contents(text):
        return True, "目录内容"

    # 5. 跳过章节标题
    if is_chapter_title(text):
        return True, "章节标题"

    return False, ""


def check_paragraph(paragraph_text: str) -> Tuple[str, str, List[Dict]]:
    """
    检查单个段落，返回原文、修改后的内容和修改建议列表

    Args:
        paragraph_text: 段落文本

    Returns:
        Tuple[str, str, List[Dict]]: (原文, 修改后的内容, 修改建议列表)
            如果不需要修改，修改后的内容与原文相同，修改建议列表为空
    """
    config = PROCESSOR_CONFIGS['grammar']

    # 构建提示词
    prompt = config['prompt_template'].format(content=paragraph_text)

    # 构建消息
    messages = [config['role'], {'role': 'user', 'content': prompt}]

    # 调用 Ollama（流式显示）
    result = chat_streaming(model=DEFAULT_MODEL, messages=messages).strip()

    # 解析结果 - 新格式
    corrected_text, modifications = _parse_modifications(result, paragraph_text)

    return paragraph_text, corrected_text, modifications


def _parse_modifications(result: str, original_text: str) -> Tuple[str, List[Dict]]:
    """
    从 Ollama 返回结果中解析修改后的文本和修改建议（新格式）

    Args:
        result: Ollama 返回的完整结果
        original_text: 原始段落文本

    Returns:
        Tuple[str, List[Dict]]: (修改后的文本, 修改建议列表)
            修改建议列表每个包含:
            - type: 错误类型（如：标点误用）
            - original: 原句片段
            - corrected: 修改后的片段
            - reason: 修改原因
    """
    # 检查是否未发现错误
    if "本章内容质量很高，未发现错误。" in result or "本章内容质量很高，未发现明显的语法或标点错误。" in result:
        return original_text, []

    # 检查是否有 ###MODIFIED_TEXT### 分隔符
    if "###MODIFIED_TEXT###" not in result:
        # 没有分隔符，返回原文，不应用任何修改
        return original_text, []

    # 解析第一部分：修改后的文本
    corrected_text = original_text
    if "###MODIFIED_TEXT###" in result:
        # 分割得到修改后的文本部分和修改说明部分
        parts = result.split("###MODIFIED_TEXT###")
        if len(parts) > 1:
            # 提取修改后的文本（直到下一部分开始）
            modified_part = parts[1].strip()
            # 如果有修改说明部分，分割出来
            if "**[" in modified_part:
                lines = modified_part.split('\n')
                # 找到第一个以 **[ 开头的行
                for i, line in enumerate(lines):
                    if line.strip().startswith('**['):
                        corrected_text = '\n'.join(lines[:i]).strip()
                        break
                else:
                    # 没找到，整个都是修改后的文本
                    corrected_text = modified_part
            else:
                corrected_text = modified_part

    # 解析第二部分：修改说明
    modifications = []
    lines = result.split('\n')
    for line in lines:
        line = line.strip()
        # 匹配格式：**[错误类型]** 原句 -> 修改后（原因）
        match = re.match(r'^\*\*\[([^\]]+)\]\*\*\s*(.+?)\s*->\s*(.+?)\s*\((.+)\)', line)
        if match:
            error_type = match.group(1).strip()
            original = match.group(2).strip()
            corrected = match.group(3).strip()
            reason = match.group(4).strip()

            modifications.append({
                'type': error_type,
                'original': original,
                'corrected': corrected,
                'reason': reason
            })

    return corrected_text, modifications


def _replace_text_in_runs(para, old_text: str, new_text: str) -> bool:
    """
    在段落的 runs 中替换文本（支持跨 run）

    Args:
        para: 段落对象
        old_text: 要替换的文本
        new_text: 替换后的文本

    Returns:
        bool: 是否成功替换
    """
    # 先尝试在单个 run 中替换
    for run in para.runs:
        if old_text in run.text:
            run.text = run.text.replace(old_text, new_text)
            return True

    # 如果单个 run 中没找到，尝试跨 run 替换
    full_text = ''.join(run.text for run in para.runs)
    if old_text not in full_text:
        return False

    # 找到替换的位置
    start_pos = full_text.find(old_text)
    end_pos = start_pos + len(old_text)

    # 找到对应的 run 和位置
    current_pos = 0
    for i, run in enumerate(para.runs):
        run_end = current_pos + len(run.text)

        # 检查是否在当前 run 中
        if start_pos < run_end:
            # 计算在当前 run 中的位置
            run_start = max(0, start_pos - current_pos)
            run_end_pos = min(len(run.text), end_pos - current_pos)

            # 替换文本
            before = run.text[:run_start]
            after = run.text[run_end_pos:]

            if end_pos > run_end:
                # 跨越多个 run，需要处理
                run.text = before + new_text

                # 清除后续 run 中的文本
                for j in range(i + 1, len(para.runs)):
                    para.runs[j].text = ''
            else:
                # 在单个 run 中
                run.text = before + new_text + after

            return True

        current_pos = run_end

    return False


def process_docx_paragraphs(input_docx: str, output_docx: str, output_txt: str | None = None) -> Tuple[int, int]:
    """
    逐段处理 DOCX 文件，应用语法检查修改

    Args:
        input_docx: 输入 DOCX 文件路径
        output_docx: 输出 DOCX 文件路径
        output_txt: 语法检查结果 TXT 文件路径（可选），保存完整的修改建议

    Returns:
        Tuple[int, int]: (处理的总段落数, 修改的段落数)
    """
    if not os.path.exists(input_docx):
        print(f"[错误] 输入文件不存在：{input_docx}")
        return 0, 0

    doc = Document(input_docx)

    total_paragraphs = len(doc.paragraphs)
    modified_count = 0
    skipped_count = 0

    # 找到最后一个"参考文献"段落的位置
    last_references_idx = -1
    for idx, para in enumerate(doc.paragraphs):
        if is_references_section(para.text.strip()):
            last_references_idx = idx

    # 确定处理的段落范围（参考文献段落之前）
    process_until = last_references_idx if last_references_idx != -1 else total_paragraphs

    # 初始化 txt 文件（如果指定）
    if output_txt:
        save_to_txt("语法检查结果\n\n", output_txt, title="=" * 80, mode='w')

    # 逐段处理（只处理参考文献之前的段落）
    for idx, para in enumerate(doc.paragraphs[:process_until], 1):
        para_text = para.text.strip()

        # 检查是否应该跳过该段落
        should_skip, skip_reason = _should_skip_paragraph(para_text)
        if should_skip:
            skipped_count += 1
            continue

        # 检查段落
        original, corrected, modifications = check_paragraph(para_text)

        # 如果需要修改，直接应用，不输出提示
        if corrected != original:
            _replace_text_in_runs(para, original, corrected)
            modified_count += 1

        # 每处理完一个段落，立即写入 txt 文件
        if output_txt:
            _save_modifications_to_txt(output_txt, idx, para_text, modifications)

    # 保存修改后的文档
    doc.save(output_docx)

    # 完成 txt 文件
    if output_txt:
        summary = (
            f"处理完成\n"
            f"总段落数：{total_paragraphs}\n"
            f"处理段落：{process_until}\n"
            f"跳过段落：{skipped_count}\n"
            f"修改段落：{modified_count}\n"
            f"保持不变：{process_until - skipped_count - modified_count}\n"
        )
        save_to_txt(summary, output_txt, title="=" * 80, mode='a')

    # 处理完成，输出结果
    print(f"处理完成！共处理 {process_until} 个段落，修改 {modified_count} 个")
    print(f"保存: {output_docx}")
    if output_txt:
        print(f"结果: {output_txt}")

    return process_until, modified_count


def _save_modifications_to_txt(txt_file: str, para_idx: int, para_text: str, modifications: List[Dict]):
    """
    将修改建议保存到 txt 文件

    Args:
        txt_file: txt 文件路径
        para_idx: 段落索引
        para_text: 原始段落文本
        modifications: 修改建议列表
    """
    content = f"{'=' * 60}\n"
    content += f"段落 {para_idx}\n"
    content += f"{'=' * 60}\n"
    content += f"原始内容：\n{para_text}\n\n"

    if not modifications:
        content += "本章内容质量很高，未发现错误。\n"
    else:
        for i, mod in enumerate(modifications, 1):
            content += f"**[{mod['type']}]** {mod['original']} -> {mod['corrected']}（{mod['reason']}）\n"

    save_to_txt(content, txt_file, title="", mode='a')


__all__ = [
    'check_paragraph',
    'process_docx_paragraphs',
]
