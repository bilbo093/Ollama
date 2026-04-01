#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DOCX 文件编辑器
根据语法检查结果修改 DOCX 文件
"""

import os
import re
from typing import Dict, List
from docx import Document


def parse_grammar_check_file(grammar_file: str) -> List[Dict]:
    """
    解析语法检查结果文件，提取修改建议

    Args:
        grammar_file: 语法检查结果文件路径

    Returns:
        List[Dict]: 修改建议列表，每个元素只包含:
            - chapter_title: 章节标题
            - original: 原句
            - corrected: 修改后的句子
    """
    modifications = []

    if not os.path.exists(grammar_file):
        print(f"[警告] 语法检查文件不存在：{grammar_file}")
        return modifications

    with open(grammar_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 按章节分割
    chapter_pattern = r'^(.+)\n(?=-{3,})'
    chapters = re.split(chapter_pattern, content, flags=re.MULTILINE)

    current_chapter = "未命名章节"
    for i in range(1, len(chapters), 2):
        if i < len(chapters):
            current_chapter = chapters[i].strip()
            chapter_content = chapters[i + 1] if i + 1 < len(chapters) else ""

            # 直接解析整个内容，提取所有原句和修改配对
            section_mods = _parse_modifications_from_content(chapter_content, current_chapter)
            modifications.extend(section_mods)

    return modifications


def _parse_modifications_from_content(content: str, chapter_title: str) -> List[Dict]:
    """
    从内容中解析修改建议（简化版：只提取原句和修改的配对）

    Args:
        content: 章节内容
        chapter_title: 章节标题

    Returns:
        List[Dict]: 修改建议列表，只包含章节、原句、修改
    """
    modifications = []

    # 统一模式：直接匹配原句和修改的配对
    # 匹配：- **原句**：xxx\n- **修改**：xxx 或 - **原句**：xxx\n- **修改建议**：xxx
    # 需要跳过中间的 - **原因**：xxx 或其他内容
    pattern = r'- \*\*原句\*\*[：:](.+?)(?=\n- \*\*(?:修改|修改建议)\*\*[：:])\n- \*\*(?:修改|修改建议)\*\*[：:](.+?)(?=\n- \*\*(?:原因|原句)\*\*[：:]|\n\d+\.|\n###|$|---)'

    matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)

    for match in matches:
        original = match.group(1).strip()
        corrected = match.group(2).strip()

        modifications.append({
            'chapter_title': chapter_title,
            'original': original,
            'corrected': corrected
        })

    return modifications


def _find_text_in_para(para_text: str, original: str) -> tuple[bool, str, str]:
    """
    在段落文本中查找原句，支持精确匹配和模糊匹配

    Args:
        para_text: 段落文本
        original: 原句

    Returns:
        tuple: (是否找到, 实际匹配的文本, 匹配类型)
            - 是否找到: True 或 False
            - 实际匹配的文本: 匹配到的文本片段
            - 匹配类型: 'exact' 精确匹配, 'stripped' 去标点匹配, 'no_dots' 去省略号匹配, 'fuzzy' 模糊匹配
    """
    # 1. 精确匹配
    if original in para_text:
        return True, original, 'exact'

    # 2. 去除首尾标点符号后匹配
    original_stripped = original.strip('，。！？；：""''、·「」『』【】《》（）()[]{}')
    if original_stripped != original and original_stripped in para_text:
        return True, original_stripped, 'stripped'

    # 3. 去除省略号后匹配
    original_no_dots = original.replace('...', '').strip(' ，。！？；：""''、·「」『』【】《》（）()[]{}')
    if original_no_dots in para_text:
        return True, original_no_dots, 'no_dots'

    # 4. 模糊匹配：查找原句中较长的连续子串
    # 去除标点和空格后进行比较
    punctuation = '，。！？；：""''、·「」『』【】《》（）()[]{}... '
    original_clean = ''.join(c for c in original if c not in punctuation)
    para_clean = ''.join(c for c in para_text if c not in punctuation)

    # 查找至少15个字符的匹配子串
    min_match_length = 15
    if len(original_clean) >= min_match_length:
        best_match = ''
        best_pos = -1

        # 在清理后的段落中查找最长的匹配子串
        for i in range(len(original_clean) - min_match_length + 1):
            for j in range(len(original_clean), i + min_match_length, -1):
                substring = original_clean[i:j]
                if substring in para_clean:
                    if len(substring) > len(best_match):
                        best_match = substring
                        # 在原始段落中找到这个子串的位置
                        pos = _find_original_position(para_text, para_clean, substring)
                        best_pos = pos
                    break
            if best_match:
                break

        if best_match:
            # 在原始段落中找到对应的文本片段
            if best_pos >= 0:
                matched_text = para_text[best_pos:best_pos + len(best_match)]
                return True, matched_text, 'fuzzy'

    return False, '', ''


def _find_original_position(para_text: str, para_clean: str, clean_substring: str) -> int:
    """
    在原始段落中查找清理后的子串对应的位置

    Args:
        para_text: 原始段落文本
        para_clean: 清理后的段落文本
        clean_substring: 清理后的子串

    Returns:
        int: 在段落中的位置，-1 表示未找到
    """
    # 在清理后的段落中找到子串的位置
    pos_in_clean = para_clean.find(clean_substring)
    if pos_in_clean == -1:
        return -1

    # 将清理后的位置映射回原始段落
    clean_count = 0
    for i, char in enumerate(para_text):
        if char not in '，。！？；：""''、·「」『』【】《》（）()[]{}... ':
            if clean_count == pos_in_clean:
                return i
            clean_count += 1

    return -1


def apply_modifications_to_docx(input_docx: str, output_docx: str, modifications: List[Dict]) -> tuple[List[Dict], int]:
    """
    将修改建议应用到 DOCX 文件（保留格式）

    Args:
        input_docx: 输入 DOCX 文件路径
        output_docx: 输出 DOCX 文件路径
        modifications: 修改建议列表

    Returns:
        tuple: (处理结果列表, 成功应用的数量)
            - 处理结果列表: 每个元素包含章节、原句、修改、匹配类型、状态
            - 成功应用的数量: 整数
    """
    if not os.path.exists(input_docx):
        print(f"[错误] 输入文件不存在：{input_docx}")
        return [], 0

    # 不再过滤，直接应用所有修改建议
    if not modifications:
        print("[信息] 没有需要应用的修改")
        return [], 0

    print(f"[信息] 正在处理 {len(modifications)} 条修改建议...")

    # 加载文档
    doc = Document(input_docx)

    # 存储处理结果
    results = []

    # 遍历所有段落，查找并应用修改
    for para in doc.paragraphs:
        para_text = para.text
        for mod in modifications:
            if not mod.get('processed', False):
                original = mod['original']
                corrected = mod['corrected']

                # 使用查找函数（支持模糊匹配）
                found, matched_text, match_type = _find_text_in_para(para_text, original)

                if found:
                    # 执行替换
                    _replace_text_in_para(para, matched_text, corrected)

                    # 记录处理结果
                    results.append({
                        'chapter': mod['chapter_title'],
                        'original': original,
                        'corrected': corrected,
                        'match_type': match_type,
                        'status': '成功'
                    })

                    # 标记为已处理
                    mod['processed'] = True
                else:
                    # 记录未找到的修改
                    results.append({
                        'chapter': mod['chapter_title'],
                        'original': original,
                        'corrected': corrected,
                        'match_type': '未找到',
                        'status': '失败'
                    })

                    # 标记为已处理（避免重复检查）
                    mod['processed'] = True

    # 保存修改后的文档
    doc.save(output_docx)

    # 输出处理结果总览
    print(f"\n{'=' * 80}")
    print(f"[处理结果总览]")
    print(f"{'=' * 80}")

    success_count = 0
    fail_count = 0

    for i, result in enumerate(results, 1):
        status_icon = "✓" if result['status'] == '成功' else "✗"
        print(f"{i}. {status_icon} [{result['chapter']}] - {result['match_type']}")
        print(f"   原句: {result['original'][:60]}...")
        print(f"   修改: {result['corrected'][:60]}...")

        if result['status'] == '成功':
            success_count += 1
        else:
            fail_count += 1
        print(f"   {'-' * 80}")

    print(f"{'=' * 80}")
    print(f"[统计] 共处理 {len(results)} 条建议：成功 {success_count} 条，失败 {fail_count} 条")
    print(f"[完成] 修改后的文档已保存到：{output_docx}")

    return results, success_count


def _replace_text_in_para(para, old_text: str, new_text: str):
    """
    在段落中替换文本，保留原有格式

    Args:
        para: 段落对象
        old_text: 要替换的文本
        new_text: 替换后的文本
    """
    # 遍历段落中的所有 run
    for run in para.runs:
        if old_text in run.text:
            # 在当前 run 中找到所有匹配位置
            run.text = run.text.replace(old_text, new_text)
            break

    # 如果在单个 run 中没有找到，尝试跨 run 替换
    if old_text not in ''.join(run.text for run in para.runs):
        full_text = ''.join(run.text for run in para.runs)
        if old_text in full_text:
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
                            end_pos -= len(para.runs[j].text)
                    else:
                        # 在单个 run 中
                        run.text = before + new_text + after

                    break

                current_pos = run_end


def generate_corrected_docx(grammar_file: str, input_docx: str, output_docx: str) -> tuple[List[Dict], int]:
    """
    根据语法检查结果生成修改后的 DOCX 文件（主入口函数）

    Args:
        grammar_file: 语法检查结果文件路径
        input_docx: 输入 DOCX 文件路径
        output_docx: 输出 DOCX 文件路径

    Returns:
        tuple: (处理结果列表, 成功应用的数量)
    """
    print(f"[开始] 解析语法检查结果：{grammar_file}")

    # 解析语法检查结果
    modifications = parse_grammar_check_file(grammar_file)

    if not modifications:
        print("[信息] 未发现任何修改建议")
        return [], 0

    # 统计各章节的修改数量
    chapter_stats = {}
    for mod in modifications:
        chapter = mod['chapter_title']
        if chapter not in chapter_stats:
            chapter_stats[chapter] = 0
        chapter_stats[chapter] += 1

    print(f"[统计] 发现 {len(modifications)} 条修改建议")
    for chapter, count in chapter_stats.items():
        print(f"  - {chapter}: {count} 条")

    # 应用修改
    results, success_count = apply_modifications_to_docx(
        input_docx,
        output_docx,
        modifications
    )

    return results, success_count


__all__ = [
    'parse_grammar_check_file',
    'apply_modifications_to_docx',
    'generate_corrected_docx',
]
