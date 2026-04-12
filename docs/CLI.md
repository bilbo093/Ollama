# CLI 命令行模式使用指南

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置 LLM 后端

编辑 `src/config.py` 文件：

```python
# llama.cpp 本地服务
BASE_URL = 'http://127.0.0.1:8080/'
API_KEY = ''
MODEL_NAME = ''

# DeepSeek 云端
BASE_URL = 'https://api.deepseek.com/'
API_KEY = 'sk-your-key'
MODEL_NAME = 'deepseek-chat'

# 通义千问云端
BASE_URL = 'https://dashscope.aliyuncs.com/compatible-mode/v1/'
API_KEY = 'sk-your-key'
MODEL_NAME = 'qwen-plus'
```

也可以通过环境变量配置（优先级更高）：

```bash
export BASE_URL='http://127.0.0.1:8080/'
export API_KEY=''
export MODEL_NAME=''
```

### 启动 LLM 服务

**使用本地 llama.cpp：**
```bash
# 启动 llama.cpp 服务器
./llama-server -m your-model.gguf
```

**使用云端服务：** 无需本地启动，配置好 API Key 即可。

## 命令格式

```bash
python main.py <模式> -i <输入文件> -o <输出文件>
```

## 三种处理模式

| 模式 | 功能 | 输入 | 输出 |
|------|------|------|------|
| `full` | 生成总结与展望 | .txt/.docx | .txt |
| `chapter` | 生成各章总结 | .txt/.docx | .txt |
| `paragraph` | 语法检查润色 | .txt/.docx | .txt + .docx |

### 全文模式

将整个文档一次性送入 LLM，适用于生成论文"总结与展望"章节。

```bash
python main.py full -i input.txt -o output.txt
python main.py full -i input.docx -o output.txt
```

### 章节模式

按章节拆分后逐章送入 LLM，适用于生成各章总结。

```bash
python main.py chapter -i input.txt -o output.txt
python main.py chapter -i input.docx -o output.txt
```

### 段落模式

按段落拆分后逐段送入 LLM，适用于语法检查和润色。

```bash
# 自动推断输出文件
python main.py paragraph -i input.docx

# 指定检查结果文件
python main.py paragraph -i input.docx -o check.txt
```

**输出文件：**
- `<文件名>_grammar.txt` - 检查结果
- `<文件名>_fixed.docx` - 润色后文档（与输入文件同目录）

## ⚙️ 提示词配置

CLI 模式**仅支持加载默认的提示词**，即 `src/prompts/` 目录下各模式的 `default.md` 文件。

如需修改提示词：

1. 打开对应的默认提示词文件：
   - 全文模式：`src/prompts/full/default.md`
   - 章节模式：`src/prompts/chapter/default.md`
   - 段落模式：`src/prompts/paragraph/default.md`

2. 编辑 `## Role` 和 `## Prompt` 章节内容

3. 保存后直接运行 CLI 命令即可生效

> 💡 **提示**：如果您需要更灵活的版本管理和在线切换功能，建议使用 **Web UI** 方式。

## 验证安装

```bash
python main.py full -i input/test.txt -o output/test.txt
```

## 帮助信息

```bash
python main.py --help
python main.py full --help
```
