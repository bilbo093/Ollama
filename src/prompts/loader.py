"""
提示词加载器
支持 3 个类别，每个类别支持多版本管理
"""
from pathlib import Path


# 类别配置
CATEGORIES = {
    'full': '全文模式',
    'chapter': '章节模式',
    'paragraph': '段落模式',
}

# 默认版本（不可删除）
DEFAULT_VERSIONS = {
    'full': 'default',
    'chapter': 'default',
    'paragraph': 'default',
}


def _get_category_dir(category: str) -> Path:
    """获取类别目录"""
    if category not in CATEGORIES:
        raise ValueError(f"无效的类别: {category}，可选: {list(CATEGORIES.keys())}")
    return Path(__file__).parent / category


def _parse_md_file(file_path: Path) -> dict:
    """解析 Markdown 文件"""
    if not file_path.exists():
        return None
    
    content = file_path.read_text(encoding='utf-8')
    
    result = {
        'name': '',
        'description': '',
        'role': '',
        'prompt': '',
    }
    
    current_section = None
    
    for line in content.split('\n'):
        if line.startswith('# ') and current_section is None:
            result['name'] = line[2:].strip()
        elif line.startswith('## 描述'):
            current_section = 'description'
        elif line.startswith('## Role'):
            current_section = 'role'
        elif line.startswith('## Prompt'):
            current_section = 'prompt'
        elif current_section in result and not line.startswith('#'):
            result[current_section] += line + '\n'
    
    for key in result:
        result[key] = result[key].strip()
    
    return result


def _save_md_file(file_path: Path, data: dict):
    """保存为 Markdown 文件"""
    content = f"""# {data.get('name', '')}

## 描述
{data.get('description', '')}

## Role
{data.get('role', '')}

## Prompt
{data.get('prompt', '')}
"""
    file_path.write_text(content, encoding='utf-8')


def get_categories() -> list:
    """
    获取所有类别
    
    Returns:
        [{'id': 'full', 'name': '全文模式'}, ...]
    """
    return [{'id': k, 'name': v} for k, v in CATEGORIES.items()]


def get_versions(category: str) -> list:
    """
    获取某类别的所有版本
    
    Args:
        category: 类别 ID
    
    Returns:
        [{'id': 'default', 'name': '默认版本', 'is_default': True}, ...]
    """
    cat_dir = _get_category_dir(category)
    if not cat_dir.exists():
        return []
    
    versions = []
    default_version = DEFAULT_VERSIONS.get(category, 'default')
    
    for md_file in sorted(cat_dir.glob('*.md')):
        version_id = md_file.stem
        data = _parse_md_file(md_file)
        
        versions.append({
            'id': version_id,
            'name': data['name'] if data else version_id,
            'is_default': version_id == default_version,
        })
    
    return versions


def get_prompt(category: str, version: str) -> dict:
    """
    获取指定类别和版本的提示词

    Args:
        category: 类别 ID
        version: 版本 ID

    Returns:
        {'name': ..., 'description': ..., 'role': ..., 'prompt': ...}
    """
    cat_dir = _get_category_dir(category)
    file_path = cat_dir / f"{version}.md"

    data = _parse_md_file(file_path)
    if not data:
        raise FileNotFoundError(f"提示词文件不存在: {file_path}")

    return data


def get_available_versions(category: str) -> list[str]:
    """
    获取类别下所有可用的版本
    
    Args:
        category: 类别 ID
    
    Returns:
        版本 ID 列表
    """
    cat_dir = _get_category_dir(category)
    if not cat_dir.exists():
        return []
    
    versions = []
    for md_file in cat_dir.glob("*.md"):
        if md_file.name != 'README.md':  # 排除可能的说明文件
            versions.append(md_file.stem)
    
    return sorted(versions)


def save_version(category: str, version: str, data: dict) -> str:
    """
    保存版本

    Args:
        category: 类别 ID
        version: 版本 ID
        data: {'name': ..., 'description': ..., 'role': ..., 'prompt': ...}

    Returns:
        'success' 或错误信息
    """
    # 禁止修改默认版本
    default_version = DEFAULT_VERSIONS.get(category, 'default')
    if version == default_version:
        return 'error: 默认版本不可修改'

    cat_dir = _get_category_dir(category)
    cat_dir.mkdir(parents=True, exist_ok=True)

    file_path = cat_dir / f"{version}.md"

    _save_md_file(file_path, data)

    return 'success'


def delete_version(category: str, version: str) -> str:
    """
    删除版本（默认版本不可删除）
    
    Args:
        category: 类别 ID
        version: 版本 ID
    
    Returns:
        'success' 或错误信息
    """
    default_version = DEFAULT_VERSIONS.get(category, 'default')
    if version == default_version:
        return 'error: 默认版本不可删除'
    
    cat_dir = _get_category_dir(category)
    file_path = cat_dir / f"{version}.md"
    
    if not file_path.exists():
        return f'error: 版本不存在: {version}'
    
    file_path.unlink()
    return 'success'


def get_all_prompts() -> dict:
    """
    获取所有类别的所有版本
    
    Returns:
        {
            'full': {
                'name': '全文模式',
                'versions': [
                    {'id': 'default', 'name': '...', 'data': {...}},
                    ...
                ]
            },
            ...
        }
    """
    result = {}
    
    for cat_id, cat_name in CATEGORIES.items():
        versions = []
        for v in get_versions(cat_id):
            try:
                data = get_prompt(cat_id, v['id'])
                versions.append({
                    'id': v['id'],
                    'name': v['name'],
                    'is_default': v['is_default'],
                    'data': data,
                })
            except FileNotFoundError:
                pass
        
        result[cat_id] = {
            'name': cat_name,
            'versions': versions,
        }
    
    return result
