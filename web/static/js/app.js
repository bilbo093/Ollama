/**
 * LLM-Doc-Processor Web UI - JavaScript
 */

// 全局状态
let selectedFile = null;
let uploading = false;
let processing = false;
let uploadedFiles = []; // 存储已上传文件列表

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initUploadArea();
    initModeChange();
    initProcessButton();
    loadAllVersions();

    // 如果在主页，加载任务列表和已上传文件
    if (window.location.pathname === '/') {
        loadTasks();
        loadUploadedFiles();
    }
});

// ==================== 文件上传 ====================

function initUploadArea() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    
    if (!uploadArea || !fileInput) return;
    
    // 点击上传
    uploadArea.addEventListener('click', () => fileInput.click());
    
    // 文件选择
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });
    
    // 拖拽上传
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        
        if (e.dataTransfer.files.length > 0) {
            handleFileSelect(e.dataTransfer.files[0]);
        }
    });
}

async function handleFileSelect(file) {
    // 验证文件类型
    const validExtensions = ['.txt', '.docx'];
    const ext = '.' + file.name.split('.').pop().toLowerCase();

    if (ext === '.doc') {
        showNotification('不支持旧版 .doc 格式，请在 Word 中另存为 .docx 后再上传', 'error');
        return;
    }

    if (!validExtensions.includes(ext)) {
        showNotification('仅支持 .txt 和 .docx 格式', 'error');
        return;
    }

    // 验证文件大小（500MB）
    if (file.size > 500 * 1024 * 1024) {
        showNotification('文件大小不能超过 500MB', 'error');
        return;
    }

    // 立即上传到服务器
    uploading = true;
    showNotification('正在上传文件...', 'info');
    
    try {
        const uploadResult = await uploadFile(file);
        
        // 更新全局状态，保存文件ID和原始文件名
        selectedFile = {
            file: file,
            file_id: uploadResult.file_id,
            original_filename: uploadResult.filename
        };
        
        // 更新 UI
        const fileInfo = document.getElementById('fileInfo');
        const fileName = document.getElementById('fileName');
        const fileSize = document.getElementById('fileSize');
        const processBtn = document.getElementById('processBtn');

        if (fileInfo && fileName && fileSize) {
            fileInfo.style.display = 'flex';
            fileName.textContent = uploadResult.filename;
            fileSize.textContent = formatFileSize(uploadResult.file_size);
        }

        if (processBtn) {
            processBtn.disabled = false;
        }

        // 根据是否重复给出提示
        if (uploadResult.duplicate) {
            showNotification('文件已存在，已自动复用指纹记录', 'info');
        } else {
            showNotification('文件已选择', 'success');
        }
        
    } catch (error) {
        showNotification('上传失败: ' + error.message, 'error');
        selectedFile = null;
    } finally {
        uploading = false;
    }
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / 1024 / 1024).toFixed(2) + ' MB';
}

async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData
    });
    
    const data = await response.json();
    
    if (!data.success) {
        throw new Error(data.message);
    }
    
    return data;
}

// ==================== 处理模式 ====================

// 加载所有模式的版本列表
async function loadAllVersions() {
    try {
        const response = await fetch('/api/prompts');
        const data = await response.json();
        
        if (data.success && data.prompts) {
            // 为每种模式加载版本
            const modes = ['full', 'chapter', 'paragraph'];
            
            modes.forEach(mode => {
                if (data.prompts[mode]) {
                    const select = document.getElementById(`version-${mode}`);
                    const hint = document.getElementById(`versionHint-${mode}`);
                    
                    if (select) {
                        select.innerHTML = '';
                        
                        data.prompts[mode].versions.forEach(v => {
                            const option = document.createElement('option');
                            option.value = v.id;
                            option.textContent = v.name;
                            if (v.is_default) option.selected = true;
                            select.appendChild(option);
                        });
                    }
                    
                    if (hint && data.prompts[mode].versions.length > 0) {
                        const versions = data.prompts[mode].versions.map(v => v.name).join('、');
                        hint.textContent = `可用版本：${versions}`;
                    }
                }
            });
        }
    } catch (error) {
        console.error('加载版本失败:', error);
    }
}

