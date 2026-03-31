#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from content_splitter import split_content_by_chapters
from file_io import read_txt_content

content = read_txt_content('input/input0330.txt')
chapters = split_content_by_chapters(content)
print(f'识别到 {len(chapters)} 个章节:')
for i, c in enumerate(chapters):
    print(f'{i+1}. {c["title"]} ({len(c["content"])} 字符)')
