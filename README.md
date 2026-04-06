# OllamaDoc-Processor

```
╔══════════════════════╗
║  📚  ➜  🤖          ║
║   OllamaDoc          ║
║   Processor          ║
║  智能学术文档处理      ║
╚══════════════════════╝
```

基于本地大模型的学术文档智能处理工具，支持 Ollama 和 llama.cpp 两种后端，为研究人员、学生提供高效的文档分析能力。支持 TXT/DOCX 文档的学术摘要生成、章节总结和语法检查功能。

## ✨ 功能特性

- **学术摘要生成**: 基于论文全文生成"总结与展望"章节，符合盲审规范
- **章节总结**: 按章节自动分割并生成各章节的简明总结
- **语法检查**: 逐段检查文档，自动应用修改，保留格式和参考文献标记
- **后端自动探测**: 只需配置服务地址，统一使用 OpenAI 兼容协议，兼容 Ollama / llama.cpp / OpenAI / DeepSeek 等所有服务
- **多格式支持**: 通过 DocumentProvider 抽象层统一管理 TXT / DOCX 格式
- **本地运行**: 基于本地大模型，保护数据隐私
- **流式输出**: 实时显示处理进度
- **智能分段**: 自动识别章节结构，跳过目录

## 📦 安装

### 前置要求

1. 安装 [Ollama](https://ollama.com/) 或 [llama.cpp server](https://github.com/ggerganov/llama.cpp)
2. 下载支持中文的模型（推荐 qwen3.5:4b）

### 安装项目依赖

```bash
pip install -r requirements.txt
```

## 🚀 快速开始

### 学术摘要生成

```bash
# 生成"总结与展望"章节
python main.py summarizer -i input.txt -o output.txt
python main.py summarizer -i input.docx -o output.txt
```

基于论文全文，生成结构严谨、逻辑清晰的"总结与展望"章节，包含研究总结和研究不足与未来展望两部分。

### 章节总结生成

```bash
# 按章节生成总结
python main.py chapter -i input.txt -o output.txt
python main.py chapter -i input.docx -o output.txt
```

自动识别章节结构，跳过目录，为每个章节生成 200-300 字的简洁总结。

### 语法检查并修改

```bash
# 自动推断语法检查文件
python main.py grammar -i input.docx
python main.py grammar -i input.txt

# 指定语法检查文件
python main.py grammar -i input.docx -o grammar.txt
```

自动处理：
- 逐段检查语法、标点、用词错误
- 跳过目录、章节标题、参考文献等特殊内容
- 处理到最后一个"参考文献"段落之前
- 自动应用修改，DOCX 文件保留参考文献标记为上标格式
- 生成修改后的文件（`{输入文件名}_fixed.txt` 或 `_fixed.docx`）
- 保存完整的修改建议到 TXT 文件

如果检测到已有的语法检查结果文件（仅 DOCX），会询问：
1. 使用现有的 TXT 文件生成文档（跳过 LLM 检查）
2. 重新进行语法检查（覆盖现有的 TXT 文件）
3. 取消操作

## 📝 命令行参数

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

### grammar 子命令

```
python main.py grammar -i <输入文件> [-o <输出文件>]
```

- `-i, --input`: 输入文件路径（.txt 或 .docx，必需）
- `-o, --output`: 语法检查结果文件路径（.txt，可选，默认 `input/{文件名}_grammar.txt`）

## ⚙️ 配置

### 环境变量

```bash
# LLM 服务地址（必需）
set BASE_URL=https://api.deepseek.com/

# API Key（本地服务通常不需要，云服务需要）
set API_KEY=sk-xxx

# 模型名称（本地服务通常不需要，云服务需要指定具体模型）
set MODEL_NAME=deepseek-chat
```

配置示例：
- **Ollama**: `BASE_URL=http://127.0.0.1:11434/`（无需 API_KEY）
- **llama.cpp**: `BASE_URL=http://127.0.0.1:8033/`（无需 API_KEY）
- **DeepSeek**: `BASE_URL=https://api.deepseek.com/` + `API_KEY=sk-xxx` + `MODEL_NAME=deepseek-chat`
- **OpenAI**: `BASE_URL=https://api.openai.com/v1/` + `API_KEY=sk-xxx` + `MODEL_NAME=gpt-4`

### 模型配置

在 `src/config.py` 中修改：

```python
STREAM_BUFFER_SIZE = 30        # 流式输出缓冲区大小（字符数）
```

## 📂 项目结构

```
OllamaDoc-Processor/
├── main.py                      # 主入口
├── src/
│   ├── config.py               # 配置管理（角色、提示词、常量）
│   ├── file_io.py              # 文件读写（TXT/DOCX）
│   ├── ollama_processor.py     # 统一 LLM 客户端（自动探测后端）
│   ├── document_provider.py    # 文档抽象层（DocumentProvider ABC + 工厂）
│   ├── content_splitter.py     # 内容分段（章节识别、目录过滤）
│   └── docx_editor.py          # 语法检查业务逻辑（格式无关）
├── input/                       # 输入目录（不提交）
├── output/                      # 输出目录（不提交）
├── requirements.txt             # 依赖列表
├── README.md                    # 项目说明
├── CODEBUDDY.md                 # 开发指南
└── PROJECT_DESIGN.md            # 项目设计文档
```

## 🔧 核心架构

### 后端自动探测

统一使用 OpenAI 兼容协议 `/v1/chat/completions`，兼容所有主流 LLM 服务：
- **本地服务**: Ollama、llama.cpp（通常无需 API Key）
- **云服务**: OpenAI、DeepSeek、通义千问等（需配置 API_KEY 和 MODEL_NAME）

### DocumentProvider 抽象层

通过抽象基类 + 工厂模式统一文档格式处理：

```python
class DocumentProvider(ABC):
    def read_paragraphs(self) -> list[str]: ...
    def apply_and_save(self, modifications, output_path) -> int: ...
    def infer_output_path(self) -> str: ...

# 工厂函数
provider = create_provider("input.docx")  # → DocxDocumentProvider
provider = create_provider("input.txt")   # → TxtDocumentProvider
```

新增格式只需实现 `DocumentProvider` 子类并注册到 `create_provider()`。

### 配置驱动模式

所有处理器通过 `PROCESSOR_CONFIGS` 统一配置：

```python
PROCESSOR_CONFIGS = {
    'summarizer': { 'role': ..., 'prompt_template': ... },
    'chapter':    { 'role': ..., 'prompt_template': ... },
    'grammar':    { 'role': ..., 'prompt_template': ... },
}
```

### 逐段语法检查

- 通过 `DocumentProvider` 接口操作文档，业务逻辑与格式解耦
- 自动跳过目录、章节标题、参考文献、短段落、LaTeX 公式等
- DOCX 修改时自动将参考文献标记 [X] 设为上标格式
- 支持从 TXT 缓存文件重新应用修改

## ⚠️ 注意事项

1. **确保 LLM 服务已启动**（`BASE_URL` 配置的地址）
2. **统一协议**: 使用 OpenAI 兼容协议，兼容 Ollama / llama.cpp / DeepSeek / OpenAI 等所有服务
3. **中文支持**: 确保模型支持中文
4. **章节识别**: 章节总结功能会自动识别"第X章"、"Chapter X"、"1."等格式的章节标题
5. **复读保护**: 内置复读检测机制，相似度 >=0.6 连续 5 次会自动中断

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🔗 相关链接

- [项目设计](./PROJECT_DESIGN.md)
- [开发指南](./CODEBUDDY.md)