// 模式切换时显示对应的版本选择框
function updateVersionVisibility(mode) {
    const modes = ['full', 'chapter', 'paragraph'];
    
    modes.forEach(m => {
        const section = document.getElementById(`versionSection-${m}`);
        if (section) {
            section.style.display = m === mode ? 'block' : 'none';
        }
    });
}

// 修改 initModeChange 函数
function initModeChange() {
    const modeRadios = document.querySelectorAll('input[name="mode"]');
    const modeDesc = document.getElementById('modeDesc');
    
    if (!modeRadios.length) return;

    const descriptions = {
        full: '全文模式：将整个文档一次性送入 LLM，适用于生成论文"总结与展望"章节',
        chapter: '章节模式：按章节拆分后逐章送入 LLM，适用于生成各章总结',
        paragraph: '段落模式：按段落拆分后逐段送入 LLM，适用于语法检查和润色'
    };

    // 初始化时根据当前选中模式显示版本框
    const checkedMode = document.querySelector('input[name="mode"]:checked');
    if (checkedMode) {
        updateVersionVisibility(checkedMode.value);
    }

    modeRadios.forEach(radio => {
        radio.addEventListener('change', (e) => {
            const mode = e.target.value;

            // 更新描述
            if (modeDesc) {
                modeDesc.querySelector('span').textContent = descriptions[mode];
            }

            // 显示对应的版本选择框
            updateVersionVisibility(mode);
        });
    });
}

// ==================== 开始处理 ====================

function initProcessButton() {
    const processBtn = document.getElementById('processBtn');
    if (!processBtn) return;
    
    processBtn.addEventListener('click', startProcess);
}

async function startProcess() {
    // selectedFile 现在是一个对象，包含 file, file_id, original_filename
    if (!selectedFile || !selectedFile.file_id || processing) return;

    processing = true;
    const processBtn = document.getElementById('processBtn');
    processBtn.disabled = true;
    processBtn.innerHTML = '<span>处理中...</span>';

    try {
        // 获取配置
        const mode = document.querySelector('input[name="mode"]:checked').value;
        const version = document.getElementById(`version-${mode}`)?.value || 'default';
        const outputFilename = document.getElementById('outputFilename')?.value || '';

        // 直接使用已上传的文件ID
        const fileId = selectedFile.file_id;
        const displayFilename = selectedFile.original_filename;

        // 创建处理任务
        showNotification('正在创建处理任务...', 'info');
        const response = await fetch('/api/process', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                task_id: fileId,
                mode: mode,
                version: version,
                original_filename: displayFilename.replace(/\.[^/.]+$/, ""),
                output_filename: outputFilename || undefined
            })
        });

        const data = await response.json();

        if (!data.success) {
            throw new Error(data.message);
        }

        showNotification('任务已创建，正在处理...', 'success');

        // 跳转到任务页面
        setTimeout(() => {
            window.location.href = `/task/${fileId}`;
        }, 500);

    } catch (error) {
        showNotification(error.message, 'error');
        processing = false;
        processBtn.disabled = false;
        processBtn.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg><span>开始处理</span>';
    }
}

// ==================== 任务列表 ====================

