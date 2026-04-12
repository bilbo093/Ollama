# QWEN.md - LLM-Doc-Processor 项目上下文

## 项目概述

**LLM-Doc-Processor** 是一个通过 AI 辅助开发的学术文档智能处理工具，采用 **Vibe Coding** 实践理念构建。项目通过本地或云端大语言模型（LLM），为学术文档提供三种处理粒度：**全文摘要**、**章节总结**、**段落润色**，满足学术研究中的不同场景需求。

### 核心能力

- 🎯 **三种处理模式**：全文 / 章节 / 段落，灵活适配不同需求
- 🌐 **现代化 Web UI**：拖拽上传、实时进度、任务管理
- 🤖 **多后端支持**：llama.cpp、DeepSeek、通义千问、OpenAI 等所有 OpenAI 兼容 API
- 📝 **提示词系统**：支持版本管理和自定义编辑
- 🔒 **隐私安全**：本地部署，数据无需外传

### 处理模式

| 模式 | 适用场景 | 输出 |
|------|----------|------|
| **全文模式** | 生成论文总结与展望 | `.txt` |
| **章节模式** | 逐章生成总结 | `.txt` |
| **段落模式** | 语法检查与润色 | `.txt` + `.docx` |

---

## 技术栈

- **后端核心**：Python + requests + python-docx
- **Web UI**：Flask + Flask-SocketIO（纯 Python，无需 Node.js）
- **前端**：原生 HTML/CSS/JavaScript
- **LLM 后端**：llama.cpp、DeepSeek、通义千问、OpenAI 等所有 OpenAI 兼容 API

---

## 项目结构

```
LLM-Doc-Processor/
├── main.py                 # CLI 命令行主入口
├── requirements.txt        # Python 依赖列表
├── README.md               # 项目说明文档
├── QWEN.md                 # 项目上下文（本文件）
│
├── src/                    # 核心处理模块
│   ├── config.py           # 项目配置（后端地址、API Key、模型名称）
│   ├── llm_client.py       # 统一 LLM 客户端（OpenAI 兼容协议）
│   ├── file_io.py          # 文件读写工具
│   ├── content_splitter.py # 文档章节拆分逻辑
│   ├── document_provider.py# 文档提供者抽象（支持 .txt/.docx）
│   ├── docx_editor.py      # DOCX 文档编辑器
│   └── prompts/            # 提示词系统
│       ├── __init__.py
│       ├── loader.py       # 提示词加载器
│       ├── full/           # 全文模式提示词
│       ├── chapter/        # 章节模式提示词
│       └── paragraph/      # 段落模式提示词
│
├── web/                    # Web UI 模块
│   ├── app.py              # Flask Web 应用主入口
│   ├── templates/          # HTML 模板
│   ├── static/             # 静态资源（CSS/JS）
│   ├── uploads/            # 上传文件存储
│   └── results/            # 处理结果存储
│
├── docs/                   # 详细文档
│   ├── CLI.md              # CLI 命令行使用指南
│   └── WEBUI.md            # Web UI 使用指南
│
├── input/                  # 示例输入目录
└── output/                 # 示例输出目录
```

---

## 构建与运行

### 安装依赖

```bash
pip install -r requirements.txt
```

### Web UI 方式（推荐）

```bash
cd web
python app.py
```

访问 **http://localhost:5000** 即可使用。

### CLI 命令行方式

```bash
# 全文模式
python main.py full -i input.txt -o output.txt

# 章节模式
python main.py chapter -i input.txt -o output.txt

# 段落模式
python main.py paragraph -i input.docx
python main.py paragraph -i input.docx -o grammar.txt  # 指定检查结果文件
```

---

## 配置说明

### LLM 后端配置

编辑 `src/config.py` 文件：

```python
# llama.cpp 本地服务
BASE_URL = 'http://127.0.0.1:8080/'
API_KEY = ''
MODEL_NAME = ''

# 或云端服务
BASE_URL = 'https://api.deepseek.com/'
API_KEY = 'sk-your-key'
MODEL_NAME = 'deepseek-chat'
```

也可以通过环境变量配置（优先级更高）：

```bash
export BASE_URL='http://127.0.0.1:8080/'
export API_KEY=''
export MODEL_NAME=''
```

### 提示词配置

- **CLI 模式**：仅支持加载 `src/prompts/` 目录下各模式的 `default.md` 文件
- **Web UI 模式**：支持完整的提示词版本管理（查看、切换、创建、编辑、删除版本）

---

## 开发约定

### 代码风格

- 纯 Python 技术栈，降低使用门槛
- 配置驱动设计：提示词、后端地址等通过配置文件管理
- 模块化架构：CLI 和 Web UI 共享核心处理逻辑

### 架构设计

- **LLM 客户端**：统一的 `LLMClient` 类，使用 OpenAI 兼容协议，支持流式输出和复读检测
- **文档处理**：通过 `DocumentProvider` 抽象不同文档类型（.txt/.docx）
- **Web 实时推送**：使用 Flask-SocketIO 实现 WebSocket 进度推送

### 关键特性

- 流式输出：`STREAM_BUFFER_SIZE = 30` 字符缓冲区，实现流畅的实时显示
- 复读检测：检测模型复读，相似度 >= 0.6 且连续 5 次则自动中断
- 文件去重：Web UI 使用 MD5 指纹去重上传文件
- 任务持久化：任务记录存储在 `web/tasks.json`，最多保留 20 条

---

## 常用命令参考

| 操作 | 命令 |
|------|------|
| 安装依赖 | `pip install -r requirements.txt` |
| 启动 Web UI | `cd web && python app.py` |
| CLI 全文模式 | `python main.py full -i input.txt -o output.txt` |
| CLI 章节模式 | `python main.py chapter -i input.txt -o output.txt` |
| CLI 段落模式 | `python main.py paragraph -i input.docx` |
| 查看帮助 | `python main.py --help` |

---

## 注意事项

1. **确保 LLM 服务已启动**（本地 llama.cpp 或云端 API 可用）
2. **文件大小**：Web UI 最大支持 500MB
3. **浏览器兼容**：推荐使用 Chrome/Edge 等现代浏览器
4. **端口占用**：Web UI 默认使用 5000 端口，可在 `web/app.py` 修改
5. **默认的 `default` 提示词版本**不可修改或删除

---

## 许可证

MIT License
