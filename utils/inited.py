import json
import os
from core.runtime_dir import get_runtime_dir

def maren_dir_path():
    return os.path.join(get_runtime_dir(), ".maren")

def maren_json_path():
    return os.path.join(maren_dir_path(), "maren.json")

# 旧的 maren.json 路径（用于迁移检测）
def old_maren_json_path():
    return os.path.join(get_runtime_dir(), "maren.json")

def skill_json_path():
    return os.path.join(maren_dir_path(), "skill.json")

def role_skills_json_path():
    return os.path.join(maren_dir_path(), "role_skills.json")

def project_json_path():
    return os.path.join(maren_dir_path(), "project.json")

def agents_md_path():
    return os.path.join(maren_dir_path(), "AGENTS.md")

def is_inited():
    # 迁移逻辑：如果旧的 maren.json 存在但新的不存在，则移动它
    if os.path.exists(old_maren_json_path()) and not os.path.exists(maren_json_path()):
        try:
            # 确保目录存在
            os.makedirs(maren_dir_path(), exist_ok=True)
            import shutil
            shutil.move(old_maren_json_path(), maren_json_path())
            print(f"Migrated maren.json to {maren_json_path()}")
        except PermissionError as e:
            print(f"[ERROR] 迁移 maren.json 权限不足: {e}")
        except OSError as e:
            print(f"[ERROR] 迁移 maren.json 文件系统错误: {type(e).__name__}: {e}")
        except Exception as e:
            print(f"[ERROR] 迁移 maren.json 失败: {type(e).__name__}: {e}")

    # 必须同时存在 maren.json 文件和 .maren 目录才视为已初始化
    if not os.path.exists(maren_json_path()):
        return False
    if not os.path.exists(maren_dir_path()) or not os.path.isdir(maren_dir_path()):
        return False
    # 确保配置文件存在
    if not os.path.exists(skill_json_path()):
        _create_default_skill_json()
    if not os.path.exists(role_skills_json_path()):
        _create_default_role_skills_json()
    if not os.path.exists(project_json_path()):
        _create_default_project_json()
    return True

def _create_default_agents_md():
    content = """# Maren Code Agents Registry

这里记录了 Maren Code 系统中已注册的智能体 (Agents) 及其职责。

## 核心智能体

| 角色 (Role) | 职责 (Responsibility) | 模型配置 (Model) |
| :--- | :--- | :--- |
| **Leader** | 全局规划、任务拆解、决策仲裁 | (见 maren.json) |
| **Coder** | 代码编写、重构、优化、Bug修复 | (见 maren.json) |
| **Tester** | 编写测试用例、执行测试、质量保证 | (见 maren.json) |
| **Chatter** | 用户交互、知识问答、信息检索 | (见 maren.json) |
| **Icon Designer** | 生成图标、UI 元素设计 | (见 maren.json) |

## 扩展智能体
*(在此处添加自定义智能体)*
"""
    try:
        with open(agents_md_path(), "w", encoding="utf-8") as f:
            f.write(content)
    except PermissionError as e:
        print(f"[ERROR] 创建 AGENTS.md 权限不足: {e}")
    except Exception as e:
        print(f"[ERROR] 创建 AGENTS.md 失败: {type(e).__name__}: {e}")

def _create_default_project_json():
    """创建默认 project.json"""
    from datetime import datetime
    project = {
        "name": os.path.basename(get_runtime_dir()),
        "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "description": "",
        "version": "0.1.0"
    }
    try:
        os.makedirs(maren_dir_path(), exist_ok=True)
        with open(project_json_path(), "w", encoding="utf-8") as f:
            json.dump(project, f, ensure_ascii=False, indent=4)
    except PermissionError as e:
        print(f"[ERROR] 创建 project.json 权限不足: {e}")
    except Exception as e:
        print(f"[ERROR] 创建 project.json 失败: {type(e).__name__}: {e}")

