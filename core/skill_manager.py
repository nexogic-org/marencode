
import os
import json
import importlib
import inspect
import logging

def load_skills():
    """动态加载技能配置"""
    try:
        # 始终以当前工作目录（用户执行命令的目录）为基准
        skill_path = os.path.join(os.getcwd(), ".maren", "skill.json")
        if os.path.exists(skill_path):
            with open(skill_path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logging.error(f"读取 skill.json 失败: {e}")
    return []

def load_role_skills():
    """加载角色技能映射"""
    try:
        role_skills_path = os.path.join(os.getcwd(), ".maren", "role_skills.json")
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


def execute_skill(skill_name: str, **kwargs):
    """
    动态执行技能
    :param skill_name: 技能名称 (对应 skill.json 中的 name)
    :param kwargs: 传递给技能函数的参数
    :return: 技能执行结果
    """
    skills = load_skills()
    skill_config = next((s for s in skills if s['name'] == skill_name), None)

    # 别名回退：AI 可能输出变体名称
    if not skill_config and skill_name in _SKILL_ALIASES:
        resolved = _SKILL_ALIASES[skill_name]
        logging.info(f"技能别名解析: '{skill_name}' -> '{resolved}'")
        skill_config = next((s for s in skills if s['name'] == resolved), None)

    if not skill_config:
        available = [s['name'] for s in skills]
        raise ValueError(f"Skill '{skill_name}' not found. Available: {', '.join(available)}")
        
    module_name = skill_config.get("module")
    function_name = skill_config.get("function")
    
    if not module_name or not function_name:
        raise ValueError(f"Skill '{skill_name}' does not have module/function defined.")
        
    try:
        module = importlib.import_module(module_name)
        func = getattr(module, function_name)
        
        # 检查函数参数，只传递匹配的参数
        sig = inspect.signature(func)
        valid_kwargs = {k: v for k, v in kwargs.items() if k in sig.parameters}
        
        return func(**valid_kwargs)
    except (ImportError, AttributeError):
        raise
    except Exception as e:
        import traceback
        error_msg = f"执行工具 '{skill_name}' 失败: {e}\n传入参数: {kwargs}\n堆栈:\n{traceback.format_exc()}"
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
