"""
core/skill/memory.py — 记忆技能
将用户的长期规定/偏好写入 .maren/AGENTS.md
AI 在后续请求时会自动读取这些记忆
"""
import os
from datetime import datetime
from core.runtime_dir import get_runtime_dir


def _agents_md_path() -> str:
    return os.path.join(get_runtime_dir(), ".maren", "AGENTS.md")


def add_memory(content: str) -> str:
    """
    添加一条记忆到 AGENTS.md
    :param content: 要记住的内容
    :return: 操作结果
    """
    if not content or not content.strip():
        return "[ERROR] 记忆内容不能为空。"

    path = _agents_md_path()
    parent = os.path.dirname(path)
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)

    # 如果文件不存在，先创建默认头部
    if not os.path.exists(path):
        _create_default(path)

    # 追加记忆条目
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"\n- [{timestamp}] {content.strip()}\n"

    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(entry)
        return f"[OK] 已记住: {content.strip()}"
    except Exception as e:
        return f"[ERROR] 写入记忆失败: {type(e).__name__}: {e}"


def read_memory() -> str:
    """
    读取 AGENTS.md 中的所有记忆
    :return: 记忆内容
    """
    path = _agents_md_path()
    if not os.path.exists(path):
        return ""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


def _create_default(path: str):
    """创建默认 AGENTS.md"""
    content = """# Maren Code 记忆

## 用户偏好与长期规定
"""
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception:
        pass