async function loadTasks() {
    const tbody = document.getElementById('taskTableBody');
    const emptyState = document.getElementById('emptyState');
    const table = document.getElementById('taskTable');
    
    if (!tbody) return;
    
    try {
        const response = await fetch('/api/tasks');
        const data = await response.json();
        
        if (!data.success || !data.tasks.length) {
            if (table) table.style.display = 'none';
            if (emptyState) emptyState.style.display = 'block';
            return;
        }
        
        if (table) table.style.display = 'table';
        if (emptyState) emptyState.style.display = 'none';
        
        tbody.innerHTML = data.tasks.map(task => `
            <tr>
                <td><code>${task.task_id.substring(0, 12)}...</code></td>
                <td>${task.original_filename || task.input_filename || '-'}</td>
                <td><span class="badge badge-info">${getModeLabel(task.mode)}</span></td>
                <td>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <div style="flex: 1; height: 8px; background: #ebeef5; border-radius: 4px; overflow: hidden;">
                            <div style="width: ${task.progress}%; height: 100%; background: linear-gradient(90deg, #409EFF 0%, #6366f1 100%); border-radius: 4px;"></div>
                        </div>
                        <span style="font-size: 12px; color: #909399;">${task.progress}%</span>
                    </div>
                </td>
                <td><span class="badge badge-${getStatusClass(task.status)}">${getStatusLabel(task.status)}</span></td>
                <td>
                    <a href="/task/${task.task_id}" class="btn btn-text" style="padding: 4px 8px;">查看</a>
                    ${['completed', 'failed', 'cancelled'].includes(task.status) ? `
                        <button class="btn btn-text btn-danger-text" style="padding: 4px 8px; color: #f56c6c;" onclick="deleteTask('${task.task_id}')">删除</button>
                    ` : ''}
                </td>
            </tr>
        `).join('');
        
    } catch (error) {
        console.error('加载任务列表失败:', error);
    }
}

function getModeLabel(mode) {
    const labels = { full: '全文', chapter: '章节', paragraph: '段落' };
    return labels[mode] || mode;
}

function getStatusLabel(status) {
    const labels = {
        pending: '排队中',
        processing: '处理中',
        completed: '已完成',
        failed: '失败',
        cancelled: '已取消'
    };
    return labels[status] || status;
}

function getStatusClass(status) {
    const classes = {
        pending: 'info',
        processing: 'warning',
        completed: 'success',
        failed: 'danger',
        cancelled: 'info'
    };
    return classes[status] || 'info';
}

// ==================== 任务页面 ====================

async function loadTaskStatus(taskId) {
    try {
        const response = await fetch(`/api/tasks/${taskId}`);
        const data = await response.json();
        
        if (data.success) {
            updateTaskUI(data.task);
        }
    } catch (error) {
        console.error('加载任务状态失败:', error);
    }
}

function updateTaskUI(task) {
    // 更新任务信息
    const modeEl = document.getElementById('taskMode');
    const statusEl = document.getElementById('taskStatus');
    const filenameEl = document.getElementById('taskFilename');
    const progressEl = document.getElementById('taskProgress');
    const progressFill = document.getElementById('progressFill');
    const progressMessage = document.getElementById('progressMessage');
    const cancelBtn = document.getElementById('cancelBtn');
    const restartBtn = document.getElementById('restartBtn');
    const previewBtn = document.getElementById('previewBtn');
    const downloadBtn = document.getElementById('downloadBtn');
    const homeBtn = document.getElementById('homeBtn');
    const errorAlert = document.getElementById('errorAlert');
    const errorMessage = document.getElementById('errorMessage');

    if (modeEl) {
        modeEl.textContent = getModeLabel(task.mode);
        modeEl.className = `badge badge-${task.status === 'completed' ? 'success' : 'info'}`;
    }

    if (statusEl) {
        statusEl.textContent = getStatusLabel(task.status);
        statusEl.className = `badge badge-${getStatusClass(task.status)}`;
    }

    if (filenameEl) {
        filenameEl.textContent = task.original_filename || task.input_filename || '-';
    }

    if (progressEl) {
        progressEl.textContent = `${task.current || 0} / ${task.total || 0}`;
    }

    if (progressFill) {
        progressFill.style.width = `${task.progress || 0}%`;
    }

    if (progressMessage) {
        progressMessage.textContent = task.message || '等待任务开始...';
    }

    // 显示/隐藏按钮
    if (cancelBtn) {
        cancelBtn.style.display = task.status === 'processing' ? 'inline-flex' : 'none';
    }

    if (restartBtn) {
        restartBtn.style.display = ['completed', 'failed', 'cancelled'].includes(task.status) ? 'inline-flex' : 'none';
    }

    if (downloadBtn) {
        downloadBtn.style.display = task.status === 'completed' ? 'inline-flex' : 'none';
    }

    if (previewBtn) {
        previewBtn.style.display = task.status === 'completed' ? 'inline-flex' : 'none';
    }

    if (homeBtn) {
        homeBtn.style.display = task.status === 'completed' || task.status === 'failed' || task.status === 'cancelled' ? 'inline-flex' : 'none';
    }

    // 显示错误
    if (errorAlert && errorMessage) {
        if (task.status === 'failed') {
            errorAlert.style.display = 'flex';
            errorMessage.textContent = task.error_message || '未知错误';
        } else {
            errorAlert.style.display = 'none';
        }
    }
}

