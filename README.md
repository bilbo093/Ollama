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

基于 Ollama 本地大模型的学术文档智能处理工具，为研究人员、学生提供高效的文档分析能力。支持 TXT/DOCX 文档的学术摘要生成、章节总结、三阶段分段评价和语法检查功能。

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

# 语法检查并修改（自动推断文件）
python main.py grammar -i input.docx

# 语法检查并修改（指定语法检查文件）
python main.py grammar -i input.docx -o grammar.txt

# 语法检查并修改（指定输出 DOCX 文件）
python main.py grammar -i input.docx -o output.docx

# 仅高亮显示修改建议（不实际修改）
python main.py grammar -i input.docx --highlight-only

# 应用所有修改（包括润色建议）
python main.py grammar -i input.docx --apply-suggestions
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
- `grammar`: 语法检查并修改 DOCX 文件
  - `-i, --input`: 输入 DOCX 文件路径（必需）
  - `-o, --output`: 语法检查结果文件路径（.txt）或输出 DOCX 文件路径（.docx，可选）
    - 指定 .txt 文件：使用指定的语法检查结果文件
    - 指定 .docx 文件：输出修改后的 DOCX 文件
    - 未指定：自动使用 input/{文件名}_grammar.txt 作为语法检查文件，输出 {输入文件名}_fixed.docx
  - `--apply-suggestions`: 是否应用润色建议（默认只应用硬性错误）
  - `--highlight-only`: 仅高亮显示修改建议，不实际修改文档（输出文件名：{输入文件名}_highlighted.docx）

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
