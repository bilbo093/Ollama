# OllamaDoc-Processor Web UI

学术文档智能处理工具的现代化 Web 界面 - **纯 Python 实现，无需 Node.js**

## 🚀 快速启动

### 一键启动（推荐）

**Windows:**
```bash
start-web.bat
```

**手动启动:**
```bash
cd web
python app.py
```

访问 **http://localhost:5000** 即可使用！

## ✨ 特点

- ✅ **纯 Python 实现**：仅需 Python 环境，无需安装 Node.js
- ✅ **Flask + SocketIO**：轻量级 Web 框架，实时日志推送
- ✅ **现代化 UI**：渐变主题、响应式设计、中文本地化
- ✅ **功能完整**：文件上传、三种处理模式、实时进度、任务管理

## 📋 功能特性

### 核心功能
- **文件上传**: 拖拽上传，支持 `.txt` 和 `.docx` 格式
- **三种处理模式**:
  - 全文模式：生成学术摘要
  - 章节模式：生成各章总结
  - 段落模式：语法检查润色
- **实时进度**: SocketIO 实时推送处理进度和日志
- **任务管理**: 查看、取消、下载历史任务
- **系统设置**: LLM 后端配置和连接测试

### 技术栈
- **后端**: Flask + Flask-SocketIO
- **前端**: 原生 HTML/CSS/JavaScript（无框架）
- **WebSocket**: Socket.IO 实时通信
- **复用代码**: 直接调用 `src/` 下的处理模块

## 📁 项目结构

```
web/
├── app.py                   # Flask 应用入口
├── templates/               # HTML 模板
│   ├── index.html          # 主页（上传+配置）
│   ├── task.html           # 任务进度
│   └── settings.html       # 系统设置
├── static/                 # 静态资源
│   ├── css/
│   │   └── style.css       # 样式表
│   └── js/
│       └── app.js          # JavaScript
├── uploads/                # 上传文件目录（自动创建）
├── results/                # 结果文件目录（自动创建）
└── README.md              # 本文件
```

## 🛠 依赖

### Python 依赖

```bash
pip install -r requirements.txt
```

或手动安装：

```bash
pip install flask flask-socketio simple-websocket
```

### 系统要求

- Python 3.8+
- 无需 Node.js！

## 🎯 使用流程

1. **启动服务**:
   ```bash
   cd web
   python app.py
   ```

2. **访问界面**: 打开浏览器访问 http://localhost:5000

3. **上传文件**: 拖拽或点击上传 `.txt` 或 `.docx` 文件

4. **选择模式**: 全文/章节/段落

5. **配置参数**: 语法检查版本、输出文件名

6. **开始处理**: 点击按钮，自动跳转到任务进度页

7. **查看进度**: 实时显示处理进度和日志

8. **下载结果**: 处理完成后一键下载

## 🔧 配置说明

### LLM 后端配置

在系统设置页面配置，或手动编辑 `src/config.py`:

```python
# 本地 Ollama
BASE_URL = 'http://127.0.0.1:11434/'
API_KEY = ''
MODEL_NAME = ''

# 或云端服务
BASE_URL = 'https://api.deepseek.com/'
API_KEY = 'sk-your-key'
MODEL_NAME = 'deepseek-chat'
```

### Web 服务配置

默认端口：`5000`

修改端口：编辑 `web/app.py` 最后一行：
```python
socketio.run(app, host='0.0.0.0', port=8080, debug=True)
```

## 📝 API 接口

### 文件上传
```
POST /api/upload
Content-Type: multipart/form-data
```

### 创建任务
```
POST /api/process
{
  "task_id": "string",
  "mode": "full|chapter|paragraph",
  "grammar_version": "v1|v2",
  "output_filename": "string (可选)"
}
```

### 查询任务
```
GET /api/tasks/{task_id}
```

### 下载结果
```
GET /api/download/{task_id}?type=output
```

### 测试连接
```
POST /api/config/test
{
  "base_url": "http://127.0.0.1:11434/",
  "api_key": "",
  "model_name": ""
}
```

## ⚠️ 注意事项

1. **确保 LLM 服务已启动**:
   ```bash
   ollama serve
   ollama pull qwen2.5
   ```

2. **文件大小**: 最大支持 50MB 文件

3. **长时间处理**: 长文档处理可能需要较长时间，请耐心等待

4. **浏览器兼容**: 推荐使用 Chrome/Edge 等现代浏览器

5. **Socket.IO CDN**: 任务页面使用 CDN 加载 Socket.IO 客户端，需要网络连接

## 🐛 故障排除

### 端口占用
```bash
# 检查端口占用
netstat -ano | findstr :5000

# 修改端口：编辑 web/app.py 最后一行
socketio.run(app, host='0.0.0.0', port=8080, debug=True)
```

### 依赖缺失
```bash
# 重新安装依赖
pip install -r requirements.txt
```

### Socket.IO 连接失败
- 检查防火墙设置
- 确认任务页面加载了 Socket.IO CDN（需要网络）
- 查看浏览器控制台错误信息

##  许可证

与主项目保持一致

## 🎉 开始使用

```bash
# Windows 用户
start-web.bat

# 或手动启动
cd web && python app.py

# 浏览器访问
# http://localhost:5000
```

祝您使用愉快！ 🚀