async function cancelTask() {
    if (!confirm('确定要取消当前任务吗？')) return;

    const taskId = document.getElementById('taskId')?.textContent;
    if (!taskId) return;

    try {
        const response = await fetch(`/api/tasks/${taskId}/cancel`, {
            method: 'POST'
        });

        const data = await response.json();

        if (data.success) {
            showNotification('任务已取消', 'success');
            loadTaskStatus(taskId);
        } else {
            showNotification(data.message, 'error');
        }
    } catch (error) {
        showNotification('取消失败: ' + error.message, 'error');
    }
}

async function restartTask() {
    if (!confirm('确定要重启任务吗？\n\n这将清空当前进度和日志，重新开始处理。')) return;

    const taskId = document.getElementById('taskId')?.textContent;
    if (!taskId) return;

    try {
        const response = await fetch(`/api/tasks/${taskId}/restart`, {
            method: 'POST'
        });

        const data = await response.json();

        if (data.success) {
            showNotification('任务已重启，正在重新处理...', 'success');
            
            // 清空日志
            clearLogs();
            
            // 隐藏预览面板
            const previewPanel = document.getElementById('previewPanel');
            if (previewPanel) {
                previewPanel.style.display = 'none';
            }
            
            // 重新加载任务状态
            loadTaskStatus(taskId);
        } else {
            showNotification('重启失败: ' + data.message, 'error');
        }
    } catch (error) {
        showNotification('重启失败: ' + error.message, 'error');
    }
}

