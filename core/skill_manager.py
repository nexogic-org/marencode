
import os
import json
import importlib
import inspect
import logging
from core.runtime_dir import get_runtime_dir

def load_skills():
    """动态加载技能配置"""
    try:
        skill_path = os.path.join(get_runtime_dir(), ".maren", "skill.json")
        if os.path.exists(skill_path):
            with open(skill_path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logging.error(f"读取 skill.json 失败: {e}")
    return []

def load_role_skills():
    """加载角色技能映射"""
    try:
        role_skills_path = os.path.join(get_runtime_dir(), ".maren", "role_skills.json")
        if os.path.exists(role_skills_path):
            with open(role_skills_path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logging.error(f"读取 role_skills.json 失败: {e}")
    return {}


# AI 常见的技能名称变体 → 正确名称映射
_SKILL_ALIASES = {
    "run_shell": "run_command",
    "shell": "run_command",
    "exec": "run_command",
    "execute": "run_command",
    "terminal": "run_command",
    "read": "read_file",
    "write": "write_file",
    "edit": "edit_file",
    "mkdir": "create_directory",
    "create_dir": "create_directory",
    "rename": "rename_file",
    "move_file": "rename_file",
    "list_directory": "list_dir",
    "ls": "list_dir",
    "search": "search_web",
    "web_search": "search_web",
    "fetch_url": "read_url",
    "get_url": "read_url",
    "get_web": "read_url",
    "github": "search_github",
    "time": "get_time",
    "timestamp": "get_timestamp",
    "create": "create_file",
}

# 硬编码回退表：当 skill.json 缺失或 module 字段错误时，直接用已知的正确 module/function
_SKILL_FALLBACK = {
    "run_command":      ("core.skill.terminal",     "run_command"),
    "read_file":        ("core.skill.read_file",    "read_file"),
    "list_dir":         ("core.skill.read_file",    "list_dir"),
    "write_file":       ("core.skill.write_file",   "write_file"),
    "edit_file":        ("core.skill.edit_file",    "edit_file"),
    "edit_file_lines":  ("core.skill.edit_file",    "edit_file_lines"),
    "rename_file":      ("core.skill.file_ops",     "rename_file"),
    "create_directory": ("core.skill.file_ops",     "create_directory"),
    "create_file":      ("core.skill.file_ops",     "create_file"),
    "read_url":         ("core.skill.get_website",  "get_website"),
    "search_web":       ("core.skill.get_web_info", "search_web"),
    "search_github":    ("core.skill.get_github",   "search_github"),
    "get_time":         ("core.skill.get_time",     "get_current_time"),
    "get_timestamp":    ("core.skill.get_time",     "get_timestamp"),
    "add_memory":       ("core.skill.memory",       "add_memory"),
}


def _resolve_skill(skill_name: str):
    """
    解析技能名称 → (resolved_name, module_name, function_name)
    优先 skill.json，再别名，最后硬编码回退表
    """
    skills = load_skills()

    # 第一步：直接匹配 skill.json
    cfg = next((s for s in skills if s['name'] == skill_name), None)

    # 第二步：别名 → 再查 skill.json
    resolved = skill_name
    if not cfg and skill_name in _SKILL_ALIASES:
        resolved = _SKILL_ALIASES[skill_name]
        cfg = next((s for s in skills if s['name'] == resolved), None)

    if cfg:
        mod = cfg.get("module")
        func = cfg.get("function")
        if mod and func:
            return resolved, mod, func

    # 第三步：硬编码回退表（skill.json 缺失或 module 字段错误时兜底）
    fallback_key = resolved if resolved in _SKILL_FALLBACK else skill_name
    if fallback_key in _SKILL_FALLBACK:
        mod, func = _SKILL_FALLBACK[fallback_key]
        logging.info(f"技能回退: '{skill_name}' -> {mod}.{func}")
        return fallback_key, mod, func

    available = [s['name'] for s in skills]
    raise ValueError(
        f"技能 '{skill_name}' 未找到。"
        f"可用: {', '.join(available) if available else '(空)'}"
    )


def execute_skill(skill_name: str, **kwargs):
    """
    动态执行技能
    :param skill_name: 技能名称 (对应 skill.json 中的 name)
    :param kwargs: 传递给技能函数的参数
    :return: 技能执行结果
    """
    resolved_name, module_name, function_name = _resolve_skill(skill_name)

    try:
        module = importlib.import_module(module_name)
        func = getattr(module, function_name)

        sig = inspect.signature(func)
        valid_kwargs = {
            k: v for k, v in kwargs.items()
            if k in sig.parameters
        }
        return func(**valid_kwargs)
    except ImportError as e:
        raise RuntimeError(
            f"技能 '{resolved_name}' 模块加载失败: {module_name}\n"
            f"详情: {e}"
        )
    except AttributeError as e:
        raise RuntimeError(
            f"技能 '{resolved_name}' 函数不存在: "
            f"{module_name}.{function_name}\n详情: {e}"
        )
    except Exception as e:
        import traceback
        error_msg = (
            f"执行工具 '{resolved_name}' 失败: {e}\n"
            f"传入参数: {kwargs}\n"
            f"堆栈:\n{traceback.format_exc()}"
        )
        logging.error(error_msg)
        raise RuntimeError(error_msg)

def build_skill_prompt(role="Chatter"):
    """根据角色构建技能提示词"""
    skills = load_skills()
    role_skills_map = load_role_skills()
    
    if not skills:
        return ""
    
    # 获取当前角色允许使用的技能名称列表
    allowed_skills = role_skills_map.get(role, [])
    
    prompt = ["\n## 动态技能库"]
    prompt.append(f"你已挂载以下扩展技能（适用于 {role}）：")
    
    count = 1
    has_skills = False
    
    for skill in skills:
        # 检查技能是否在角色的允许列表中
        # 或者为了兼容旧逻辑，如果 skill.json 中直接定义了 roles 字段且包含当前角色，也视为允许
        if skill['name'] in allowed_skills or role in skill.get("roles", []):
            desc = skill.get("description", "")
            usage = json.dumps(skill.get("usage", {}), ensure_ascii=False, indent=4)
            # 格式化 JSON 块
            usage_block = f"```tool_call\n{usage}\n```"
            prompt.append(f"{count}. **{skill['name']}**: {desc}\n   格式：\n{usage_block}")
            count += 1
            has_skills = True
            
    if not has_skills:
        return ""
            
    prompt.append("\n输出工具指令后，系统会自动调用并注入结果。\n注意：不要捏造搜索结果。")
    return "\n".join(prompt)
