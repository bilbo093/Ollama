"""
LLM-Doc-Processor Web UI - Flask 版本
纯 Python 实现，无需 Node.js
"""
import os
import sys
import uuid
import threading
import time
import hashlib
from pathlib import Path
from datetime import datetime

from flask import (
    Flask, render_template, request, jsonify, 
    send_file, send_from_directory, redirect, url_for
)
from flask_socketio import SocketIO, emit, join_room

# 添加 src 目录到路径
src_dir = Path(__file__).parent.parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# 导入现有模块
from llm_client import LLMClient
from file_io import read_file_content, save_to_txt
from config import PROCESSOR_CONFIGS
from docx_editor import process_document, apply_txt_to_document, is_ref_section, _skip_para, _save_mods_to_txt, _parse_modified_text
from document_provider import create_provider
from content_splitter import split_content_by_chapters


class WebLLMClient(LLMClient):
    """Web 环境下的 LLM 客户端，支持实时进度推送"""
    
    def __init__(self, task_id=None):
        super().__init__()
        self.task_id = task_id
        self._last_emit_count = 0
    
    def _emit_progress(self):
        """推送进度到前端"""
        if self.task_id and self._char_count - self._last_emit_count >= 100:
            # 每 100 字符推送一次进度
            socketio.emit('llm_progress', {
                'task_id': self.task_id,
                'char_count': self._char_count,
                'preview': self._full_content[-100:].replace('\n', ' ')
            }, room=self.task_id)
            self._last_emit_count = self._char_count


def llm_chat(messages, task_id=None):
    """
    LLM 调用函数，支持 Web 环境下的实时进度推送
    
    Args:
        messages: 消息列表
        task_id: 任务 ID（可选），如果提供则推送进度
    """
    if task_id:
        # Web 环境，使用带进度推送的客户端
        client = WebLLMClient(task_id=task_id)
        # 重写 _check_repeat 方法以推送进度
        original_check = client._check_repeat
        def check_with_progress():
            result = original_check()
            client._emit_progress()
            return result
        client._check_repeat = check_with_progress
        return client.chat(messages)
    else:
        # 普通环境
        return LLMClient().chat(messages)

# 创建 Flask 应用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'llm-doc-processor-secret-key'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB

# SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# 目录配置
UPLOAD_DIR = Path(__file__).parent / "uploads"
RESULTS_DIR = Path(__file__).parent / "results"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# 任务存储
tasks = {}
task_logs = {}
task_choices = {}  # 存储用户的 TXT 选择


import json
task_events = {}  # 存储任务等待事件

# 任务持久化配置
TASKS_FILE = Path(__file__).parent / "tasks.json"
MAX_TASKS = 20  # 最多保留20条记录

# 文件去重配置
FILE_HEADER_SIZE = 4096  # 读取文件头部 4KB 计算哈希


def compute_file_fingerprint(filename, file_size, file_data):
    """
    计算文件指纹，用于去重和物理文件命名
    指纹 = MD5(原始文件名 + 文件大小 + 头部4KB数据)
    """
    # 组合特征数据
    feature = f"{filename}_{file_size}".encode('utf-8')
    feature += file_data[:FILE_HEADER_SIZE]
    
    # 计算 MD5 哈希，取前 16 位作为指纹
    fingerprint = hashlib.md5(feature).hexdigest()[:16]
    return fingerprint


