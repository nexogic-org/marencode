"""
read_file 技能 — 读取本地文件内容
支持文本文件读取，自动检测编码，限制最大读取大小
"""
import os
from core.runtime_dir import resolve_path


def read_file(path: str, max_lines: int = 200) -> str:
    """
    读取指定路径的文件内容
    :param path: 文件路径（相对或绝对）
    :param max_lines: 最大读取行数，默认 200
    :return: 文件内容字符串
    """
    if not path:
        return "[ERROR] 未指定文件路径。"

    abs_path = resolve_path(path)

    if not os.path.exists(abs_path):
        return f"[ERROR] 文件不存在: {abs_path}"

    if not os.path.isfile(abs_path):
        return f"[ERROR] 路径不是文件: {abs_path}"

    # 安全限制：最大 1MB
    size = os.path.getsize(abs_path)
    if size > 1024 * 1024:
        return f"[ERROR] 文件过大 ({size} bytes)，最大支持 1MB。"

    # 尝试多种编码
    encodings = ["utf-8", "utf-8-sig", "gbk", "gb2312", "latin-1"]
    content = None
    for enc in encodings:
        try:
            with open(abs_path, "r", encoding=enc) as f:
                content = f.read()
            break
        except (UnicodeDecodeError, UnicodeError):
            continue

    if content is None:
        return f"[ERROR] 无法解码文件: {abs_path}"

    lines = content.splitlines()
    total = len(lines)

    if total > max_lines:
        lines = lines[:max_lines]
        result = "\n".join(lines)
        result += f"\n\n... (已截断，共 {total} 行，仅显示前 {max_lines} 行)"
    else:
        result = "\n".join(lines)

    return f"文件: {abs_path}\n行数: {total}\n\n{result}"


def list_dir(path: str = ".") -> str:
    """
    列出目录内容
    :param path: 目录路径，默认当前目录
    :return: 目录内容列表
    """
    abs_path = resolve_path(path)

    if not os.path.exists(abs_path):
        return f"[ERROR] 目录不存在: {abs_path}"

    if not os.path.isdir(abs_path):
        return f"[ERROR] 路径不是目录: {abs_path}"

    items = []
    try:
        for name in sorted(os.listdir(abs_path)):
            full = os.path.join(abs_path, name)
            if os.path.isdir(full):
                items.append(f"  [DIR]  {name}/")
            else:
                size = os.path.getsize(full)
                items.append(f"  [FILE] {name} ({size} bytes)")
    except PermissionError:
        return f"[ERROR] 无权限访问: {abs_path}"

    header = f"目录: {abs_path}\n共 {len(items)} 项\n"
    return header + "\n".join(items)
