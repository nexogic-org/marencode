"""
core/skill/edit_file.py — 文件编辑技能
支持锚点定位更改、行号范围替换，节省 token 的增量编辑
"""
import os
from core.runtime_dir import resolve_path


def edit_file(path: str, anchor: str, new_content: str) -> str:
    """
    基于锚点的增量编辑：找到 anchor 文本并替换为 new_content
    类似 Cursor 的锚点更改策略，只传输变更部分，节省 token
    :param path: 文件路径
    :param anchor: 要查找的原始文本片段（锚点）
    :param new_content: 替换后的新内容
    :return: 操作结果描述
    """
    if not path:
        return "[ERROR] 未指定文件路径。"
    if not anchor:
        return "[ERROR] 未指定锚点文本。"

    abs_path = resolve_path(path)
    if not os.path.exists(abs_path):
        return f"[ERROR] 文件不存在: {abs_path}"
    if not os.path.isfile(abs_path):
        return f"[ERROR] 路径不是文件: {abs_path}"

    # 读取原始内容
    encodings = ["utf-8", "utf-8-sig", "gbk", "latin-1"]
    content = None
    used_enc = "utf-8"
    for enc in encodings:
        try:
            with open(abs_path, "r", encoding=enc) as f:
                content = f.read()
            used_enc = enc
            break
        except (UnicodeDecodeError, UnicodeError):
            continue

    if content is None:
        return f"[ERROR] 无法解码文件: {abs_path}"

    # 查找锚点
    idx = content.find(anchor)
    if idx == -1:
        return f"[ERROR] 未找到锚点文本。文件: {abs_path}"

    # 检查是否有多个匹配
    count = content.count(anchor)
    if count > 1:
        return f"[WARNING] 找到 {count} 处匹配，仅替换第一处。文件: {abs_path}"

    # 执行替换
    new_full = content[:idx] + new_content + content[idx + len(anchor):]

    try:
        with open(abs_path, "w", encoding=used_enc) as f:
            f.write(new_full)
        return f"[OK] 已更新文件: {abs_path} (替换了 {len(anchor)} 字符 → {len(new_content)} 字符)"
    except PermissionError as e:
        return f"[ERROR] 写入权限不足: {abs_path}\n详情: {e}"
    except Exception as e:
        return f"[ERROR] 写入失败: {abs_path}\n类型: {type(e).__name__}\n详情: {e}"


def edit_file_lines(path: str, start_line: int, end_line: int, new_content: str) -> str:
    """
    按行号范围替换文件内容
    :param path: 文件路径
    :param start_line: 起始行号（从 1 开始）
    :param end_line: 结束行号（包含）
    :param new_content: 替换后的新内容
    :return: 操作结果描述
    """
    if not path:
        return "[ERROR] 未指定文件路径。"

    abs_path = resolve_path(path)
    if not os.path.exists(abs_path):
        return f"[ERROR] 文件不存在: {abs_path}"

    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except PermissionError as e:
        return f"[ERROR] 读取权限不足: {abs_path}\n详情: {e}"
    except UnicodeDecodeError as e:
        return f"[ERROR] 文件编码错误: {abs_path}\n详情: {e}"
    except Exception as e:
        return f"[ERROR] 读取失败: {abs_path}\n类型: {type(e).__name__}\n详情: {e}"

    total = len(lines)
    if start_line < 1 or end_line < start_line or start_line > total:
        return f"[ERROR] 行号范围无效 ({start_line}-{end_line})，文件共 {total} 行。"

    # 执行替换
    new_lines = new_content.splitlines(keepends=True)
    if new_content and not new_content.endswith("\n"):
        new_lines[-1] += "\n"

    result_lines = lines[:start_line - 1] + new_lines + lines[end_line:]

    try:
        with open(abs_path, "w", encoding="utf-8") as f:
            f.writelines(result_lines)
        replaced = end_line - start_line + 1
        return f"[OK] 已替换第 {start_line}-{end_line} 行 ({replaced} 行 → {len(new_lines)} 行)"
    except PermissionError as e:
        return f"[ERROR] 写入权限不足: {abs_path}\n详情: {e}"
    except Exception as e:
        return f"[ERROR] 写入失败: {abs_path}\n类型: {type(e).__name__}\n详情: {e}"
