# OllamaDoc-Processor

```
╔══════════════════════╗
║  📚  ➜  🤖          ║
║   OllamaDoc          ║
║   Processor          ║
║  智能学术文档处理      ║
╚══════════════════════╝
```

基于 Ollama 本地大模型的学术文档智能处理工具，为研究人员、学生提供高效的文档分析能力。支持 TXT/DOCX 文档的学术摘要生成、章节总结、三阶段分段评价和语法检查功能。

## ✨ 功能特性

- **学术摘要生成**: 快速提取文档核心内容，生成符合学术规范的摘要和评分
- **章节总结**: 按章节自动分割并生成各章节的简明总结
- **三阶段评价**: 分段处理 → 分段汇总 → 最终评价报告，全面评估文档质量
- **语法检查**: 逐段检查 DOCX 文件，自动应用修改，保留格式和参考文献标记
- **本地运行**: 基于 Ollama 本地大模型，保护数据隐私
- **流式输出**: 实时显示处理进度
- **智能分段**: 自动识别章节结构，跳过目录

## 📦 安装

### 前置要求

1. 安装 [Ollama](https://ollama.com/)
2. 下载支持中文的模型（推荐 qwen3.5:4b）

```bash
# 下载模型
ollama pull qwen3.5:4b

# 启动 Ollama 服务
ollama serve
```

### 安装项目依赖

```bash
pip install -r requirements.txt
```

## 🚀 快速开始

### 学术摘要生成

```bash
# 生成学术风格摘要和评分
python main.py summarizer -i input.txt -o output.txt
python main.py summarizer -i input.docx -o output.txt
```

输出包含：
- 论文质量评估
- 各维度详细评价（选题、基础知识、创新性、规范性）
- 综合评分（0-100分）
- 等级判断（A/B/C）
- 修改建议

### 章节总结生成

```bash
# 按章节生成总结
python main.py chapter -i input.txt -o output.txt
python main.py chapter -i input.docx -o output.txt
```

自动识别章节结构，跳过目录，为每个章节生成 200-300 字的简洁总结。

### 三阶段分段评价

```bash
# 完整的三阶段评价流程
python main.py evaluate -i input.txt -o output.txt

# 自定义分段大小
python main.py evaluate -i input.txt -o output.txt --chunk-size 30000 --overlap 3000
```

三个阶段：
1. **分段处理**: 按章节分段评价，超长章节自动分割
2. **分段汇总**: 去重并按维度整理（选题、基础、创新、规范）
3. **最终报告**: 生成评分、等级和修改建议

### 语法检查并修改

```bash
# 自动推断语法检查文件
python main.py grammar -i input.docx

# 指定语法检查文件
python main.py grammar -i input.docx -o grammar.txt
```

自动处理：
- 逐段检查语法、标点、用词错误
- 跳过目录、章节标题、参考文献等特殊内容
- 自动应用修改，保留参考文献标记为上标格式
- 生成修改后的 DOCX 文件（`{输入文件名}_fixed.docx`）
- 保存完整的修改建议到 TXT 文件

如果检测到已有的语法检查结果文件，会询问：
1. 使用现有的 TXT 文件生成 DOCX（跳过 Ollama 检查）
2. 重新进行语法检查（覆盖现有的 TXT 文件）
3. 取消操作

## 📝 命令行参数

### 通用参数

无全局参数，使用子命令模式。

### summarizer 子命令

```
python main.py summarizer -i <输入文件> -o <输出文件>
```

- `-i, --input`: 输入文件路径（.txt 或 .docx）
- `-o, --output`: 输出文件路径（.txt）

### chapter 子命令

```
python main.py chapter -i <输入文件> -o <输出文件>
```

- `-i, --input`: 输入文件路径（.txt 或 .docx）
- `-o, --output`: 输出文件路径（.txt）

### evaluate 子命令

```
python main.py evaluate -i <输入文件> -o <输出文件> [选项]
```

- `-i, --input`: 输入文件路径（.txt 或 .docx）
- `-o, --output`: 输出文件路径（.txt）
- `--chunk-size`: 每块字符数（默认：30000）
- `--overlap`: 重叠字符数（默认：3000）

### grammar 子命令

```
python main.py grammar -i <输入文件> [-o <输出文件>]
```

- `-i, --input`: 输入 DOCX 文件路径（必需）
- `-o, --output`: 
  - 指定 .txt 文件：使用指定的语法检查结果文件
  - 未指定：自动使用 `input/{文件名}_grammar.txt`，输出 `{输入文件名}_fixed.docx`

## ⚙️ 配置

### 环境变量

```bash
# Windows
set OLLAMA_MODEL='qwen3.5:4b'

# Linux/Mac
export OLLAMA_MODEL='qwen3.5:4b'
```

### 模型配置

在 `src/config.py` 中修改：

```python
DEFAULT_MODEL = 'qwen3.5:4b'  # 使用的 Ollama 模型
STREAM_BUFFER_SIZE = 30        # 流式输出缓冲区大小
```

## 📂 项目结构

```
OllamaDoc-Processor/
├── main.py                      # 主入口
├── src/
│   ├── config.py               # 配置管理（角色、提示词、常量）
│   ├── file_io.py              # 文件读写（TXT/DOCX）
│   ├── ollama_processor.py     # Ollama 客户端和统一处理器
│   ├── content_splitter.py     # 内容分段（章节/字符数）
│   ├── segmented_evaluator.py  # 三阶段评价处理器
│   └── docx_editor.py          # DOCX 文件编辑器（语法检查）
├── input/                       # 输入目录（不提交）
├── output/                      # 输出目录（不提交）
├── requirements.txt             # 依赖列表
├── README.md                    # 项目说明
├── CODEBUDDY.md                 # 开发指南
└── PROJECT_DESIGN.md            # 项目设计文档
```

## 🔧 核心架构

### 配置驱动模式

所有处理器统一使用 `TextProcessor` 类，通过配置驱动实现不同功能：

```python
PROCESSOR_CONFIGS = {
    'summarizer': {
        'role': ACADEMIC_SUMMARIZER_ROLE,
        'prompt_template': ACADEMIC_SUMMARIZER_PROMPT,
    },
    'chapter': {
        'role': CHAPTER_SUMMARIZER_ROLE,
        'prompt_template': CHAPTER_SUMMARIZER_PROMPT,
    },
    'grammar': {
        'role': GRAMMAR_CHECKER_ROLE,
        'prompt_template': GRAMMAR_CHECKER_PROMPT,
    },
}
```

### 三阶段评价流程

1. **分段处理**: 按章节分割，超长章节使用带重叠的分段
2. **分段汇总**: 去重并按维度整理（选题、基础知识、创新性、规范性）
3. **最终报告**: 生成评分（0-100分）、等级（A/B/C）和修改建议

### 逐段语法检查

- 直接按段落序号处理，完全避免内容匹配问题
- 自动跳过目录、章节标题、参考文献等特殊内容
- 自动处理参考文献标记为上标格式
- 支持从已有 TXT 文件重新应用修改

## 📖 使用示例

### 示例 1：评估论文质量

```bash
# 生成完整的论文评价报告
python main.py evaluate -i 本科生毕业论文示例.docx -o 评价报告.txt
```

输出包含：
- 分段评价结果
- 分段汇总（按维度整理）
- 最终评价报告（评分、等级、建议）

### 示例 2：快速概览章节

```bash
# 生成章节总结，快速了解论文结构
python main.py chapter -i 本科生毕业论文示例.docx -o 章节总结.txt
```

### 示例 3：语法检查并修改

```bash
# 检查并修改 DOCX 文件
python main.py grammar -i 本科生毕业论文示例.docx

# 输出文件：
# - input/本科生毕业论文示例_grammar.txt（修改建议）
# - 本科生毕业论文示例_fixed.docx（修改后的文档）
```

## ⚠️ 注意事项

1. **确保 Ollama 已启动**（默认地址：http://localhost:11434）
2. **中文支持**：确保 Ollama 模型支持中文（qwen3.5:4b 支持）
3. **章节识别**：章节总结功能会自动识别"第X章"、"Chapter X"、"1."等格式的章节标题
4. **复读保护**：内置复读检测机制，相似度 ≥0.6 连续 5 次会自动中断
5. **长度保护**：输出长度超过输入长度 × 20 会自动中断

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🔗 相关链接

- [项目设计](./PROJECT_DESIGN.md)
- [开发指南](./CODEBUDDY.md)
- [Ollama 官网](https://ollama.com/)

---

**Made with ❤️ using Ollama**
