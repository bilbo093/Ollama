# CODEBUDDY.md This file provides guidance to CodeBuddy when working with code in this repository.

## 常用命令

### 安装依赖
```bash
pip install -r requirements.txt
```

### 运行主入口
```bash
# 学术摘要生成
python main.py summarizer -i input.txt -o output.txt
python main.py summarizer -i input.docx -o output.txt

# 章节总结生成
python main.py chapter -i input.txt -o output.txt
python main.py chapter -i input.docx -o output.txt

# 三阶段分段评价
python main.py evaluate -i input.txt -o output.txt
python main.py evaluate -i input.txt -o output.txt --chunk-size 30000 --overlap 3000

# 语法检查并修改 DOCX 文件
python main.py grammar -i input.docx
python main.py grammar -i input.docx -o grammar.txt
```

### 常用选项
- `--chunk-size`: 每块字符数（默认：30000，仅 evaluate 命令）
- `--overlap`: 重叠字符数（默认：3000，仅 evaluate 命令）

## 架构概览

这是一个基于 Ollama 的学术文档处理工具集，采用配置驱动的分层架构设计，支持 TXT/DOCX 文档的学术摘要生成、章节总结、三阶段分段评价和语法检查功能。

### 核心模式

**配置驱动模式**: 所有处理器统一使用 `TextProcessor` 类，通过配置的 role 和 prompt_template 实现不同的处理逻辑。`PROCESSOR_CONFIGS` 字典在 `config.py` 中集中定义所有处理器的配置。

**三阶段评价**: 针对长文档场景，采用分段处理（带重叠）→ 分段汇总（去重并按维度整理）→ 最终评价报告的三阶段流程，确保评价的全面性和准确性。

**逐段语法检查**: 直接按段落序号处理 DOCX 文件，完全避免内容匹配问题。每段独立检查并应用修改，自动跳过目录、章节标题、参考文献等特殊内容。

### 关键组件

**main.py**: 主入口文件，处理命令行参数，支持四个子命令（summarizer、chapter、evaluate、grammar），包含文件格式验证和内容读取。支持语法检查结果缓存，已存在 TXT 文件时可选择重用或重新检查。

**config.py**: 集中管理所有配置常量、角色定义和提示词模板，包括模型配置（DEFAULT_MODEL）、流式输出配置（STREAM_BUFFER_SIZE）、各种处理角色的 system prompt 以及 `PROCESSOR_CONFIGS` 字典。

**ollama_processor.py**: 定义统一的 `TextProcessor` 类和流式输出函数 `chat_streaming()`。`TextProcessor` 通过配置驱动支持不同的处理任务，提供 `process_content()` 方法处理内容。还包含 `generate_and_save_chapter_summaries()` 用于章节总结生成。内置复读检测和长度阈值保护机制。

**file_io.py**: 处理文件读取和保存，支持 TXT（UTF-8/GBK）和 DOCX 格式。包含 `read_file_content()`、`read_txt_content()`、`read_docx_content()` 和 `save_to_txt()` 等函数。

**content_splitter.py**: 内容分段工具，提供按章节分割（自动跳过目录）、按字符数分段（带重叠）等功能。包含章节标题识别、目录过滤、从目录提取章节结构等实用函数。

**segmented_evaluator.py**: 三阶段评价处理器，包含 `three_stage_evaluation()` 主流程函数，以及 `evaluate_chunk()`（分段评价）、`aggregate_evaluations()`（分段汇总）、`generate_final_evaluation()`（生成最终报告）等核心函数。

**docx_editor.py**: DOCX 文件编辑器，支持逐段语法检查和修改。包含 `process_docx()`（逐段处理）、`apply_txt_to_docx()`（从 TXT 文件应用修改）、`apply_modifications()`（应用修改到 DOCX）等函数。自动处理参考文献标记为上标格式，跳过目录、章节标题等特殊内容。

### 处理流程

1. **文档读取** - 使用 `read_file_content()` 读取文件内容，支持 TXT（UTF-8/GBK）和 DOCX 格式。

2. **内容预处理** - 对于章节总结，使用 `split_content_by_chapters()` 按章节分割（自动跳过目录）；对于三阶段评价，使用 `split_content_by_chunks()` 按字符数分段（带重叠）。

3. **提示词构建** - 处理器根据类型从 `config.py` 加载对应的 role 和 prompt template，动态填充内容。

4. **Ollama 调用** - 通过 `chat_streaming()` 进行流式输出，支持进度显示和缓冲（STREAM_BUFFER_SIZE 配置）。内置复读检测（相似度阈值 0.6，连续 5 次中断）和长度阈值保护（输入长度 × 20）。

5. **结果处理** - 保存到 `.txt` 输出文件，输出格式包含标题和分隔线。

### 特殊处理

**章节检测**: 使用正则匹配 "第 X 章"、"Chapter X"、"1. "等格式，区分章节标题和目录条目。`extract_chapters_from_toc()` 先从目录提取章节结构，然后在正文中定位章节内容。

**目录过滤**: 自动跳过目录内容，通过 `is_table_of_contents()` 函数识别目录区域。

**三阶段评价**:
- 阶段1：按章节分段评价，超长章节使用 `split_content_by_chunks()` 分割（默认每块30000字符，重叠3000字符）
- 阶段2：汇总所有分段评价，去重并按维度整理（选题、基础知识、创新性、规范性）
- 阶段3：基于汇总信息生成最终评价报告，包含评分（0-100分）、等级（A/B/C）、详细评价和修改建议

**语法检查**:
- 逐段处理 DOCX 文件，每段独立调用 Ollama 检查
- 自动跳过目录、章节标题、参考文献、空段落、短段落（<50字符）、LaTeX 公式等
- Ollama 返回格式：`###MODIFIED_TEXT###` 后接修改后的文本，`###MODIFIED_DESCRIPTION###` 后接修改说明
- 应用修改时自动将参考文献标记 [X] 设置为上标格式，并删除文中所有空格（中文写作不需要）
- 支持从已有 TXT 文件重新应用修改（`apply_txt_to_docx`），避免重复调用 Ollama
- 默认处理到参考文献段落之前

**文件格式支持**: 
- TXT 文件支持 UTF-8 和 GBK 两种常见编码格式
- DOCX 文件通过 python-docx 库提取纯文本内容，按顺序提取段落和表格

### 环境依赖

确保 Ollama 服务运行在 `http://localhost:11434`，推荐使用支持中文的模型如 `qwen3.5:4b`（通过 DEFAULT_MODEL 配置）。

依赖安装：
```bash
pip install -r requirements.txt
```

主要依赖：
- `ollama>=0.4.0`: Ollama Python SDK
- `python-docx>=1.1.0`: DOCX 文件处理

### 代码约定

- 类型提示用于所有公共函数签名
- 中文注释用于中文代码逻辑
- 所有配置集中在 `config.py`（PROCESSOR_CONFIGS 字典）
- 输出文件（`*.txt`）已加入 `.gitignore`
- src 目录通过 sys.path 自动添加到 Python 路径
