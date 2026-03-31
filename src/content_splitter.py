#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内容分段工具模块
提供按章节分段、按字符数分段等功能
"""
import re
from typing import List, Dict


def is_chapter_title(text: str) -> bool:
    """
    判断是否是章节标题

    Args:
        text: 待判断的文本

    Returns:
        bool: 是否是章节标题
    """
    text = text.strip()
    patterns = [
        r'^第[一二三四五六七八九十\d]+章',  # 第X章
        r'^Chapter\s+\d+',  # Chapter X
        r'^\d+\.\s+',  # 1. 2. 等编号格式
        r'^第 \d+ 节',  # 第 X 节
    ]
    for pattern in patterns:
        if re.match(pattern, text, re.IGNORECASE):
            return True
    return False


def is_table_of_contents(line: str) -> bool:
    """
    判断是否是目录内容（避免将目录中的章节标题误认为是真正章节）

    Args:
        line: 文本行

    Returns:
        bool: 是否是目录内容
    """
    # 目录常见标识
    toc_keywords = ['目录', '目  录', '目录CONTENTS', 'CONTENTS', 'Contents']

    # 简单判断：如果包含"目录"且后面跟着章节标题，可能是目录
    stripped = line.strip()
    for keyword in toc_keywords:
        if keyword in stripped.upper():
            return True

    # 如果行包含页码格式（如 "... 5" 或 "...123"），可能是目录
    if re.search(r'\.{3,}\s*\d+$', stripped) or re.search(r'\.{3,}\s*$', stripped):
        return True

    return False


def extract_chapters_from_toc(content: str) -> List[Dict[str, str]]:
    """
    从目录中提取章节信息

    Args:
        content: 文档内容

    Returns:
        List[Dict]: 章节标题列表，包含 title 和 page_number
    """
    chapters = []
    lines = content.split('\n')

    # 查找目录区域
    toc_start = -1
    for i, line in enumerate(lines):
        if is_table_of_contents(line):
            toc_start = i
            break

    if toc_start == -1:
        return []  # 没有找到目录

    # 从目录区域提取章节信息
    for i in range(toc_start + 1, min(toc_start + 100, len(lines))):
        line = lines[i].strip()
        if not line:
            continue

        # 匹配 "第X章 标题 页码" 或 "第X章\t标题\t页码"
        # 匹配数字编号格式（如 "1.1 标题 页码"）
        patterns = [
            r'^第[一二三四五六七八九十\d]+章\s+(.+?)\s+\d+$',
            r'^\d+\.\d+\s+(.+?)\s+\d+$',
            r'^第[一二三四五六七八九十\d]+节\s+(.+?)\s+\d+$',
        ]

        for pattern in patterns:
            match = re.match(pattern, line)
            if match:
                title = match.group(1).strip()
                # 移除可能的多余页码信息
                # 只保留主要章节（如"第1章"、"第2章"等）
                if re.match(r'^第[一二三四五六七八九十\d]+章', line):
                    chapters.append({'title': title})
                elif re.match(r'^\d+\.\d+', line):
                    # 小节标题，暂不处理
                    pass
                break

        # 如果遇到明显的正文内容（长段落），停止解析目录
        if len(line) > 50 and not is_chapter_title(line) and '参考文献' not in line:
            break

    return chapters


def split_content_by_chapters(content: str) -> List[Dict[str, str]]:
    """
    按章节分割文档内容（跳过目录）
    改进版：先从目录提取章节结构，然后在正文中定位章节内容

    Args:
        content: 原始文档内容

    Returns:
        List[Dict]: 章节列表，每个章节包含 title 和 content
    """
    # 首先尝试从目录提取章节信息
    toc_chapters = extract_chapters_from_toc(content)

    if not toc_chapters:
        # 如果没有找到目录，使用原始方法
        return split_content_by_chapters_original(content)

    # 在正文中查找章节标题的位置
    lines = content.split('\n')
    chapter_positions = []

    for chapter in toc_chapters:
        chapter_title = chapter['title']
        for i, line in enumerate(lines):
            stripped = line.strip()
            # 匹配章节标题（考虑可能的空格和格式差异）
            if chapter_title in stripped or stripped.startswith(chapter_title):
                chapter_positions.append({
                    'title': chapter_title,
                    'position': i
                })
                break

    # 如果没有找到章节位置，返回原始方法
    if not chapter_positions:
        return split_content_by_chapters_original(content)

    # 按位置分割内容
    chapters = []
    for i, pos in enumerate(chapter_positions):
        title = pos['title']
        start_pos = pos['position']
        if i < len(chapter_positions) - 1:
            end_pos = chapter_positions[i + 1]['position']
        else:
            end_pos = len(lines)

        chapter_content = '\n'.join(lines[start_pos:end_pos])
        chapters.append({'title': title, 'content': chapter_content})

    return chapters


def split_content_by_chapters_original(content: str) -> List[Dict[str, str]]:
    """
    原始的章节分割方法（向后兼容）

    Args:
        content: 原始文档内容

    Returns:
        List[Dict]: 章节列表，每个章节包含 title 和 content
    """
    chapters = []
    lines = content.split('\n')
    current_chapter = "序言"
    current_content = []

    # 标记是否在目录中
    in_toc = False

    for line in lines:
        stripped = line.strip()

        # 检查是否是目录
        if is_table_of_contents(line):
            in_toc = True
            continue

        # 如果在目录中，跳过所有内容直到遇到真正的章节（内容较长的段落）
        if in_toc:
            # 如果遇到一个较长的段落（假设是正文开始），退出目录模式
            if len(stripped) > 50 and not is_chapter_title(stripped):
                in_toc = False
            else:
                continue

        # 检查是否是章节标题
        if is_chapter_title(stripped):
            # 保存前一个章节
            if current_content:
                chapters.append({
                    'title': current_chapter,
                    'content': '\n'.join(current_content)
                })
            current_chapter = stripped
            current_content = []
        else:
            current_content.append(line)

    # 保存最后一个章节
    if current_content:
        chapters.append({
            'title': current_chapter,
            'content': '\n'.join(current_content)
        })

    return chapters


__all__ = [
    'split_content_by_chapters',
]

