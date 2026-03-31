# OllamaDoc-Processor

[![GitHub Stars](https://img.shields.io/github/stars/YOUR_USERNAME/YOUR_REPO_NAME?style=social)](https://github.com/YOUR_USERNAME/YOUR_REPO_NAME/stargazers)

```
╔══════════════════════╗
║  📚  ➜  🤖          ║
║   OllamaDoc          ║
║   Processor          ║
║  智能学术文档处理      ║
╚══════════════════════╝
```

基于 Ollama 本地大模型的学术文档智能处理工具，为研究人员、学生提供高效的文档分析能力。支持 TXT/DOCX 文档的学术摘要生成、章节总结和三阶段分段评价功能。

## 安装

```bash
pip install -r requirements.txt
```

## 使用方法

### 运行主入口（推荐）

```bash
# 学术摘要生成
python main.py summarizer -i input.txt -o output.txt

# 章节总结生成
python main.py chapter -i input.txt -o output.txt

# 三阶段分段评价
python main.py evaluate -i input.txt -o output.txt
python main.py evaluate -i input.txt -o output.txt --chunk-size 30000 --overlap 3000
```

## 命令行参数

### 通用参数
无

### 子命令参数

- `summarizer`: 学术摘要生成
  - `-i, --input`: 输入文件路径 (.txt 或 .docx)
  - `-o, --output`: 输出文件路径 (.txt)
- `chapter`: 章节总结生成
  - `-i, --input`: 输入文件路径 (.txt 或 .docx)
  - `-o, --output`: 输出文件路径 (.txt)
- `evaluate`: 三阶段分段评价
  - `-i, --input`: 输入文件路径 (.txt 或 .docx)
  - `-o, --output`: 输出文件路径 (.txt)
  - `--chunk-size`: 每块字符数（默认：30000）
  - `--overlap`: 重叠字符数（默认：3000）

## 注意事项

1. **确保 Ollama 已启动**（默认地址：http://localhost:11434）
2. **中文支持**：确保 Ollama 模型支持中文（qwen3.5:9b 支持）
3. **章节识别**：章节总结功能会自动识别"第X章"、"Chapter X"、"1."等格式的章节标题

## 环境变量

```bash
# Windows
set OLLAMA_MODEL='qwen3.5:9b'

# Linux/Mac
export OLLAMA_MODEL='qwen3.5:9b'
```

## 许可证

MIT License

## 项目信息

- **项目名称**: OllamaDoc-Processor
- **当前版本**: v1.0.0
- **开发状态**: 活跃维护
- **设计文档**: [PROJECT_DESIGN.md](./PROJECT_DESIGN.md)

## 相关链接

- [GitHub Issues](https://github.com/YOUR_USERNAME/YOUR_REPO_NAME/issues)
- [开发指南](./CODEBUDDY.md)
- [项目设计](./PROJECT_DESIGN.md)

---

**Made with ❤️ using Ollama**
