/**
 * 提示词配置页面 JavaScript
 * 支持 3 类别 × 多版本管理
 */

// 全局状态
let allPrompts = {};
let currentCategory = null;
let currentVersion = null;

// 类别图标
const categoryIcons = {
    full: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>`,
    chapter: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>`,
    paragraph: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>`,
};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    loadPrompts();
});

// 加载所有提示词
async function loadPrompts() {
    try {
        const response = await fetch('/api/prompts');
        const data = await response.json();
        
        if (data.success) {
            allPrompts = data.prompts;
            renderCategoryList();
        } else {
            showNotification('加载失败: ' + data.message, 'error');
        }
    } catch (error) {
        showNotification('加载失败: ' + error.message, 'error');
    }
}

// 渲染类别列表
function renderCategoryList() {
    const container = document.getElementById('categoryList');
    container.innerHTML = '';
    
    for (const [catId, catData] of Object.entries(allPrompts)) {
        const div = document.createElement('div');
        div.className = 'category-item';
        div.dataset.category = catId;
        div.innerHTML = `
            ${categoryIcons[catId] || ''}
            <span>${catData.name}</span>
        `;
        div.onclick = () => selectCategory(catId);
        container.appendChild(div);
    }
}

// 选择类别
function selectCategory(catId) {
    currentCategory = catId;
    currentVersion = null;
    
    // 更新选中状态
    document.querySelectorAll('.category-item').forEach(el => {
        el.classList.toggle('active', el.dataset.category === catId);
    });
    
    // 更新类别名称
    document.getElementById('currentCategoryName').textContent = allPrompts[catId].name;
    document.getElementById('addVersionBtn').style.display = 'inline-flex';
    
    // 渲染版本列表
    renderVersionList();
    
    // 清空编辑器
    clearEditor();
}

// 渲染版本列表
function renderVersionList() {
    const container = document.getElementById('versionList');
    container.innerHTML = '';
    
    if (!currentCategory || !allPrompts[currentCategory]) {
        container.innerHTML = '<div class="empty-state"><p>请先选择左侧的类别</p></div>';
        return;
    }
    
    const versions = allPrompts[currentCategory].versions;
    
    if (versions.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>暂无版本</p></div>';
        return;
    }
    
    versions.forEach(v => {
        const div = document.createElement('div');
        div.className = 'version-item';
        div.dataset.version = v.id;
        div.innerHTML = `
            <div class="version-item-name">${v.name}</div>
            <div style="display: flex; align-items: center;">
                <span class="version-item-id">${v.id}</span>
                ${v.is_default ? '<span class="badge badge-success" style="margin-left: 8px;">默认</span>' : ''}
            </div>
        `;
        div.onclick = () => selectVersion(v.id);
        container.appendChild(div);
    });
}

// 选择版本
function selectVersion(versionId) {
    currentVersion = versionId;

    // 更新选中状态
    document.querySelectorAll('.version-item').forEach(el => {
        el.classList.toggle('active', el.dataset.version === versionId);
    });

    // 加载版本数据到编辑器
    const version = allPrompts[currentCategory].versions.find(v => v.id === versionId);
    if (version) {
        document.getElementById('versionName').value = version.name;
        document.getElementById('versionDescription').textContent = version.data.description || '';
        document.getElementById('roleEditor').value = version.data.role || '';
        document.getElementById('promptEditor').value = version.data.prompt || '';
    }

    // 显示/隐藏按钮
    const isDefault = version && version.is_default;
    document.getElementById('resetBtn').style.display = isDefault ? 'none' : 'inline-flex';
    document.getElementById('deleteBtn').style.display = isDefault ? 'none' : 'inline-flex';
    
    // 禁用默认版本的保存按钮
    const saveBtn = document.querySelector('.header .btn-primary');
    if (saveBtn) {
        saveBtn.disabled = isDefault;
        if (isDefault) {
            saveBtn.title = '默认版本不可修改，请创建新版本';
            saveBtn.style.opacity = '0.5';
            saveBtn.style.cursor = 'not-allowed';
        } else {
            saveBtn.title = '';
            saveBtn.style.opacity = '';
            saveBtn.style.cursor = '';
        }
    }
}

// 清空编辑器
function clearEditor() {
    document.getElementById('versionName').value = '';
    document.getElementById('versionDescription').textContent = '';
    document.getElementById('roleEditor').value = '';
    document.getElementById('promptEditor').value = '';
    document.getElementById('resetBtn').style.display = 'none';
    document.getElementById('deleteBtn').style.display = 'none';
    document.querySelectorAll('.version-item').forEach(el => el.classList.remove('active'));
}

// 保存当前版本
async function saveCurrentVersion() {
    if (!currentCategory || !currentVersion) {
        showNotification('请先选择一个版本', 'error');
        return;
    }
    
    // 检查是否是默认版本
    const version = allPrompts[currentCategory].versions.find(v => v.id === currentVersion);
    if (version && version.is_default) {
        showNotification('默认版本不可修改，请创建新版本后保存', 'error');
        return;
    }

    const data = {
        category: currentCategory,
        version: currentVersion,
        data: {
            name: document.getElementById('versionName').value,
            description: document.getElementById('versionDescription').textContent,
            role: document.getElementById('roleEditor').value,
            prompt: document.getElementById('promptEditor').value,
        }
    };

    try {
        const response = await fetch('/api/prompts/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            showNotification('版本已保存', 'success');
            // 重新加载
            await loadPrompts();
            // 恢复选中状态
            if (currentCategory) {
                selectCategory(currentCategory);
                if (currentVersion) {
                    selectVersion(currentVersion);
                }
            }
        } else {
            showNotification('保存失败: ' + result.message, 'error');
        }
    } catch (error) {
        showNotification('保存失败: ' + error.message, 'error');
    }
}

// 删除当前版本
async function deleteCurrentVersion() {
    if (!currentCategory || !currentVersion) return;
    
    if (!confirm(`确定要删除版本"${currentVersion}"吗？此操作不可恢复。`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/prompts/delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                category: currentCategory,
                version: currentVersion
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('版本已删除', 'success');
            await loadPrompts();
            selectCategory(currentCategory);
        } else {
            showNotification('删除失败: ' + result.message, 'error');
        }
    } catch (error) {
        showNotification('删除失败: ' + error.message, 'error');
    }
}

// 恢复默认
async function resetToDefault() {
    if (!currentCategory || !currentVersion) return;
    
    if (!confirm('确定要恢复默认版本吗？当前修改将丢失。')) {
        return;
    }
    
    try {
        const response = await fetch('/api/prompts');
        const data = await response.json();
        
        if (data.success) {
            allPrompts = data.prompts;
            const defaultVersion = allPrompts[currentCategory].versions.find(v => v.is_default);
            if (defaultVersion) {
                selectVersion(defaultVersion.id);
                showNotification('已恢复默认版本（未保存）', 'info');
            }
        }
    } catch (error) {
        showNotification('恢复失败: ' + error.message, 'error');
    }
}

// 显示新增版本对话框
function showAddVersionDialog() {
    document.getElementById('addVersionModal').style.display = 'flex';
    document.getElementById('newVersionId').value = '';
    document.getElementById('newVersionName').value = '';
}

// 关闭新增版本对话框
function closeAddVersionDialog() {
    document.getElementById('addVersionModal').style.display = 'none';
}

// 新增版本
async function addNewVersion() {
    const versionId = document.getElementById('newVersionId').value.trim();
    const versionName = document.getElementById('newVersionName').value.trim();
    
    if (!versionId) {
        showNotification('请输入版本 ID', 'error');
        return;
    }
    
    if (!/^[a-zA-Z0-9_]+$/.test(versionId)) {
        showNotification('版本 ID 只能使用英文字母、数字和下划线', 'error');
        return;
    }
    
    // 检查是否已存在
    if (allPrompts[currentCategory].versions.some(v => v.id === versionId)) {
        showNotification('版本 ID 已存在', 'error');
        return;
    }
    
    // 创建新版本（从默认版本复制）
    const defaultVersion = allPrompts[currentCategory].versions.find(v => v.is_default);
    const newData = defaultVersion ? JSON.parse(JSON.stringify(defaultVersion.data)) : {
        name: versionName || versionId,
        description: '',
        role: '',
        prompt: '',
    };
    newData.name = versionName || versionId;
    
    const data = {
        category: currentCategory,
        version: versionId,
        data: newData,
    };
    
    try {
        const response = await fetch('/api/prompts/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('版本已创建', 'success');
            closeAddVersionDialog();
            await loadPrompts();
            selectCategory(currentCategory);
            selectVersion(versionId);
        } else {
            showNotification('创建失败: ' + result.message, 'error');
        }
    } catch (error) {
        showNotification('创建失败: ' + error.message, 'error');
    }
}