def _create_default_role_skills_json():
    # 默认角色技能映射
    default_role_skills = {
        "Chatter": ["read_url", "search_web", "get_time", "get_timestamp", "search_github", "read_file", "list_dir", "add_memory"],
        "Coder": ["read_file", "list_dir", "write_file", "edit_file", "edit_file_lines", "rename_file", "create_directory", "create_file", "run_command", "search_web", "add_memory"],
        "Designer": ["read_file", "list_dir", "write_file", "edit_file", "create_file", "create_directory", "search_web", "read_url", "add_memory"],
        "Leader": ["read_file", "list_dir"],
        "Tester": ["read_file", "list_dir", "run_command"]
    }
    try:
        os.makedirs(maren_dir_path(), exist_ok=True)
        with open(role_skills_json_path(), "w", encoding="utf-8") as f:
            json.dump(default_role_skills, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error creating role_skills.json: {e}")

def _create_default_skill_json():
    # 默认技能配置
    default_skills = [
        {
            "name": "read_url",
            "description": "获取并阅读网页内容",
            "roles": ["Chatter"],
            "module": "core.skill.get_website",
            "function": "get_website",
            "usage": {
                "action": "read_url",
                "url": "https://example.com",
                "msg": "正在获取网页..."
            }
        },
        {
            "name": "search_web",
            "description": "在互联网上搜索信息 (Bing/Baidu)",
            "roles": ["Chatter"],
            "module": "core.skill.get_web_info",
            "function": "search_web",
            "usage": {
                "action": "search_web",
                "query": "关键词",
                "engine": "bing",
                "msg": "正在搜索..."
            }
        },
        {
            "name": "get_time",
            "description": "获取当前系统时间",
            "roles": ["Chatter"],
            "module": "core.skill.get_time",
            "function": "get_current_time",
            "usage": {
                "action": "get_time",
                "msg": "正在获取时间..."
            }
        },
        {
            "name": "get_timestamp",
            "description": "获取当前 Unix 时间戳",
            "roles": ["Chatter"],
            "module": "core.skill.get_time",
            "function": "get_timestamp",
            "usage": {
                "action": "get_timestamp",
                "msg": "正在获取时间戳..."
            }
        },
        {
            "name": "search_github",
            "description": "搜索 GitHub 项目",
            "roles": ["Chatter"],
            "module": "core.skill.get_github",
            "function": "search_github",
            "usage": {
                "action": "search_github",
                "query": "关键词,支持github高级搜索",
                "limit": 5,
                "msg": "正在搜索 GitHub..."
            }
        },
        {
            "name": "read_file",
            "description": "读取本地文件内容",
            "roles": ["Chatter", "Coder"],
            "module": "core.skill.read_file",
            "function": "read_file",
            "usage": {
                "action": "read_file",
                "path": "文件路径",
                "msg": "正在读取文件..."
            }
        },
        {
            "name": "list_dir",
            "description": "列出目录内容",
            "roles": ["Chatter", "Coder"],
            "module": "core.skill.read_file",
            "function": "list_dir",
            "usage": {
                "action": "list_dir",
                "path": "目录路径",
                "msg": "正在列出目录..."
            }
        },
        {
            "name": "write_file",
            "description": "写入内容到文件（覆盖写入，自动创建父目录）",
            "roles": ["Coder"],
            "module": "core.skill.write_file",
            "function": "write_file",
            "usage": {
                "action": "write_file",
                "path": "文件路径",
                "content": "文件内容",
                "msg": "正在写入文件..."
            }
        },
        {
            "name": "edit_file",
            "description": "基于锚点的增量编辑文件（找到anchor文本并替换为new_content）",
            "roles": ["Coder"],
            "module": "core.skill.edit_file",
            "function": "edit_file",
            "usage": {
                "action": "edit_file",
                "path": "文件路径",
                "anchor": "要查找的原始文本",
                "new_content": "替换后的新内容",
                "msg": "正在编辑文件..."
            }
        },
        {
            "name": "edit_file_lines",
            "description": "按行号范围替换文件内容",
            "roles": ["Coder"],
            "module": "core.skill.edit_file",
            "function": "edit_file_lines",
            "usage": {
                "action": "edit_file_lines",
                "path": "文件路径",
                "start_line": 1,
                "end_line": 5,
                "new_content": "替换后的内容",
                "msg": "正在编辑文件..."
            }
        },
        {
            "name": "rename_file",
            "description": "重命名或移动文件/目录",
            "roles": ["Coder"],
            "module": "core.skill.file_ops",
            "function": "rename_file",
            "usage": {
                "action": "rename_file",
                "old_path": "原路径",
                "new_path": "新路径",
                "msg": "正在重命名..."
            }
        },
        {
            "name": "create_directory",
            "description": "创建目录（支持多级）",
            "roles": ["Coder"],
            "module": "core.skill.file_ops",
            "function": "create_directory",
            "usage": {
                "action": "create_directory",
                "path": "目录路径",
                "msg": "正在创建目录..."
            }
        },
        {
            "name": "create_file",
            "description": "创建新文件",
            "roles": ["Coder"],
            "module": "core.skill.file_ops",
            "function": "create_file",
            "usage": {
                "action": "create_file",
                "path": "文件路径",
                "content": "初始内容（可选）",
                "msg": "正在创建文件..."
            }
        },
        {
            "name": "run_command",
            "description": "执行终端命令（带安全检查和超时）",
            "roles": ["Coder"],
            "module": "core.skill.terminal",
            "function": "run_command",
            "usage": {
                "action": "run_command",
                "command": "命令内容",
                "cwd": "工作目录（可选）",
                "timeout": 30,
                "msg": "正在执行命令..."
            }
        },
        {
            "name": "add_memory",
            "description": "记住用户的长期规定或偏好（当用户说'记住'、'添加记忆'、'以后都要'等时调用）",
            "roles": ["Chatter", "Coder"],
            "module": "core.skill.memory",
            "function": "add_memory",
            "usage": {
                "action": "add_memory",
                "content": "要记住的内容",
                "msg": "正在记录..."
            }
        }
    ]
    
    try:
        os.makedirs(maren_dir_path(), exist_ok=True)
        with open(skill_json_path(), "w", encoding="utf-8") as f:
            json.dump(default_skills, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error creating skill.json: {e}")

def init_maren(base_url, language, models, keys, role_urls=None):
    """
    初始化 Maren 配置
    :param base_url: 默认 API base URL
    :param language: 语言
    :param models: 角色模型映射
    :param keys: 角色 API Key 映射
    :param role_urls: 角色独立 base_url 映射（可选）
    """
    # 如果没有角色独立 URL，全部使用默认
    if not role_urls:
        role_urls = {}

    maren = {
        "lang": language,
        "model": {
            "api_key": keys,
            "base_url": base_url,
            "role_base_urls": role_urls,
            "coder": {
                "model_name": models.get("coder", ""),
                "max_tokens": 8192,
                "temperature": 0.0,
                "top_p": 1.0
            },
            "leader": {
                "model_name": models.get("leader", ""),
                "max_tokens": 4096,
                "temperature": 0.3,
                "top_p": 0.95
            },
            "tester": {
                "model_name": models.get("tester", ""),
                "max_tokens": 4096,
                "temperature": 0.1,
                "top_p": 1.0
            },
            "chatter": {
                "model_name": models.get("chatter", ""),
                "max_tokens": 4096,
                "temperature": 0.7,
                "top_p": 0.95
            },
            "icon_designer": {
                "model_name": models.get("icon_designer", ""),
                "max_tokens": 2048,
                "temperature": 1.0,
                "top_p": 1.0
            }
        }
    }

    # 创建 .maren 目录
    os.makedirs(maren_dir_path(), exist_ok=True)
    
    # 创建默认 skill.json
    _create_default_skill_json()
    # 创建默认 role_skills.json
    _create_default_role_skills_json()
    # 创建默认 project.json
    _create_default_project_json()

    # maren.json 写入 .maren 目录
    with open(maren_json_path(), "w", encoding="utf-8") as f:
        json.dump(maren, f, ensure_ascii=False, indent=4)
