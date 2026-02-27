"""
core/skill/file_ops.py — 文件操作技能
支持重命名文件、新建文件、新建目录
"""
import os
import shutil
from core.runtime_dir import resolve_path


def rename_file(old_path: str, new_path: str) -> str:
    """
    重命名或移动文件/目录
    :param old_path: 原路径
    :param new_path: 新路径
    :return: 操作结果描述
    """
    if not old_path or not new_path:
        return "[ERROR] 路径参数不能为空。"

    abs_old = resolve_path(old_path)
    abs_new = resolve_path(new_path)

    if not os.path.exists(abs_old):
        return f"[ERROR] 原路径不存在: {abs_old}"

    if os.path.exists(abs_new):
        return f"[ERROR] 目标路径已存在: {abs_new}"

    # 确保目标父目录存在
    parent = os.path.dirname(abs_new)
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)

    try:
        shutil.move(abs_old, abs_new)
        return f"[OK] 已重命名: {abs_old} → {abs_new}"
    except PermissionError as e:
        return f"[ERROR] 重命名权限不足: {abs_old} → {abs_new}\n详情: {e}"
    except Exception as e:
        return f"[ERROR] 重命名失败: {type(e).__name__}: {e}\n原路径: {abs_old}\n目标: {abs_new}"


def create_directory(path: str) -> str:
    """
    创建目录（支持多级）
    :param path: 目录路径
    :return: 操作结果描述
    """
    if not path:
        return "[ERROR] 未指定目录路径。"

    abs_path = resolve_path(path)

    if os.path.exists(abs_path):
        if os.path.isdir(abs_path):
            return f"[OK] 目录已存在: {abs_path}"
        return f"[ERROR] 路径已存在且不是目录: {abs_path}"

    try:
        os.makedirs(abs_path, exist_ok=True)
        return f"[OK] 已创建目录: {abs_path}"
    except PermissionError as e:
        return f"[ERROR] 创建目录权限不足: {abs_path}\n详情: {e}"
    except Exception as e:
        return f"[ERROR] 创建目录失败: {type(e).__name__}: {e}\n路径: {abs_path}"


def create_file(path: str, content: str = "") -> str:
    """
    创建新文件（如果不存在）
    :param path: 文件路径
    :param content: 初始内容（可选）
    :return: 操作结果描述
    """
    if not path:
        return "[ERROR] 未指定文件路径。"

    abs_path = resolve_path(path)

    if os.path.exists(abs_path):
        return f"[ERROR] 文件已存在: {abs_path}"

    parent = os.path.dirname(abs_path)
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)

    try:
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content or "")
        return f"[OK] 已创建文件: {abs_path}"
    except PermissionError as e:
        return f"[ERROR] 创建文件权限不足: {abs_path}\n详情: {e}"
    except Exception as e:
        return f"[ERROR] 创建文件失败: {type(e).__name__}: {e}\n路径: {abs_path}"
