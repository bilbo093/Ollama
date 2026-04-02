#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试 TXT 解析功能"""

import sys
import os
sys.path.insert(0, 'src')

from docx_editor import _parse_txt_paragraphs

txt_file = 'output/grammarccf.txt'
print(f"正在解析文件: {txt_file}")

modifications = _parse_txt_paragraphs(txt_file)

print(f"\n解析结果:")
print(f"共解析到 {len(modifications)} 个修改记录")

if modifications:
    print(f"\n前 5 个修改记录:")
    for idx in sorted(modifications.keys())[:5]:
        text = modifications[idx]
        preview = text[:80] + "..." if len(text) > 80 else text
        print(f"  段落 {idx}: {preview}")
