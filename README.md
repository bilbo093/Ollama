# 学术文档处理工具

基于 Ollama 的学术文档处理工具集，提供 TXT 文档的学术摘要生成和章节总结生成功能。

## 安装

```bash
pip install -r requirements.txt
```

## 使用方法

### 运行主入口（推荐）

```bash
# 学术摘要生成
python main.py summarizer -i input.txt -o output.txt

# 学术摘要生成（两阶段压缩模式）
python main.py summarizer -i input.txt -o output.txt --compact

# 章节总结生成
python main.py chapter -i input.txt -o output.txt
```

## 命令行参数

### 通用参数
- `--model, -m`: Ollama 模型名称 (默认：qwen3.5:9b)
- `--timeout`: 请求超时时间 (秒，默认：120)

### 子命令参数

- `summarizer`: 学术摘要生成
  - `-i, --input`: 输入文件路径 (.txt)
  - `-o, --output`: 输出文件路径 (.txt)
  - `--compact`: 启用两阶段压缩处理（先压缩内容，再分析）
- `chapter`: 章节总结生成
  - `-i, --input`: 输入文件路径 (.txt)
  - `-o, --output`: 输出文件路径 (.txt)

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