def save_tasks_to_file():
    """保存任务列表到 JSON 文件"""
    try:
        # 只保存最近 MAX_TASKS 条记录
        sorted_tasks = sorted(
            tasks.values(),
            key=lambda x: x['created_at'],
            reverse=True
        )[:MAX_TASKS]

        data = {
            'tasks': sorted_tasks,
            'logs': {task: task_logs.get(task, []) for task in [t['task_id'] for t in sorted_tasks]}
        }

        with open(TASKS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[错误] 保存任务失败: {e}")


def load_tasks_from_file():
    """从 JSON 文件加载任务列表"""
    if not TASKS_FILE.exists():
        return

    try:
        with open(TASKS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 加载任务
        for task in data.get('tasks', []):
            tasks[task['task_id']] = task

        # 加载日志
        for task_id, logs in data.get('logs', {}).items():
            task_logs[task_id] = logs

        print(f"[信息] 已加载 {len(tasks)} 个历史任务")
    except Exception as e:
        print(f"[错误] 加载任务失败: {e}")


def check_cancelled(task_id):
    """检查任务是否被取消，如果是则抛出异常中断"""
    if task_id in tasks and tasks[task_id]['status'] == 'cancelled':
        raise Exception('任务已被用户取消')


@app.route('/')
def index():
    """主页 - 文件上传和处理配置"""
    return render_template('index.html')


@app.route('/task/<task_id>')
def task_page(task_id):
    """任务进度页面"""
    return render_template('task.html', task_id=task_id)


@app.route('/settings')
def settings_page():
    """系统设置页面"""
    return render_template('settings.html')


@app.route('/prompts')
def prompts_page():
    """提示词配置页面"""
    return render_template('prompts.html')


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """文件上传 API（指纹去重 + 原始文件名显示）"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '没有文件'}), 400

    file = request.files['file']
    original_filename = file.filename or ''
    
    if original_filename == '':
        return jsonify({'success': False, 'message': '未选择文件'}), 400

    # 验证文件扩展名
    file_ext = Path(original_filename).suffix.lower()
    if file_ext not in ['.txt', '.docx']:
        return jsonify({
            'success': False,
            'message': f'不支持的格式: {file_ext}，仅支持 .txt 和 .docx'
        }), 400

    # 读取文件内容
    file_data = file.read()
    file_size = len(file_data)

    # 计算指纹（用于去重和物理文件名）
    fingerprint = compute_file_fingerprint(original_filename, file_size, file_data)
    physical_filename = f"{fingerprint}{file_ext}"
    upload_path = UPLOAD_DIR / physical_filename

    # 检查是否已存在（指纹去重）
    is_duplicate = upload_path.exists()

    # 如果不重复，保存文件
    if not is_duplicate:
        with open(upload_path, 'wb') as f:
            f.write(file_data)

    return jsonify({
        'success': True,
        'duplicate': is_duplicate,
        'file_id': fingerprint,  # 指纹作为 ID
        'filename': original_filename,  # 原始文件名用于显示
        'file_size': file_size,
        'message': '文件已处理'
    })


@app.route('/api/process', methods=['POST'])
def process_document_api():
    """创建处理任务 API"""
    data = request.json
    task_id = data.get('task_id')
    mode = data.get('mode')
    version = data.get('version', 'default')
    original_filename = data.get('original_filename')  # 从前端获取原始文件名

    if not task_id or not mode:
        return jsonify({'success': False, 'message': '缺少必要参数'}), 400

    # 如果没有提供原始文件名，使用 task_id 作为 fallback
    if not original_filename:
        original_filename = task_id

    # 查找文件
    input_file = None
    for ext in ['.txt', '.docx']:
        file_path = UPLOAD_DIR / f"{task_id}{ext}"
        if file_path.exists():
            input_file = str(file_path)
            break

    if not input_file:
        return jsonify({'success': False, 'message': '文件不存在'}), 404

    # 创建任务
    tasks[task_id] = {
        'task_id': task_id,
        'status': 'pending',
        'mode': mode,
        'version': version,
        'original_filename': original_filename,  # 使用前端传递的原始文件名
        'input_filename': Path(input_file).name,
        'output_filename': None,
        'progress': 0,
        'current': 0,
        'total': 0,
        'message': '任务已创建',
        'error_message': None,
        'created_at': datetime.now().isoformat(),
        'completed_at': None
    }
    task_logs[task_id] = []

    # 保存任务
    save_tasks_to_file()

    # 启动后台处理线程
    thread = threading.Thread(
        target=run_task,
        args=(task_id, mode, version, input_file)  # 传递 version 参数
    )
    thread.daemon = True
    thread.start()

    return jsonify({
        'success': True,
        'task_id': task_id,
        'message': '任务已创建并开始处理'
    })


@app.route('/api/tasks/<task_id>')
def get_task_status(task_id):
    """获取任务状态"""
    if task_id not in tasks:
        return jsonify({'success': False, 'message': '任务不存在'}), 404
    
    return jsonify({
        'success': True,
        'task': tasks[task_id]
    })


@app.route('/api/tasks')
def list_tasks():
    """获取所有任务列表"""
    task_list = sorted(
        tasks.values(),
        key=lambda x: x['created_at'],
        reverse=True
    )[:20]  # 只返回最近 20 个
    
    return jsonify({
        'success': True,
        'tasks': task_list
    })


@app.route('/api/tasks/<task_id>/cancel', methods=['POST'])
def cancel_task_api(task_id):
    """取消任务"""
    if task_id not in tasks:
        return jsonify({'success': False, 'message': '任务不存在'}), 404

    tasks[task_id]['status'] = 'cancelled'
    tasks[task_id]['message'] = '任务已取消'
    tasks[task_id]['completed_at'] = datetime.now().isoformat()

    # 保存任务
    save_tasks_to_file()

    return jsonify({
        'success': True,
        'message': '任务已取消'
    })


@app.route('/api/tasks/<task_id>/restart', methods=['POST'])
def restart_task_api(task_id):
    """重启任务"""
    if task_id not in tasks:
        return jsonify({'success': False, 'message': '任务不存在'}), 404

    task = tasks[task_id]

    # 检查任务是否可以重启（只允许已完成、失败或取消的任务）
    if task['status'] not in ['completed', 'failed', 'cancelled']:
        return jsonify({
            'success': False,
            'message': '只能重启已完成、失败或取消的任务'
        }), 400

    # 查找输入文件
    input_file = None
    for ext in ['.txt', '.docx']:
        file_path = UPLOAD_DIR / f"{task_id}{ext}"
        if file_path.exists():
            input_file = str(file_path)
            break

    if not input_file:
        return jsonify({'success': False, 'message': '输入文件不存在'}), 404

    # 重置任务状态
    task.update({
        'status': 'pending',
        'progress': 0,
        'current': 0,
        'total': 0,
        'message': '任务已重启，等待处理...',
        'error_message': None,
        'completed_at': None,
        'output_filename': None
    })

    # 清空日志
    task_logs[task_id] = []

    # 保存任务
    save_tasks_to_file()

    # 启动后台处理线程
    thread = threading.Thread(
        target=run_task,
        args=(task_id, task['mode'], task.get('version', 'default'), input_file)
    )
    thread.daemon = True
    thread.start()

    return jsonify({
        'success': True,
        'task_id': task_id,
        'message': '任务已重启并开始处理'
    })


@app.route('/api/tasks/<task_id>', methods=['DELETE'])
def delete_task_api(task_id):
    """删除任务"""
    if task_id not in tasks:
        return jsonify({'success': False, 'message': '任务不存在'}), 404

    task = tasks[task_id]

    # 不允许删除正在处理的任务
    if task['status'] == 'processing':
        return jsonify({
            'success': False,
            'message': '无法删除正在处理中的任务，请先取消任务'
        }), 400

    # 删除输出文件
    original_name = task.get('original_filename', task_id)
    deleted_files = []
    for ext in ['.docx', '.txt']:
        for pattern in [
            f"{original_name}_output{ext}",
            f"{original_name}_fixed{ext}",
            f"{original_name}_grammar{ext}",
            f"{task_id}_output{ext}",
            f"{task_id}_fixed{ext}",
            f"{task_id}_grammar{ext}",
        ]:
            file_path = RESULTS_DIR / pattern
            if file_path.exists():
                file_path.unlink()
                deleted_files.append(pattern)

    # 删除任务记录
    tasks.pop(task_id, None)
    task_logs.pop(task_id, None)
    task_choices.pop(task_id, None)

    # 保存更新后的任务列表
    save_tasks_to_file()

    return jsonify({
        'success': True,
        'message': '任务已删除',
        'deleted_files': deleted_files
    })


@app.route('/api/download/<task_id>')
def download_result(task_id):
    """下载结果文件"""
    file_type = request.args.get('type', 'output')

    if file_type == 'input':
        # 下载原始文件
        for ext in ['.txt', '.docx']:
            file_path = UPLOAD_DIR / f"{task_id}{ext}"
            if file_path.exists():
                return send_file(
                    str(file_path),
                    as_attachment=True,
                    download_name=file_path.name
                )
        return jsonify({'success': False, 'message': '原始文件不存在'}), 404

    else:
        # 下载输出文件
        original_name = tasks.get(task_id, {}).get('original_filename', task_id)
        
        for ext in ['.docx', '.txt']:
            for pattern in [
                f"{original_name}_fixed{ext}",
                f"{original_name}_output{ext}",
                f"{task_id}_fixed{ext}",  # 向后兼容旧任务
                f"{task_id}_output{ext}",
                f"{original_name}_grammar{ext}",
                f"{task_id}_grammar{ext}",
            ]:
                file_path = RESULTS_DIR / pattern
                if file_path.exists():
                    return send_file(
                        str(file_path),
                        as_attachment=True,
                        download_name=pattern
                    )

        return jsonify({'success': False, 'message': '输出文件不存在'}), 404


@app.route('/api/preview/<task_id>')
def preview_result(task_id):
    """预览结果文件（仅支持 TXT）"""
    if task_id not in tasks:
        return jsonify({'success': False, 'message': '任务不存在'}), 404

    task = tasks[task_id]
    original_name = task.get('original_filename', task_id)
    output_filename = task.get('output_filename')

    if not output_filename:
        return jsonify({'success': False, 'message': '输出文件未生成'}), 404

    file_path = RESULTS_DIR / output_filename

    if not file_path.exists():
        return jsonify({'success': False, 'message': '输出文件不存在'}), 404

    # 检查文件类型
    file_ext = file_path.suffix.lower()

    if file_ext == '.txt':
        # 读取 TXT 文件内容
        try:
            content = file_path.read_text(encoding='utf-8')
            return jsonify({
                'success': True,
                'type': 'txt',
                'content': content,
                'filename': output_filename,
                'size': file_path.stat().st_size
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'读取文件失败: {str(e)}'
            }), 500
    else:
        # DOCX 等非文本文件，返回文件信息但不返回内容
        return jsonify({
            'success': True,
            'type': 'binary',
            'filename': output_filename,
            'size': file_path.stat().st_size,
            'message': f'{file_ext.upper()} 文件需要下载后查看'
        })


@app.route('/api/uploaded-files')
def list_uploaded_files():
    """获取 uploads 目录中所有已上传文件列表"""
    files = []
    
    # 扫描 uploads 目录
    for file_path in UPLOAD_DIR.iterdir():
        if file_path.is_file():
            file_ext = file_path.suffix.lower()
            if file_ext in ['.txt', '.docx']:
                file_id = file_path.stem  # 指纹 ID
                file_size = file_path.stat().st_size
                
                # 从任务记录中查找原始文件名
                original_filename = None
                upload_time = None
                
                for task in tasks.values():
                    if task.get('input_filename') == file_path.name:
                        original_filename = task.get('original_filename')
                        upload_time = task.get('created_at')
                        break
                
                # 如果没找到任务记录，使用物理文件名
                if not original_filename:
                    original_filename = file_path.name
                
                files.append({
                    'file_id': file_id,
                    'original_filename': original_filename,
                    'file_size': file_size,
                    'file_ext': file_ext,
                    'upload_time': upload_time
                })
    
    # 按上传时间倒序排序
    files.sort(key=lambda x: x['upload_time'] or '', reverse=True)
    
    return jsonify({
        'success': True,
        'files': files
    })


@app.route('/api/uploaded-files/<file_id>', methods=['DELETE'])
def delete_uploaded_file(file_id):
    """删除已上传的文件"""
    deleted = []
    
    # 查找并删除物理文件
    for ext in ['.txt', '.docx']:
        file_path = UPLOAD_DIR / f"{file_id}{ext}"
        if file_path.exists():
            file_path.unlink()
            deleted.append(file_path.name)
    
    # 删除相关的未完成/失败任务记录
    tasks_to_remove = []
    for task_id, task in tasks.items():
        if task.get('input_filename') in deleted:
            # 只删除未完成任务（pending/processing/failed）
            if task.get('status') in ['pending', 'processing', 'failed']:
                tasks_to_remove.append(task_id)
    
    for task_id in tasks_to_remove:
        # 清理任务记录
        tasks.pop(task_id, None)
        task_logs.pop(task_id, None)
        task_choices.pop(task_id, None)
    
    # 保存更新后的任务列表
    save_tasks_to_file()
    
    return jsonify({
        'success': True,
        'message': f'已删除 {len(deleted)} 个文件',
        'deleted_files': deleted
    })


@app.route('/api/config')
def get_config():
    """获取系统配置"""
    from config import BASE_URL, API_KEY, MODEL_NAME
    
    return jsonify({
        'success': True,
        'config': {
            'base_url': BASE_URL,
            'api_key': '****' if API_KEY else '',
            'api_key_set': bool(API_KEY),
            'model_name': MODEL_NAME or '(未设置)'
        }
    })


@app.route('/api/config/test', methods=['POST'])
def test_config():
    """测试 LLM 连接"""
    import requests

    data = request.json
    base_url = data.get('base_url', '').rstrip('/')
    api_key = data.get('api_key', '')
    model_name = data.get('model_name', 'default')

    url = f"{base_url}/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": "你好，请回复'连接成功'"}],
        "stream": False,
        "max_tokens": 50
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()

        result = response.json()
        reply = result.get("choices", [{}])[0].get("message", {}).get("content", "")

        return jsonify({
            'success': True,
            'message': '连接成功',
            'reply': reply,
            'model': result.get("model", model_name)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'连接失败: {str(e)}'
        }), 500


@app.route('/api/config/save', methods=['POST'])
def save_config():
    """保存配置到 src/config.py"""
    import re
    
    data = request.json
    base_url = data.get('base_url', '')
    api_key = data.get('api_key', '')
    model_name = data.get('model_name', '')
    
    # 配置文件路径
    config_file = Path(__file__).parent.parent / "src" / "config.py"
    
    if not config_file.exists():
        return jsonify({
            'success': False,
            'message': f'配置文件不存在: {config_file}'
        }), 404
    
    try:
        # 读取配置文件内容
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 使用正则表达式替换配置值
        # 替换 BASE_URL
        content = re.sub(
            r"BASE_URL\s*=\s*os\.getenv\('BASE_URL',\s*'[^']*'\)",
            f"BASE_URL = os.getenv('BASE_URL', '{base_url}')",
            content
        )
        
        # 替换 API_KEY
        content = re.sub(
            r"API_KEY\s*=\s*os\.getenv\('API_KEY',\s*'[^']*'\)",
            f"API_KEY = os.getenv('API_KEY', '{api_key}')",
            content
        )
        
        # 替换 MODEL_NAME
        content = re.sub(
            r"MODEL_NAME\s*=\s*os\.getenv\('MODEL_NAME',\s*'[^']*'\)",
            f"MODEL_NAME = os.getenv('MODEL_NAME', '{model_name}')",
            content
        )
        
        # 写回配置文件
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return jsonify({
            'success': True,
            'message': '配置已保存'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'保存失败: {str(e)}'
        }), 500


@app.route('/api/prompts')
def get_prompts():
    """获取所有提示词配置"""
    from prompts.loader import get_all_prompts
    
    prompts_data = get_all_prompts()
    
    return jsonify({
        'success': True,
        'prompts': prompts_data
    })


@app.route('/api/prompts/save', methods=['POST'])
def save_prompts():
    """保存提示词版本"""
    from prompts.loader import save_version
    
    data = request.json
    category = data.get('category')
    version = data.get('version')
    prompt_data = data.get('data', {})
    
    try:
        result = save_version(category, version, prompt_data)
        
        if result == 'success':
            # 重新加载提示词模块
            import importlib
            import prompts
            importlib.reload(prompts)
            
            return jsonify({
                'success': True,
                'message': '版本已保存'
            })
        else:
            return jsonify({
                'success': False,
                'message': result
            }), 400
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'保存失败: {str(e)}'
        }), 500


@app.route('/api/prompts/delete', methods=['POST'])
def delete_prompt_version():
    """删除提示词版本"""
    from prompts.loader import delete_version
    
    data = request.json
    category = data.get('category')
    version = data.get('version')
    
    try:
        result = delete_version(category, version)
        
        if result == 'success':
            return jsonify({
                'success': True,
                'message': '版本已删除'
            })
        else:
            return jsonify({
                'success': False,
                'message': result
            }), 400
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'删除失败: {str(e)}'
        }), 500


@app.route('/api/tasks/<task_id>/txt-choice', methods=['POST'])
def submit_txt_choice(task_id):
    """提交用户对已存在 TXT 文件的选择"""
    data = request.json
    choice = data.get('choice')  # 'reuse', 'regenerate', 'cancel'

    if choice not in ['reuse', 'regenerate', 'cancel']:
        return jsonify({
            'success': False,
            'message': '无效的选择，必须是 reuse、regenerate 或 cancel'
        }), 400

    # 存储选择
    task_choices[task_id] = choice

    # 设置事件通知后端继续
    if task_id in task_events:
        task_events[task_id].set()

    return jsonify({
        'success': True,
        'message': f'已选择: {choice}'
    })


def run_task(task_id, mode, version, input_file):
    """后台运行任务"""
    try:
        if mode == 'full':
            run_full_mode(task_id, input_file, version)
        elif mode == 'chapter':
            run_chapter_mode(task_id, input_file, version)
        elif mode == 'paragraph':
            run_paragraph_mode(task_id, input_file, version)
    except Exception as e:
        # 检查是否是取消异常
        if '任务已被用户取消' in str(e):
            tasks[task_id].update({
                'status': 'cancelled',
                'message': '任务已取消',
                'completed_at': datetime.now().isoformat()
            })
            emit_log(task_id, 'log', '[取消] 任务已被用户取消')
            # 保存已完成/取消的任务
            save_tasks_to_file()
        else:
            tasks[task_id].update({
                'status': 'failed',
                'error_message': str(e),
                'message': f'处理失败: {str(e)}',
                'completed_at': datetime.now().isoformat()
            })
            task_logs[task_id].append({
                'type': 'error',
                'message': f'[错误] {str(e)}'
            })
            socketio.emit('task_update', {
                'task_id': task_id,
                'type': 'error',
                'message': f'[错误] {str(e)}'
            }, room=task_id)
            # 保存已完成/失败的任务
            save_tasks_to_file()


def run_full_mode(task_id, input_file, version='default'):
    """全文模式处理"""
    # 从 prompts 模块动态加载指定版本
    from prompts.loader import get_prompt
    
    try:
        prompt_data = get_prompt('full', version)
        config = {
            'role': {'role': 'system', 'content': prompt_data['role']},
            'prompt_template': prompt_data['prompt'],
        }
    except Exception as e:
        tasks[task_id].update({
            'status': 'failed',
            'error_message': f'加载提示词失败: {str(e)}',
            'completed_at': datetime.now().isoformat()
        })
        emit_log(task_id, 'error', f'[错误] 加载提示词失败: {str(e)}')
        return

    tasks[task_id].update({
        'status': 'processing',
        'message': '正在读取文件...',
        'progress': 10
    })
    emit_log(task_id, 'log', '[全文模式] 开始处理文件')

    content = read_file_content(input_file)

    tasks[task_id].update({
        'message': '正在调用 LLM 处理全文...',
        'progress': 30
    })
    emit_log(task_id, 'log', '[LLM] 正在生成学术摘要...')
    
    # 检查取消
    check_cancelled(task_id)

    prompt = config['prompt_template'].format(content=content)
    messages = [config['role'], {'role': 'user', 'content': prompt}]
    result = llm_chat(messages, task_id=task_id)
    
    # LLM 调用后再次检查
    check_cancelled(task_id)

    output_file = str(RESULTS_DIR / f"{tasks[task_id]['original_filename']}_output.txt")
    save_to_txt(result, output_file)

    tasks[task_id].update({
        'status': 'completed',
        'progress': 100,
        'message': '处理完成',
        'output_filename': f"{tasks[task_id]['original_filename']}_output.txt",
        'completed_at': datetime.now().isoformat()
    })
    emit_log(task_id, 'completed', '[完成] 全文处理完成')
    # 保存已完成的任务
    save_tasks_to_file()


def run_chapter_mode(task_id, input_file, version='default'):
    """章节模式处理"""
    # 从 prompts 模块动态加载指定版本
    from prompts.loader import get_prompt
    
    try:
        prompt_data = get_prompt('chapter', version)
        config = {
            'role': {'role': 'system', 'content': prompt_data['role']},
            'prompt_template': prompt_data['prompt'],
        }
    except Exception as e:
        tasks[task_id].update({
            'status': 'failed',
            'error_message': f'加载提示词失败: {str(e)}',
            'completed_at': datetime.now().isoformat()
        })
        emit_log(task_id, 'error', f'[错误] 加载提示词失败: {str(e)}')
        return

    tasks[task_id].update({
        'status': 'processing',
        'message': '正在读取文件并拆分章节...',
        'progress': 10
    })
    emit_log(task_id, 'log', '[章节模式] 开始处理文件')

    content = read_file_content(input_file)
    chapters = split_content_by_chapters(content)

    tasks[task_id].update({
        'total': len(chapters),
        'message': f'识别到 {len(chapters)} 个章节，开始处理...'
    })
    emit_log(task_id, 'log', f'[信息] 识别到 {len(chapters)} 个章节')

    output_file = str(RESULTS_DIR / f"{tasks[task_id]['original_filename']}_output.txt")
    save_to_txt("", output_file, "章节总结", mode='w')

    for idx, chapter in enumerate(chapters, 1):
        # 每个章节开始前检查取消
        check_cancelled(task_id)
        
        tasks[task_id].update({
            'current': idx,
            'progress': int((idx / len(chapters)) * 90),
            'message': f'处理章节 {idx}/{len(chapters)}: {chapter["title"]}'
        })
        emit_log(task_id, 'log', f'[章节 {idx}/{len(chapters)}] {chapter["title"]}')

        prompt = config['prompt_template'].format(
            content=chapter['content'],
            chapter_title=chapter['title']
        )
        messages = [config['role'], {'role': 'user', 'content': prompt}]
        summary = llm_chat(messages, task_id=task_id)

        chapter_content = f"\n\n{chapter['title']}\n\n{summary}\n\n"
        save_to_txt(chapter_content, output_file, "", mode='a')

    tasks[task_id].update({
        'status': 'completed',
        'progress': 100,
        'message': f'处理完成，共 {len(chapters)} 个章节',
        'output_filename': f"{tasks[task_id]['original_filename']}_output.txt",
        'completed_at': datetime.now().isoformat()
    })
    emit_log(task_id, 'completed', f'[完成] 共处理 {len(chapters)} 个章节')
    # 保存已完成的任务
    save_tasks_to_file()


def run_paragraph_mode(task_id, input_file, version):
    """段落模式处理"""
    from prompts.loader import get_prompt

    try:
        # 根据用户选择的版本加载提示词
        prompt_data = get_prompt('paragraph', version)
        PROCESSOR_CONFIGS['paragraph'] = {
            'role': {'role': 'system', 'content': prompt_data['role']},
            'prompt_template': prompt_data['prompt'],
        }
        print(f"[信息] 使用段落模式版本: {version}")
    except Exception as e:
        tasks[task_id].update({
            'status': 'failed',
            'error_message': f'加载提示词失败: {str(e)}',
            'completed_at': datetime.now().isoformat()
        })
        emit_log(task_id, 'error', f'[错误] 加载提示词失败: {str(e)}')
        return

    provider = create_provider(input_file)
    original_name = tasks[task_id].get('original_filename', Path(input_file).stem)
    task_id_stem = task_id

    # 检查是否存在同名的 grammar.txt
    existing_grammar_txt = None

    # 方案1: 在 RESULTS_DIR 中查找
    for pattern in [f"{original_name}*_grammar.txt", f"{task_id_stem}*_grammar.txt"]:
        for f in RESULTS_DIR.glob(pattern):
            if '_grammar' in f.name:
                existing_grammar_txt = str(f)
                break
        if existing_grammar_txt:
            break

    # 方案2: 检查 uploads 目录
    if not existing_grammar_txt:
        input_dir = Path(input_file).parent
        for pattern in [f"{original_name}*_grammar.txt", f"{task_id_stem}*_grammar.txt"]:
            for f in input_dir.glob(pattern):
                if '_grammar' in f.name:
                    existing_grammar_txt = str(f)
                    break
            if existing_grammar_txt:
                break

    # 方案3: 模糊匹配
    if not existing_grammar_txt:
        for f in RESULTS_DIR.glob("*_grammar.txt"):
            if original_name in f.name or task_id_stem[:8] in f.name:
                existing_grammar_txt = str(f)
                break

    if existing_grammar_txt and Path(existing_grammar_txt).exists():
        # 通知前端存在已存在的 TXT 文件
        socketio.emit('existing_txt_found', {
            'task_id': task_id,
            'txt_file': existing_grammar_txt,
            'message': f'检测到已存在的语法检查文件：{Path(existing_grammar_txt).name}'
        }, room=task_id)

        # 创建等待事件
        event = threading.Event()
        task_events[task_id] = event

        tasks[task_id].update({
            'status': 'waiting',
            'message': '等待用户选择处理方式...',
            'progress': 0,
            'existing_txt': existing_grammar_txt,
        })
        emit_log(task_id, 'log', f'[发现] 已存在的语法检查文件：{existing_grammar_txt}')
        emit_log(task_id, 'choice_needed', '请选择：1.复用现有TXT 2.重新检查 3.取消')
        
        # 等待用户选择（最多 5 分钟）
        event.wait(timeout=300)
        
        choice = task_choices.get(task_id, 'cancel')
        
        # 清理
        del task_events[task_id]
        if task_id in task_choices:
            del task_choices[task_id]
        
        if choice == 'reuse':
            # 复用现有 TXT 生成 DOCX
            emit_log(task_id, 'log', '[复用] 使用现有 TXT 文件生成 DOCX...')
            tasks[task_id].update({
                'status': 'processing',
                'message': '正在从 TXT 生成 DOCX...',
                'progress': 50,
            })

            original_name = tasks[task_id].get('original_filename', Path(input_file).stem)
            output_suffix = Path(input_file).suffix
            output_path_fixed = str(RESULTS_DIR / f"{original_name}_fixed{output_suffix}")

            # 应用 TXT 到文档，直接保存到 RESULTS_DIR
            try:
                from docx_editor import apply_txt_to_document_with_output

                # 使用新函数，直接指定输出路径
                _, modified_count = apply_txt_to_document_with_output(
                    provider, existing_grammar_txt, output_path_fixed
                )

                emit_log(task_id, 'log', f'[完成] 已生成 DOCX 文件（{modified_count} 个段落）')

            except ImportError:
                # 兼容旧版本
                try:
                    apply_txt_to_document(provider, existing_grammar_txt)
                    
                    import shutil
                    src_path = provider.infer_output_path()

                    if Path(src_path).exists():
                        shutil.move(str(src_path), output_path_fixed)
                    else:
                        raise Exception(f"生成的文件不存在: {src_path}")
                        
                except Exception as e2:
                    raise
                    
            except Exception as e:
                raise

            tasks[task_id].update({
                'status': 'completed',
                'progress': 100,
                'message': f'已从现有 TXT 生成 DOCX',
                'output_filename': f"{original_name}_fixed{output_suffix}",
                'completed_at': datetime.now().isoformat()
            })
            emit_log(task_id, 'completed', f'[完成] 已从现有 TXT 生成 DOCX')
            # 保存已完成的任务
            save_tasks_to_file()
            return
        
        elif choice == 'cancel':
            tasks[task_id].update({
                'status': 'cancelled',
                'message': '用户取消操作',
                'completed_at': datetime.now().isoformat()
            })
            emit_log(task_id, 'log', '[取消] 操作已取消')
            # 保存已取消的任务
            save_tasks_to_file()
            return
        
        # choice == 'regenerate'，继续正常流程
        emit_log(task_id, 'log', '[重新检查] 开始重新进行语法检查...')

    tasks[task_id].update({
        'status': 'processing',
        'message': '正在读取文档...',
        'progress': 10
    })
    emit_log(task_id, 'log', '[段落模式] 开始处理文件')

    paragraphs = provider.read_paragraphs()
    total_paragraphs = len(paragraphs)

    # 找到处理范围
    process_until = total_paragraphs
    for idx, text in enumerate(paragraphs):
        if is_ref_section(text.strip()):
            process_until = idx

    tasks[task_id].update({
        'total': process_until,
        'message': f'处理范围：第 1 ~ {process_until} 段（共 {total_paragraphs} 段）'
    })
    emit_log(task_id, 'log', f'[信息] 处理范围：第 1 ~ {process_until} 段')

    # 使用原始文件名生成 TXT 路径，保存到 RESULTS_DIR
    original_name = tasks[task_id].get('original_filename', Path(input_file).stem)
    output_txt = str(RESULTS_DIR / f"{original_name}_grammar.txt")

    save_to_txt("", output_txt, title="", mode='w')

    modifications = {}

    for idx, para_text in enumerate(paragraphs[:process_until], 1):
        # 每个段落前检查取消
        check_cancelled(task_id)

        if _skip_para(para_text):
            continue

        progress = int((idx / process_until) * 90)
        tasks[task_id].update({
            'current': idx,
            'progress': progress,
            'message': f'检查段落 {idx}/{process_until}'
        })
        emit_log(task_id, 'log', f'[段落 {idx}/{process_until}] 开始检查...')

        # 使用带进度推送的 LLM 调用
        config = PROCESSOR_CONFIGS['paragraph']
        prompt = config['prompt_template'].format(content=para_text)
        messages = [config['role'], {'role': 'user', 'content': prompt}]
        llm_result = llm_chat(messages, task_id=task_id)
        original = para_text

        if llm_result:
            _save_mods_to_txt(output_txt, idx, original, llm_result)
            corrected_text = _parse_modified_text(llm_result)
            if corrected_text:
                modifications[idx] = corrected_text

    # 应用修改并保存
    output_path = provider.infer_output_path()
    original_name = tasks[task_id].get('original_filename', Path(input_file).stem)
    output_path_fixed = str(RESULTS_DIR / f"{original_name}_fixed{Path(output_path).suffix}")
    modified_count = provider.apply_and_save(modifications, output_path_fixed)

    tasks[task_id].update({
        'status': 'completed',
        'progress': 100,
        'message': f'处理完成，修改 {modified_count} 个段落',
        'output_filename': f"{original_name}_fixed{Path(output_path).suffix}",
        'completed_at': datetime.now().isoformat()
    })
    emit_log(task_id, 'completed', f'[完成] 总段落数：{total_paragraphs}，修改段落：{modified_count}')
    # 保存已完成的任务
    save_tasks_to_file()


def emit_log(task_id, log_type, message):
    """发送日志并存储"""
    log_data = {
        'type': log_type,
        'message': message,
        'timestamp': datetime.now().isoformat()
    }
    task_logs[task_id].append(log_data)
    socketio.emit('task_log', {
        'task_id': task_id,
        **log_data
    }, room=task_id)
    
    # 自动保存
    save_tasks_to_file()


# SocketIO 事件处理
@socketio.on('connect')
def handle_connect():
    print('客户端已连接')


@socketio.on('disconnect')
def handle_disconnect():
    print('客户端已断开连接')


@socketio.on('subscribe_task')
def handle_subscribe(data):
    """订阅任务更新"""
    task_id = data.get('task_id')
    if task_id:
        join_room(task_id)
        if task_id in tasks:
            emit('task_status', tasks[task_id])
            for log in task_logs.get(task_id, []):
                emit('task_log', {'task_id': task_id, **log})
            # 如果任务正在等待用户选择，重新发送 existing_txt_found 事件
            task_data = tasks[task_id]
            if task_data.get('status') == 'waiting' and task_data.get('existing_txt'):
                emit('existing_txt_found', {
                    'task_id': task_id,
                    'txt_file': task_data['existing_txt'],
                    'message': f'检测到已存在的语法检查文件：{Path(task_data["existing_txt"]).name}'
                })


if __name__ == '__main__':
    import atexit
    
    # 启动时加载历史任务
    load_tasks_from_file()
    
    # 应用退出时保存当前任务状态
    atexit.register(lambda: save_tasks_to_file())

    print("=" * 60)
    print("  LLM-Doc-Processor Web UI")
    print("=" * 60)
    print()
    print("  访问地址: http://localhost:5000")
    print("  按 Ctrl+C 停止服务")
    print()
    print("=" * 60)

    socketio.run(app, host='127.0.0.1', port=5000, debug=False, use_reloader=False)