async function deleteTask(taskId) {
    if (!confirm('确定要删除此任务吗？\n\n任务记录和输出文件将被永久删除。')) return;

    try {
        const response = await fetch(`/api/tasks/${taskId}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (data.success) {
            showNotification('任务已删除', 'success');
            
            // 刷新任务列表
            loadTasks();
        } else {
            showNotification('删除失败: ' + data.message, 'error');
        }
    } catch (error) {
        showNotification('删除失败: ' + error.message, 'error');
    }
}

function downloadResult() {
    const taskId = document.getElementById('taskId')?.textContent;
    if (!taskId) return;

    window.open(`/api/download/${taskId}?type=output`, '_blank');
}

// ==================== 预览功能 ====================

let previewLoaded = false;

function togglePreview() {
    const panel = document.getElementById('previewPanel');
    if (!panel) return;

    if (panel.style.display === 'none') {
        panel.style.display = 'block';
        if (!previewLoaded) {
            loadPreview();
        }
    } else {
        panel.style.display = 'none';
    }
}

async function loadPreview() {
    const taskId = document.getElementById('taskId')?.textContent;
    if (!taskId) return;

    const contentEl = document.getElementById('previewContent');
    const infoEl = document.getElementById('previewFileInfo');

    if (contentEl) {
        contentEl.innerHTML = '<div class="preview-loading">加载中...</div>';
    }

    try {
        const response = await fetch(`/api/preview/${taskId}`);
        const data = await response.json();

        if (!data.success) {
            if (contentEl) {
                contentEl.innerHTML = `<div class="preview-error">${data.message || '加载失败'}</div>`;
            }
            return;
        }

        // 更新文件信息
        if (infoEl) {
            infoEl.textContent = `${data.filename} (${formatFileSize(data.size)})`;
        }

        if (data.type === 'txt') {
            // 显示 TXT 文件内容
            if (contentEl) {
                const pre = document.createElement('pre');
                pre.className = 'preview-text-content';
                pre.textContent = data.content;
                contentEl.innerHTML = '';
                contentEl.appendChild(pre);
            }
            previewLoaded = true;
        } else {
            // 非文本文件提示
            if (contentEl) {
                contentEl.innerHTML = `
                    <div class="preview-binary">
                        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                            <polyline points="14 2 14 8 20 8"/>
                        </svg>
                        <p>${data.message || '此文件类型需要下载后查看'}</p>
                        <button class="btn btn-primary" onclick="downloadResult()">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                                <polyline points="7 10 12 15 17 10"/>
                                <line x1="12" y1="15" x2="12" y2="3"/>
                            </svg>
                            下载文件
                        </button>
                    </div>
                `;
            }
            previewLoaded = true;
        }
    } catch (error) {
        if (contentEl) {
            contentEl.innerHTML = `<div class="preview-error">加载失败: ${error.message}</div>`;
        }
    }
}

// ==================== 日志 ====================

function addLog(data) {
    const logContainer = document.getElementById('logContainer');
    if (!logContainer) return;
    
    // 移除空状态
    const emptyMsg = logContainer.querySelector('.log-empty');
    if (emptyMsg) emptyMsg.remove();
    
    // 创建日志项
    const logItem = document.createElement('div');
    logItem.className = `log-item log-${data.type}`;
    
    const time = new Date().toLocaleTimeString('zh-CN', { hour12: false });
    logItem.innerHTML = `
        <span class="log-time">${time}</span>
        <span class="log-message">${data.message}</span>
    `;
    
    logContainer.appendChild(logItem);
    
    // 滚动到底部
    logContainer.scrollTop = logContainer.scrollHeight;
}

function clearLogs() {
    const logContainer = document.getElementById('logContainer');
    if (!logContainer) return;
    
    logContainer.innerHTML = '<div class="log-empty">等待日志输出...</div>';
}

// LLM 实时进度
function updateLLMProgress(data) {
    const progressMessage = document.getElementById('progressMessage');
    if (progressMessage) {
        progressMessage.textContent = `LLM 正在生成... 已生成 ${data.char_count} 字符`;
    }
    
    // 添加到日志
    const logContainer = document.getElementById('logContainer');
    if (logContainer) {
        // 移除空状态
        const emptyMsg = logContainer.querySelector('.log-empty');
        if (emptyMsg) emptyMsg.remove();
        
        // 更新或创建 LLM 进度日志
        let progressLog = logContainer.querySelector('.log-llm-progress');
        if (!progressLog) {
            progressLog = document.createElement('div');
            progressLog.className = 'log-item log-llm-progress';
            logContainer.appendChild(progressLog);
        }
        
        const time = new Date().toLocaleTimeString('zh-CN', { hour12: false });
        progressLog.innerHTML = `
            <span class="log-time">${time}</span>
            <span class="log-message">[LLM] ${data.preview}</span>
        `;
        
        // 滚动到底部
        logContainer.scrollTop = logContainer.scrollHeight;
    }
}

// ==================== 系统设置 ====================

async function loadConfig() {
    try {
        const response = await fetch('/api/config');
        const data = await response.json();
        
        if (data.success) {
            const baseUrl = document.getElementById('baseUrl');
            const apiKey = document.getElementById('apiKey');
            const modelName = document.getElementById('modelName');
            
            if (baseUrl) baseUrl.value = data.config.base_url;
            if (apiKey) apiKey.value = '';
            if (modelName) modelName.value = data.config.model_name === '(未设置)' ? '' : data.config.model_name;
        }
    } catch (error) {
        console.error('加载配置失败:', error);
    }
}

async function testConnection() {
    const testBtn = document.getElementById('testBtn');
    const testBtnText = document.getElementById('testBtnText');
    const testSuccess = document.getElementById('testSuccess');
    const testError = document.getElementById('testError');
    
    if (!testBtn) return;
    
    testBtn.disabled = true;
    if (testBtnText) testBtnText.textContent = '测试中...';
    if (testSuccess) testSuccess.style.display = 'none';
    if (testError) testError.style.display = 'none';
    
    try {
        const baseUrl = document.getElementById('baseUrl')?.value || '';
        const apiKey = document.getElementById('apiKey')?.value || '';
        const modelName = document.getElementById('modelName')?.value || 'default';
        
        const response = await fetch('/api/config/test', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                base_url: baseUrl,
                api_key: apiKey,
                model_name: modelName
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            if (testSuccess) {
                testSuccess.style.display = 'flex';
                const msg = document.getElementById('testSuccessMessage');
                if (msg) msg.innerHTML = `模型：${data.model}<br>回复：${data.reply}`;
            }
            showNotification('连接成功', 'success');
        } else {
            if (testError) {
                testError.style.display = 'flex';
                const msg = document.getElementById('testErrorMessage');
                if (msg) msg.textContent = data.message;
            }
            showNotification('连接失败', 'error');
        }
    } catch (error) {
        if (testError) {
            testError.style.display = 'flex';
            const msg = document.getElementById('testErrorMessage');
            if (msg) msg.textContent = error.message;
        }
        showNotification('连接失败: ' + error.message, 'error');
    } finally {
        testBtn.disabled = false;
        if (testBtnText) testBtnText.textContent = '测试连接';
    }
}

async function saveConfig() {
    const baseUrl = document.getElementById('baseUrl')?.value || '';
    const apiKey = document.getElementById('apiKey')?.value || '';
    const modelName = document.getElementById('modelName')?.value || '';
    
    try {
        const response = await fetch('/api/config/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                base_url: baseUrl,
                api_key: apiKey,
                model_name: modelName
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('配置已保存到 src/config.py', 'success');
        } else {
            showNotification('保存失败: ' + data.message, 'error');
        }
    } catch (error) {
        showNotification('保存失败: ' + error.message, 'error');
    }
}

// ==================== 通知 ====================

function showNotification(message, type = 'info') {
    const container = document.getElementById('notificationContainer');
    if (!container) return;

    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;

    container.appendChild(notification);

    // 3秒后自动移除
    setTimeout(() => {
        notification.style.animation = 'slideIn 0.3s ease reverse';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// ==================== 已上传文件管理 ====================

async function loadUploadedFiles() {
    const listContainer = document.getElementById('uploadedFilesCompactList');
    const emptyState = document.getElementById('compactEmpty');
    
    if (!listContainer) return;

    try {
        const response = await fetch('/api/uploaded-files');
        const data = await response.json();

        if (!data.success || !data.files || data.files.length === 0) {
            // 显示空状态
            if (emptyState) emptyState.style.display = 'block';
            // 移除所有文件项
            const fileItems = listContainer.querySelectorAll('.compact-file-item');
            fileItems.forEach(item => item.remove());
            return;
        }

        // 隐藏空状态
        if (emptyState) emptyState.style.display = 'none';

        // 保存文件列表
        uploadedFiles = data.files;

        // 渲染文件列表
        renderUploadedFiles(data.files);

    } catch (error) {
        console.error('加载已上传文件失败:', error);
        showNotification('加载已上传文件失败', 'error');
    }
}

function renderUploadedFiles(files) {
    const listContainer = document.getElementById('uploadedFilesCompactList');
    if (!listContainer) return;

    // 移除旧的文件项
    const oldItems = listContainer.querySelectorAll('.compact-file-item');
    oldItems.forEach(item => item.remove());

    files.forEach(file => {
        const fileItem = document.createElement('div');
        fileItem.className = 'compact-file-item';
        fileItem.dataset.fileId = file.file_id;

        const isSelected = selectedFile && selectedFile.file_id === file.file_id;
        if (isSelected) {
            fileItem.classList.add('selected');
        }

        fileItem.innerHTML = `
            <div class="compact-file-icon ${file.file_ext.replace('.', '')}">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                    <polyline points="14 2 14 8 20 8"/>
                </svg>
            </div>
            <div class="compact-file-info" onclick="selectUploadedFile('${file.file_id}')">
                <div class="compact-file-name" title="${file.original_filename}">${file.original_filename}</div>
                <div class="compact-file-meta">${formatFileSize(file.file_size)} · ${file.file_ext.toUpperCase().replace('.', '')}</div>
            </div>
            <div class="compact-file-actions">
                <button class="btn btn-sm ${isSelected ? 'btn-primary' : 'btn-outline'}" onclick="event.stopPropagation(); selectUploadedFile('${file.file_id}')">
                    ${isSelected ? '已选' : '选择'}
                </button>
                <button class="btn btn-sm btn-danger btn-icon" onclick="event.stopPropagation(); deleteUploadedFile('${file.file_id}')" title="删除">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="3 6 5 6 21 6"/>
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                    </svg>
                </button>
            </div>
        `;

        listContainer.appendChild(fileItem);
    });
}

function selectUploadedFile(fileId) {
    const file = uploadedFiles.find(f => f.file_id === fileId);
    if (!file) {
        showNotification('文件不存在', 'error');
        return;
    }

    // 更新全局状态
    selectedFile = {
        file_id: file.file_id,
        original_filename: file.original_filename,
        file_size: file.file_size
    };

    // 更新 UI - 文件信息展示
    const fileInfo = document.getElementById('fileInfo');
    const fileName = document.getElementById('fileName');
    const fileSize = document.getElementById('fileSize');
    const processBtn = document.getElementById('processBtn');

    if (fileInfo && fileName && fileSize) {
        fileInfo.style.display = 'flex';
        fileName.textContent = file.original_filename;
        fileSize.textContent = formatFileSize(file.file_size);
    }

    // 启用处理按钮
    if (processBtn) {
        processBtn.disabled = false;
    }

    // 重新渲染文件列表（更新选中状态）
    renderUploadedFiles(uploadedFiles);

    showNotification(`已选择文件: ${file.original_filename}`, 'success');

    // 滚动到顶部，让用户看到文件信息
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

async function deleteUploadedFile(fileId) {
    const file = uploadedFiles.find(f => f.file_id === fileId);
    if (!file) {
        showNotification('文件不存在', 'error');
        return;
    }

    // 确认删除
    if (!confirm(`确定要删除文件 "${file.original_filename}" 吗？\n\n注意：相关的未完成任务记录也会被删除。`)) {
        return;
    }

    try {
        const response = await fetch(`/api/uploaded-files/${fileId}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (data.success) {
            showNotification('文件已删除', 'success');
            
            // 如果删除的是当前选中的文件，清空选择
            if (selectedFile && selectedFile.file_id === fileId) {
                selectedFile = null;
                const fileInfo = document.getElementById('fileInfo');
                const processBtn = document.getElementById('processBtn');
                if (fileInfo) fileInfo.style.display = 'none';
                if (processBtn) processBtn.disabled = true;
            }

            // 重新加载文件列表
            loadUploadedFiles();
        } else {
            showNotification('删除失败: ' + data.message, 'error');
        }
    } catch (error) {
        console.error('删除文件失败:', error);
        showNotification('删除失败: ' + error.message, 'error');
    }
}
