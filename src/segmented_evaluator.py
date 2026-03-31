#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分段评价处理器
实现三阶段文档评价：分段处理 -> 分段汇总 -> 最终评价
"""
from typing import List, Dict, Tuple
from content_splitter import split_content_by_chapters
from ollama_processor import TextProcessor
from config import PROCESSOR_CONFIGS


def split_content_by_chunks(content: str, chunk_size: int = 30000, overlap: int = 3000) -> List[str]:
    """
    按字符数分段（带重叠）

    Args:
        content: 原始内容
        chunk_size: 每块大小（字符数，默认 30000）
        overlap: 重叠大小（字符数，默认 3000）

    Returns:
        List[str]: 分段列表
    """
    chunks = []
    start = 0
    content_length = len(content)

    while start < content_length:
        end = min(start + chunk_size, content_length)
        chunks.append(content[start:end])

        # 移动起始位置（减去重叠部分）
        start = end - overlap
        if start < 0:
            start = 0

    return chunks


def evaluate_chunk(chunk: str, chunk_index: int) -> Dict[str, str]:
    """
    评价单个文本块

    Args:
        chunk: 文本块内容
        chunk_index: 块索引

    Returns:
        Dict: 包含该块的评价信息
    """
    prompt_template = """请对以下文本块进行评价，该文本块是文档的第 {chunk_index} 部分。

文本块内容：
{content}

请按以下维度进行评价：
1. 存在的问题
2. 优点
3. 关键点（重要观点、数据、结论等）

要求：
- 客观准确，指出真实存在的问题
- 优点要具体，不要泛泛而谈
- 关键点要提炼核心内容
- 评价要简洁明了
- 只返回评价内容，不要添加其他说明
"""

    role = {
        'role': 'system',
        'content': '你是一位学术评审专家，擅长客观评价学术论文的质量和问题。'
    }

    processor = TextProcessor(role, prompt_template)
    result = processor.process_content(content=chunk, chunk_index=chunk_index)

    return {
        'chunk_index': chunk_index,
        'content': result
    }


def aggregate_evaluations(evaluations: List[Dict[str, str]]) -> Dict[str, str]:
    """
    汇总所有块的评价，去重并按维度整理

    Args:
        evaluations: 所有块的评价列表

    Returns:
        Dict: 按维度（选题、基础、创新、规范）整理的结构化信息
    """
    prompt_template = """以下是文档各个分段的评价结果：

{evaluations_text}

请对这些评价进行汇总整理：
1. 去重处理（重叠区域可能被提及两次）
2. 按以下维度整理成结构化信息：
   - 选题：前沿性、开创性、理论意义、现实意义、现状总结情况
   - 基础知识与科研能力：理论基础、专业知识、结构合理性、研究方法、引证资料、科研能力
   - 创新性与论文价值：学科贡献、科学发现、解决问题作用、影响和贡献
   - 论文规范性：引文规范性、学风严谨性、结构逻辑性、文字表述

要求：
- 合并相似观点，避免重复
- 突出主要问题和优点
- 每个维度下分"问题"和"优点"两部分
- 只返回汇总内容，不要添加其他说明
"""

    role = {
        'role': 'system',
        'content': '你是一位学术评审专家，擅长汇总整理学术评价信息。'
    }

    # 构建评价文本
    evaluations_text = ""
    for idx, eval_data in enumerate(evaluations, 1):
        evaluations_text += f"=== 分段 {idx} 评价 ===\n"
        evaluations_text += eval_data['content'] + "\n\n"

    processor = TextProcessor(role, prompt_template)
    result = processor.process_content(evaluations_text=evaluations_text)

    return result


def generate_final_evaluation(aggregated_info: str) -> Dict[str, str]:
    """
    基于汇总信息生成最终评价报告

    Args:
        aggregated_info: 汇总后的评价信息

    Returns:
        Dict: 最终评价报告（包含评分、等级、详细建议）
    """
    prompt_template = """基于以下汇总的评价信息，生成最终评价报告：

汇总信息：
{aggregated_info}

