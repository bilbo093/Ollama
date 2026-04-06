# CODEBUDDY.md This file provides guidance to CodeBuddy when working with code in this repository.

## 常用命令

### 安装依赖
```bash
pip install -r requirements.txt
```

### 运行主入口
```bash
# 学术摘要生成（总结与展望章节）
python main.py summarizer -i input.txt -o output.txt
python main.py summarizer -i input.docx -o output.txt

# 章节总结生成
python main.py chapter -i input.txt -o output.txt
python main.py chapter -i input.docx -o output.txt

# 语法检查并修改（支持 TXT / DOCX）
python main.py grammar -i input.docx
python main.py grammar -i input.txt
python main.py grammar -i input.docx -o grammar.txt
```

## 架构概览

这是一个基于本地 LLM 的学术文档处理工具集，采用配置驱动的分层架构设计。支持 Ollama 和 llama.cpp（OpenAI 兼容 API）两种后端，启动时通过 API 探测自动识别。支持 TXT/DOCX 文档的学术摘要生成、章节总结和语法检查功能。

### 核心模式

**后端自动探测**: 只需配置 `BASE_URL`，通过 OpenAI 兼容协议统一调用，兼容 Ollama / llama.cpp / OpenAI / DeepSeek 等所有服务。本地服务通常无需 API Key，云服务通过 `API_KEY` 和 `MODEL_NAME` 配置。

**配置驱动模式**: 所有处理器通过 `PROCESSOR_CONFIGS` 字典统一配置，包含 role 和 prompt_template。

**DocumentProvider 抽象**: 通过抽象基类 + 工厂模式统一文档格式处理，新增格式只需实现 `DocumentProvider` 子类即可接入，无需修改业务逻辑。

**逐段语法检查**: 直接按段落序号处理文档，完全避免内容匹配问题。每段独立检查并应用修改，自动跳过目录、章节标题、参考文献等特殊内容。

### 关键组件

**main.py**: 主入口文件，处理命令行参数，支持三个子命令（summarizer、chapter、grammar），包含文件格式验证和内容读取。grammar 命令通过 `create_provider()` 工厂函数自动创建对应的 DocumentProvider。

**config.py**: 集中管理所有配置常量。`BASE_URL` 为 LLM 服务地址，`API_KEY` 和 `MODEL_NAME` 为可选的认证和模型配置（本地服务通常不需要）。`PROCESSOR_CONFIGS` 字典集中定义所有处理器的角色和提示词模板。

**ollama_processor.py**: 统一的 LLM 客户端 `LLMClient`，使用 OpenAI 兼容协议 (`/v1/chat/completions`)，兼容 Ollama / llama.cpp / OpenAI / DeepSeek 等所有服务。提供模块级便捷函数 `chat()`，内置复读检测机制（相似度阈值 0.6，连续 5 次中断）。

**document_provider.py**: 文档抽象层，定义 `DocumentProvider` 抽象基类和两个实现：
- `TxtDocumentProvider`: 按 UTF-8/GBK 读取，按行分段，输出 `_fixed.txt`
- `DocxDocumentProvider`: 通过 python-docx 读取段落，应用修改时自动将参考文献标记 [X] 设为上标格式，输出 `_fixed.docx`
- `create_provider()`: 工厂函数，根据文件扩展名自动创建对应的 Provider

**docx_editor.py**: 语法检查业务逻辑层，完全解耦于具体文档格式。包含 `process_document()`（通用语法检查流程）、`apply_txt_to_document()`（从 TXT 文件应用修改）、`_skip_para()`（段落跳过判断）等函数。通过 `DocumentProvider` 接口操作文档，不直接依赖 python-docx。

**file_io.py**: 文件读取和保存，支持 TXT（UTF-8/GBK）和 DOCX 格式。DOCX 读取时按顺序提取段落和表格内容。

**content_splitter.py**: 内容分段工具，提供按章节分割（自动跳过目录）功能。包含 `is_table_of_contents()`、`is_chapter_title()`、`extract_chapters_from_toc()` 等实用函数。

### 处理流程

1. **LLM 调用** - 通过 `LLMClient.chat()` 使用 OpenAI 兼容协议进行流式输出，支持进度显示和缓冲。内置复读检测机制。
2. **结果处理** - 保存到输出文件，grammar 命令通过 `DocumentProvider.apply_and_save()` 统一应用修改。

### 特殊处理

**章节检测**: 使用正则匹配 "第 X 章"、"Chapter X"、"1. "等格式，区分章节标题和目录条目。`extract_chapters_from_toc()` 先从目录提取章节结构，然后在正文中定位章节内容。

**目录过滤**: 自动跳过目录内容，通过 `is_table_of_contents()` 函数识别目录区域（关键字 + 省略号页码格式）。

**语法检查**:
- 通过 `create_provider()` 支持 TXT 和 DOCX 格式
- 找到最后一个"参考文献"段落，确定处理范围（处理到参考文献之前）
- 自动跳过目录、章节标题、空段落、短段落（<50字符）、LaTeX 公式等
- Ollama 返回格式：`###MODIFIED_TEXT###` 后接修改后的文本，`###MODIFIED_DESCRIPTION###` 后接修改说明
- DOCX 修改时自动将参考文献标记 [X] 设置为上标格式（`_replace_para_text_with_refs` 在 `document_provider.py` 中）
- 支持从已有 TXT 文件重新应用修改（`apply_txt_to_document`），避免重复调用 LLM
- DOCX 且已有 TXT 时提供复用选项

**后端适配**:
- 统一使用 OpenAI 兼容协议 `/v1/chat/completions`
- 本地服务（Ollama / llama.cpp）：通常不需要 API Key
- 云服务（OpenAI / DeepSeek 等）：通过 `API_KEY` 和 `MODEL_NAME` 环境变量配置

### 环境依赖

确保 LLM 服务已启动（`BASE_URL` 配置的地址）。

依赖安装：
```bash
pip install -r requirements.txt
```

主要依赖：
- `requests`: HTTP 请求（LLM API 调用）
- `python-docx>=1.1.0`: DOCX 文件处理（可选，仅 DOCX 功能需要）

### 代码约定

- 类型提示用于所有公共函数签名
- 中文注释用于中文代码逻辑
- 所有配置集中在 `config.py`（PROCESSOR_CONFIGS 字典）
- 文档格式通过 DocumentProvider 抽象层统一管理，新增格式只需添加子类
- 输出文件已加入 `.gitignore`
- src 目录通过 sys.path 自动添加到 Python 路径
