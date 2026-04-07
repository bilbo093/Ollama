# OllamaDoc-Processor

```
╔══════════════════════════╗
║  📚 智能学术文档处理器     ║
║  Vibe Coding 实践项目     ║
╚══════════════════════════╝
```

> 一个通过 AI 辅助开发的学术文档智能处理工具。这个项目展示了 **Vibe Coding** 的实践：从需求表达到功能实现，从架构设计到 UI 开发，全程通过与 AI 协作完成。

## 🎯 项目简介

学术文档处理的痛点：
- 长文档难以快速生成总结和展望
- 语法检查和润色耗时耗力
- 不同章节需要统一风格的总结

这个工具通过本地或云端大语言模型，提供三种处理粒度：**全文摘要**、**章节总结**、**段落润色**，满足学术研究中的不同场景需求。

## ✨ 核心能力

- 🎯 **三种处理模式**：全文 / 章节 / 段落，灵活适配不同需求
- 🌐 **现代化 Web UI**：拖拽上传、实时进度、任务管理
- 🤖 **多后端支持**：Ollama、llama.cpp、DeepSeek、通义千问、OpenAI 等
- 📝 **提示词系统**：支持版本管理和自定义编辑
- 🔒 **隐私安全**：本地部署，数据无需外传

## 🚀 快速开始

### Web UI 方式（推荐）

```bash
# 启动 Web 服务
cd web
python app.py
```

访问 **http://localhost:5000** 即可使用！

### 命令行方式

```bash
# 安装依赖
pip install -r requirements.txt

# 配置后端（编辑 src/config.py）
# 运行处理命令
python main.py full -i input.txt -o output.txt          # 全文模式
python main.py chapter -i input.txt -o output.txt        # 章节模式
python main.py paragraph -i input.docx                   # 段落模式
```

## 🤖 Vibe Coding 实践

这个项目是一个 **Vibe Coding** 的典型案例：

### 什么是 Vibe Coding？

通过与 AI 对话，将想法快速转化为实际可用的代码。不需要逐行编写，而是描述需求、确认架构、验收功能，让 AI 完成大部分编码工作。

### 这个项目如何体现？

- **需求阶段**：描述学术文档处理的痛点和期望功能
- **架构设计**：讨论 CLI 和 Web UI 的技术选型，确定模块化设计
- **功能实现**：逐步实现三种处理模式、文件解析、LLM 集成
- **UI 开发**：描述界面需求和交互流程，生成完整的 Web 前端
- **迭代优化**：根据使用体验反馈，持续改进提示词和用户体验

### 关键特点

- ✅ **纯 Python 技术栈**：Web UI 无需 Node.js，降低使用门槛
- ✅ **配置驱动设计**：提示词、后端地址等通过配置文件管理
- ✅ **模块化架构**：CLI 和 Web UI 共享核心处理逻辑
- ✅ **渐进式开发**：从简单脚本到完整应用的自然演进

## 📊 处理模式

| 模式 | 适用场景 | 输出 |
|------|----------|------|
| **全文模式** | 生成论文总结与展望 | `.txt` |
| **章节模式** | 逐章生成总结 | `.txt` |
| **段落模式** | 语法检查与润色 | `.txt` + `.docx` |

## 🔧 配置说明

编辑 `src/config.py` 或通过 Web UI 系统设置页面配置：

```python
# 本地 Ollama
BASE_URL = 'http://127.0.0.1:11434/'

# 或云端服务
BASE_URL = 'https://api.deepseek.com/'
API_KEY = 'sk-your-key'
MODEL_NAME = 'deepseek-chat'
```

## 📖 详细文档

- [💻 CLI 命令行模式](./docs/CLI.md) - 命令行安装、配置和使用
- [🌐 Web UI 模式](./docs/WEBUI.md) - Web 界面使用和功能介绍

## 💡 技术栈

- **后端核心**：Python + requests + python-docx
- **Web UI**：Flask + Flask-SocketIO
- **前端**：原生 HTML/CSS/JavaScript
- **LLM 后端**：Ollama / llama.cpp / DeepSeek / 通义千问 / OpenAI

## 📄 许可证

MIT License

---

**Vibe Coding 的核心理念**：与其纠结每一行代码，不如专注想清楚要什么。让 AI 处理实现细节，你只需要描述需求、验收结果。这个项目就是这个理念的最佳实践。 🚀
