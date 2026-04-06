#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内容分段工具模块
提供按章节分段、按字符数分段等功能
"""
import re
from typing import List, Dict


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


def extract_chapters_from_toc(lines: List[str]) -> List[Dict[str, str]]:
    """
    从目录中提取章节信息

    Args:
        lines: 文档内容按行分割后的列表

    Returns:
        List[Dict]: 章节标题列表，包含 title 和 page_number
    """
    chapters = []

    # 查找目录区域（通过关键词定位目录标题行）
    toc_keywords = ['目录', '目 录', 'CONTENTS']
    toc_start = -1
    for i, line in enumerate(lines):
        stripped_upper = line.strip().upper()
        if any(kw in stripped_upper for kw in toc_keywords):
            toc_start = i
            break

    if toc_start == -1:
        return []  # 没有找到目录

    # 从目录区域提取章节信息
    for i in range(toc_start + 1, min(toc_start + 100, len(lines))):
        line = lines[i].strip()
        if not line:
            continue

        # 使用 is_table_of_contents 判断是否为目录条目
        if is_table_of_contents(line):
            # 提取标题：去掉末尾的数字页码
            title = re.sub(r'\s+\d+$', '', line).strip()
            # 过滤掉小节标题（如 "1.1"、"2.3" 等）
            if not re.match(r'^\d+\.\d+', title):
                # 去掉前缀（如"第X章"、"Chapter X"等）
                # 第一种：去掉"第X章"前缀
                match1 = re.match(r'^第[一二三四五六七八九十\d]+章\s+(.+)', title)
                if match1:
                    title = match1.group(1)
                # 第二种：去掉"Chapter X"前缀
                match2 = re.match(r'^Chapter\s+\d+\s+(.+)', title, re.IGNORECASE)
                if match2:
                    title = match2.group(1)

                # 清除标题中的.（点号）
                title = title.replace('.', '')
                # 去除首尾空格，确保结尾不是空格
                title = title.strip()
                chapters.append({'title': title})

        # 如果遇到明显的正文内容（长段落），停止解析目录
        if len(line) > 200 and '参考文献' not in line:
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
    # 只进行一次 split 操作
    lines = content.split('\n')

    # 首先尝试从目录提取章节信息
    toc_chapters = extract_chapters_from_toc(lines)

    if not toc_chapters:
        # 如果没有找到目录，返回空列表
        print("警告：未找到目录，无法进行章节分割")
        return []

    # 在正文中查找章节标题的位置（跳过目录区域）
    # 搜索范围分为两部分：0-toc_start（目录前）和 toc_end-文末（目录后）

    # 找到目录开始和结束的位置
    # 目录从"目录"这种单独行开始，一直到最后一个符合目录标准的行结束
    toc_start = -1
    toc_end = 0
    in_toc = False

    # 目录匹配模式：标题 + 空格/制表符 + 页码（阿拉伯数字或罗马数字）
    toc_pattern = r'^(.+?)\s+[IVXLCDM\d]+$'

    for i, line in enumerate(lines):
        if is_table_of_contents(line):
            in_toc = True
            if toc_start == -1:
                toc_start = i
            toc_end = i  # 更新目录结束位置
            continue

        if in_toc:
            # 检查是否仍符合目录标准（标题 + 空格/制表符 + 页码）
            stripped = line.strip()
            if not stripped:
                # 空行也属于目录范围的一部分
                toc_end = i
                continue

            if re.match(toc_pattern, stripped):
                # 符合目录格式，更新目录结束位置
                toc_end = i
            else:
                # 不符合目录格式，目录结束
                break

    chapter_positions = []

    for idx, chapter in enumerate(toc_chapters):
        chapter_title = chapter['title']

        # 确定搜索起始位置：如果是第一个章节，从目录结束位置开始搜索；否则从上一个章节位置后搜索
        if idx == 0:
            search_start = max(0, toc_end)
        else:
            search_start = chapter_positions[-1]['position'] + 1

        search_end = len(lines)

        # 收集所有匹配的位置（排除目录范围）
        matched_positions = []
        for i in range(search_start, search_end):
            # 跳过目录范围内的行
            if toc_start != -1 and toc_start <= i <= toc_end:
                continue

            line = lines[i]
            stripped = line.strip()

            # 第一优先级：完全匹配且长度相等
            if stripped == chapter_title:
                matched_positions.append(i)
            # 第二优先级：包含标题且长度略微增长（允许最多多10个字符）
            elif chapter_title in stripped and len(stripped) <= len(chapter_title) + 10:
                matched_positions.append(i)

        # 如果在目录后没找到，尝试在目录前查找（如"摘  要"等前置章节）
        if not matched_positions and idx == 0:
            search_start_before = 0
            search_end_before = toc_start
            for i in range(search_start_before, search_end_before):
                line = lines[i]
                stripped = line.strip()

                # 第一优先级：完全匹配且长度相等
                if stripped == chapter_title:
                    matched_positions.append(i)
                    break
                # 第二优先级：包含标题且长度略微增长（允许最多多10个字符）
                elif chapter_title in stripped and len(stripped) <= len(chapter_title) + 10:
                    matched_positions.append(i)
                    break

        if matched_positions:
            # 选择比上一个标题大的最小行号（由于search_start已确保，取第一个即可）
            pos = matched_positions[0]

            # 添加章节位置（不再在这里询问用户是否继续）
            chapter_positions.append({
                'title': chapter_title,
                'position': pos
            })
        else:
            print(f"警告：未找到章节 '{chapter_title}' 的独立标题行")

    # 如果没有找到章节位置，返回空列表
    if not chapter_positions:
        print("警告：未在正文中找到任何章节标题")
        return []

    # 按位置分割内容（章节内容从标题行的下一行开始）
    chapters = []

    # 找到目录开始位置（用于截止前置章节内容）
    toc_start_line = -1
    for i, line in enumerate(lines):
        if is_table_of_contents(line):
            toc_start_line = i
            break

    for i, pos in enumerate(chapter_positions):
        title = pos['title']
        # 章节内容从标题行的下一行开始
        start_pos = pos['position'] + 1

        if i < len(chapter_positions) - 1:
            end_pos = chapter_positions[i + 1]['position']
        else:
            end_pos = len(lines)

        # 如果是目录前的章节（如"摘  要"），内容应该在目录开始前截止
        if pos['position'] < toc_start_line and end_pos > toc_start_line:
            end_pos = toc_start_line

        # 提取章节内容，保留空行
        chapter_lines = lines[start_pos:end_pos]
        chapter_content = '\n'.join(chapter_lines)
        chapters.append({'title': title, 'content': chapter_content})

    # 打印分章结果
    print(f"\n{'='*60}")
    print(f"共分割为 {len(chapters)} 个章节：")
    print(f"{'='*60}")
    for i, chapter in enumerate(chapters, 1):
        pos = chapter_positions[i-1]
        title_pos = pos['position']
        start_pos = title_pos + 1
        if i < len(chapters):
            end_pos = chapter_positions[i]['position'] - 1
        else:
            end_pos = len(lines) - 1
        print(f"{i}. {chapter['title']} ({len(chapter['content'])} 字符) [行号: {start_pos}-{end_pos}]")
    print(f"{'='*60}\n")

    return chapters


__all__ = [
    'split_content_by_chapters',
]


