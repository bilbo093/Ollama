#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内容分段工具模块
提供按章节分段、按字符数分段等功能
"""
import re
from pathlib import Path
from typing import List, Dict, Optional


def is_table_of_contents(text: str) -> bool:
    """
    判断是否是目录内容

    判断标准（同时满足）：
    1. 段落中没有中英文逗号
    2. 以数字结尾
    3. 去除所有标点符号后不超过 20 个字符

    Args:
        text: 文本段落

    Returns:
        bool: 是否是目录内容
    """
    stripped = text.strip()
    if not stripped:
        return False

    # 1. 没有中英文逗号
    if ',' in stripped or '，' in stripped:
        return False

    # 2. 以数字结尾
    if not re.search(r'\d+$', stripped):
        return False

    # 3. 去除所有标点符号后不超过 100 个字符
    clean_text = re.sub(r'[^\w\s]', '', stripped)
    if len(clean_text.replace(' ', '')) > 100:
        return False

    return True


def extract_chapters_from_toc(lines: List[str]) -> Optional[Dict]:
    """
    从目录中提取章节信息
    
    目录范围定义：
    - 从第一次符合 is_table_of_contents 的行开始
    - 连续符合的行都属于目录
    - 一旦遇到不符合的行，目录结束

    Args:
        lines: 文档内容按行分割后的列表

    Returns:
        Dict: 包含 chapters, toc_start, toc_end
    """
    chapters = []
    toc_start = -1
    toc_end = -1
    in_toc = False

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            if in_toc:
                continue
            continue
        
        is_toc_line = is_table_of_contents(stripped)
        
        if is_toc_line and not in_toc:
            toc_start = i
            in_toc = True
        
        if in_toc:
            if is_toc_line:
                title = stripped
                title = re.sub(r'\s+\d+$', '', title).strip()
                
                if not re.match(r'^\d+\.\d+', title):
                    match1 = re.match(r'^第[一二三四五六七八九十\d]+章\s+(.+)', title)
                    if match1:
                        title = match1.group(1)
                    match2 = re.match(r'^Chapter\s+\d+\s+(.+)', title, re.IGNORECASE)
                    if match2:
                        title = match2.group(1)

                    title = title.replace('.', '').strip()
                    if title:
                        chapters.append({'title': title, 'position': i})
                toc_end = i
            else:
                break
    
    if toc_start == -1:
        return None

    return {
        'chapters': chapters,
        'toc_start': toc_start,
        'toc_end': toc_end
    }


def split_content_by_chapters(content: str) -> List[Dict[str, str]]:
    """
    按章节分割文档内容
    先从目录提取章节结构，然后在正文中定位章节内容

    Args:
        content: 原始文档内容

    Returns:
        List[Dict]: 章节列表，每个章节包含 title 和 content
    """
    lines = content.split('\n')

    toc_data = extract_chapters_from_toc(lines)

    if not toc_data:
        return []

    toc_chapters = toc_data['chapters']
    toc_start = toc_data['toc_start']
    toc_end = toc_data['toc_end']

    chapter_positions = []

    if toc_start > 0:
        pre_content = '\n'.join(lines[0:toc_start])
        if pre_content.strip():
            chapter_positions.append({
                'title': '摘要/前言',
                'position': 0
            })

    for idx, chapter in enumerate(toc_chapters):
        chapter_title = chapter['title']

        if chapter_positions and chapter_positions[-1]['position'] == 0:
            search_start = max(0, toc_end)
        elif idx == 0:
            search_start = max(0, toc_end)
        else:
            search_start = chapter_positions[-1]['position'] + 1

        search_end = len(lines)

        matched_positions = []

        for i in range(search_start, search_end):
            if toc_start != -1 and toc_start <= i <= toc_end:
                continue

            line = lines[i]
            stripped = line.strip()

            if stripped == chapter_title:
                matched_positions.append(i)
            elif chapter_title in stripped and len(stripped) <= len(chapter_title) + 10:
                matched_positions.append(i)

        if matched_positions:
            pos = matched_positions[0]
            chapter_positions.append({
                'title': chapter_title,
                'position': pos
            })

    if not chapter_positions:
        return []

    chapters = []

    for i, chapter in enumerate(chapter_positions):
        title = chapter['title']
        title_pos = chapter['position']
        start_pos = title_pos + 1

        if i < len(chapter_positions) - 1:
            end_pos = chapter_positions[i + 1]['position']
        else:
            end_pos = len(lines)

        chapter_lines = lines[start_pos:end_pos]
        chapter_content = '\n'.join(chapter_lines)
        chapters.append({'title': title, 'content': chapter_content})

    reference_idx = -1
    for i, chapter in enumerate(chapters):
        if '参考文献' in chapter['title']:
            reference_idx = i
            break
    
    if reference_idx != -1:
        chapters = chapters[:reference_idx]

    return chapters


__all__ = [
    'split_content_by_chapters',
]