请生成一份包含以下内容的最终评价报告：
1. 综合评分（0-100分，按各维度加权计算）
2. 等级判断（A/B/C三个等级）
   - A等级：同意答辩（≥85分），优秀硕士学位论文水平，不需修改
   - B等级：修改后答辩（≥65分且<85分），硕士学位论文水平，需一定修改
   - C等级：较大修改后重审（≥60分且<65分），基本达标，需较大修改
   - <60分：未达到硕士学位论文水平
3. 各维度详细评价（选题、基础、创新、规范）
4. 总体评价
5. 修改建议（针对主要问题给出具体建议）

注意：
- 当前时间为2026年，在此之前的参考文献都是存在的
- 致谢和总结与展望不需要评价
- 评价要严格客观，不能强行润色通过
- 如果文章存在逻辑漏洞、数据缺失或格式不规范等情况，必须客观指出
"""

    role = {
        'role': 'system',
        'content': '你是一位资深学术评审专家，负责研究生学位论文的最终评审和等级判定。'
    }

    processor = TextProcessor(role, prompt_template)
    result = processor.process_content(aggregated_info=aggregated_info)

    return result


def three_stage_evaluation(content: str, chunk_size: int = 30000, overlap: int = 3000) -> Tuple[str, str, str]:
    """
    三阶段评价流程

    Args:
        content: 文档内容
        chunk_size: 每块大小（默认 30000 字符）
        overlap: 重叠大小（默认 3000 字符）

    Returns:
        Tuple: (分段评价结果, 汇总结果, 最终评价报告)
    """
    # 阶段1：分段处理
    print("\n" + "=" * 60)
    print("[阶段1] 分段处理（带重叠）")
    print("=" * 60)

    # 先按章节分割
    chapters = split_content_by_chapters(content)
    print(f"[信息] 识别到 {len(chapters)} 个章节")

    # 对每个章节进行分段（如果章节超长）
    chunk_evaluations = []
    global_chunk_index = 1

    for chapter in chapters:
        chapter_title = chapter['title']
        chapter_content = chapter['content']
        content_length = len(chapter_content)

        if content_length <= chunk_size:
            # 章节较短，整体评价
            print(f"\n[章节] {chapter_title} ({content_length} 字符) - 整体评价")
            eval_result = evaluate_chunk(chapter_content, global_chunk_index)
            chunk_evaluations.append(eval_result)
            global_chunk_index += 1
        else:
            # 章节较长，分段评价
            chunks = split_content_by_chunks(chapter_content, chunk_size, overlap)
            print(f"\n[章节] {chapter_title} ({content_length} 字符) - 分为 {len(chunks)} 块评价")

            for i, chunk in enumerate(chunks, 1):
                print(f"  [分段 {i}/{len(chunks)}] 正在评价...")
                eval_result = evaluate_chunk(chunk, global_chunk_index)
                chunk_evaluations.append(eval_result)
                global_chunk_index += 1

    print(f"\n[完成] 共完成 {len(chunk_evaluations)} 个分段评价")

    # 收集所有分段评价结果
    all_chunk_evaluations = ""
    for eval_data in chunk_evaluations:
        all_chunk_evaluations += f"=== 分段 {eval_data['chunk_index']} ===\n"
        all_chunk_evaluations += eval_data['content'] + "\n\n"

    # 阶段2：分段汇总
    print("\n" + "=" * 60)
    print("[阶段2] 分段汇总（去重并按维度整理）")
    print("=" * 60)

    aggregated_result = aggregate_evaluations(chunk_evaluations)
    print("[完成] 汇总完成")

    # 阶段3：最终评价
    print("\n" + "=" * 60)
    print("[阶段3] 最终评价报告生成")
    print("=" * 60)

    final_report = generate_final_evaluation(aggregated_result)
    print("[完成] 最终评价报告生成完毕")

    return all_chunk_evaluations, aggregated_result, final_report


__all__ = [
    'three_stage_evaluation',
    'split_content_by_chunks',
    'evaluate_chunk',
    'aggregate_evaluations',
    'generate_final_evaluation',
]
