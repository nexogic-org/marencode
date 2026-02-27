"""
core/skill/write_file.py — 文件写入技能
支持创建新文件、覆盖写入，自动创建父目录
"""
import os
from core.runtime_dir import resolve_path


def write_file(path: str, content: str) -> str:
    """
    写入内容到指定文件
    :param path: 文件路径（相对或绝对）
    :param content: 要写入的内容
    :return: 操作结果描述
    """
    if not path:
        return "[ERROR] 未指定文件路径。"
    if content is None:
        return "[ERROR] 写入内容不能为空。"

    abs_path = resolve_path(path)

    # 自动创建父目录
    parent = os.path.dirname(abs_path)
    if parent and not os.path.exists(parent):
        try:
            os.makedirs(parent, exist_ok=True)
        except Exception as e:
            return f"[ERROR] 创建目录失败: {e}"

    try:
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)
        size = os.path.getsize(abs_path)
        return f"[OK] 已写入文件: {abs_path} ({size} bytes)"
    except PermissionError as e:
        return f"[ERROR] 写入权限不足: {abs_path}\n详情: {e}"
    except OSError as e:
        return f"[ERROR] 文件系统错误: {abs_path}\n类型: {type(e).__name__}\n详情: {e}"
    except Exception as e:
        return f"[ERROR] 写入失败: {abs_path}\n类型: {type(e).__name__}\n详情: {e}"
