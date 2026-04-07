"""
提示词配置加载
从 Markdown 文件加载 role 和 prompt
保持与现有代码的向后兼容
"""
from .loader import get_prompt

# 从 Markdown 文件加载默认提示词（向后兼容）
_full_data = get_prompt('full', 'default')
ACADEMIC_SUMMARIZER_ROLE = {'role': 'system', 'content': _full_data['role']}
ACADEMIC_SUMMARIZER_PROMPT = _full_data['prompt']

_chapter_data = get_prompt('chapter', 'default')
CHAPTER_SUMMARIZER_ROLE = {'role': 'system', 'content': _chapter_data['role']}
CHAPTER_SUMMARIZER_PROMPT = _chapter_data['prompt']

_v1_data = get_prompt('paragraph', 'default')
GRAMMAR_CHECKER_ROLE = {'role': 'system', 'content': _v1_data['role']}
GRAMMAR_CHECKER_PROMPT = _v1_data['prompt']
