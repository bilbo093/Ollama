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

### 处理模式

- **全文模式**: 整个文档一次性送入 LLM，适用于生成论文"总结与展望"章节
- **章节模式**: 按章节拆分后逐章送入 LLM，适用于生成各章总结
- **段落模式**: 按段落拆分后逐段送入 LLM，适用于语法检查和润色

### Web UI 特性 🎨

- 📤 **拖拽上传**: 支持 `.txt` 和 `.docx` 格式，最大 50MB
- ⚙️ **可视化配置**: 处理模式选择、语法检查版本配置
- 📊 **实时进度**: WebSocket 推送处理进度和日志
- 📝 **任务管理**: 查看历史任务、下载结果文件
- 🔧 **系统设置**: LLM 后端配置和连接测试
- 🌙 **现代界面**: 响应式设计、中文本地化

## 预设提示词

项目内置三种处理模式的提示词和角色配置，位于 `src/prompts/` 目录：

- `academic_summarizer.py` - 学术摘要生成（盲审专家角色）
- `chapter_summarizer.py` - 章节总结生成（学术助手角色）
- `grammar_checker.py` - 语法检查（学术编辑角色，支持最小干预和学术升格两种模式）

## 支持的后端

- **本地服务**: Ollama、llama.cpp
- **云端服务**: DeepSeek、通义千问、OpenAI（需 API Key）

## 支持的格式

- **输入**: .txt、.docx
- **输出**: .txt、.docx（段落模式自动生成润色后文档）

## 快速启动

### 方式一：Web UI（推荐 ✨）

**纯 Python 实现，无需 Node.js！**

```bash
# Windows 一键启动
start-web.bat

# 或手动启动（使用 conda 环境）
cd web
C:\Users\orchi\.conda\envs\py390\python.exe app.py
```

访问 http://localhost:5000 即可使用现代化 Web 界面！

### 方式二：命令行工具

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动 LLM 服务
ollama serve
ollama pull qwen2.5

# 3. 配置服务（src/config.py）
BASE_URL = 'http://127.0.0.1:11434/'

# 4. 运行
python main.py full -i input.txt -o output.txt
```

## 常用命令

```bash
# 学术摘要生成
python main.py full -i input.txt -o output.txt

# 章节总结生成
python main.py chapter -i input.txt -o output.txt

# 段落语法检查
python main.py paragraph -i input.docx
```

## 详细文档

- [安装配置](./docs/INSTALLATION.md) - 详细安装步骤和配置说明
- [使用指南](./docs/USAGE.md) - 三种处理模式的使用说明
- [Web UI 说明](./web/README.md) - Web 界面使用指南

## 📄 许可证

MIT License
