# 安装配置

## 前置要求

- Python 3.8+
- LLM 服务（Ollama / llama.cpp / 云端 API）

## 安装步骤

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动 LLM 服务
# Ollama:
ollama serve
ollama pull qwen2.5

# 或使用云端服务（无需本地启动）
```

## 配置

编辑 `src/config.py`:

```python
# 本地 Ollama
BASE_URL = 'http://127.0.0.1:11434/'
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

## 验证

```bash
python main.py full -i input/test.txt -o output/test.txt
```

## 环境变量（可选）

```bash
export BASE_URL='http://127.0.0.1:11434/'
export API_KEY=''
export MODEL_NAME=''
```
