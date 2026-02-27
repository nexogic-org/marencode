"""
display/table.py — 表格渲染模块
负责 Markdown 表格和 Unicode 表格的解析与美化输出
"""
import re
import unicodedata
from colorama import Fore, Style
from display.style import InlineStyler


# 用于清理私有区域字符的正则
_CLEAN_RE = re.compile(r'[\uFFF0-\uFFF3\uE000-\uF8FF]')
# 用于去除 ANSI 转义序列的正则
_ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')


def is_table_line(line: str) -> bool:
    """判断一行是否为表格行（包含足够多的分隔符）"""
    cleaned = _clean_cell_text(line)
    if "|" in cleaned:
        return cleaned.strip().count("|") >= 2
    if "│" in cleaned:
        return cleaned.strip().count("│") >= 2
    return False


def is_table_separator(line: str) -> bool:
    """判断一行是否为表格分隔符行（如 |---| 或 ├──┤）"""
    s = line.strip()
    if not s:
        return False
    # Markdown 分隔符: |---|
    if "|" in s and "-" in s:
        if all(ch in "|-: " for ch in s):
            return True
    # Unicode 表格边框/分隔符
    box_chars = set("┌┐└┘├┤┬┴┼─│ ")
    if any(c in s for c in "┌└├┬┴┼─"):
        if all(ch in box_chars for ch in s):
            return True
    return False


def _clean_cell_text(text: str) -> str:
    """清理单元格文本：替换 Tab、移除私有区域字符"""
    text = text.replace("\t", "    ")
    return re.sub(r'[\uFFF0-\uFFF3\uE000-\uF8FF]', '', text)


def _split_row(line: str) -> list:
    """将表格行按分隔符拆分为单元格列表"""
    s = line.strip()
    sep = "│" if "│" in s else "|"
    if s.startswith(sep):
        s = s[1:]
    if s.endswith(sep):
        s = s[:-1]
    return [_clean_cell_text(p.strip()) for p in s.split(sep)]


def _visible_len(s: str) -> int:
    """
    计算字符串的可见宽度（考虑中文宽字符和 ANSI 转义序列）
    - 全角字符 (W/F) 宽度为 2
    - Ambiguous 字符根据具体范围判断
    - ANSI 转义序列宽度为 0
    """
    plain = _ANSI_RE.sub("", s)
    total = 0
    for ch in plain:
        # 排除零宽字符（组合字符、控制字符等）
        if unicodedata.category(ch) in ('Mn', 'Me', 'Cf', 'Cc'):
            continue
        eaw = unicodedata.east_asian_width(ch)
        if eaw in ("F", "W"):
            total += 2
        elif eaw == "A":
            cp = ord(ch)
            if 0x2500 <= cp <= 0x257F:  # Box Drawing 制表符
                total += 1
            elif cp == 0x00B7:  # Middle Dot (·)
                total += 1
            else:
                total += 2  # 默认 Ambiguous 在中文环境下为宽字符
        else:
            total += 1
    return total


def _style_cell(text: str, is_header: bool) -> str:
    """为单元格内容应用样式"""
    cell_styler = InlineStyler()
    rendered = cell_styler.feed(text) + cell_styler.finalize()
    if is_header:
        return f"{Style.BRIGHT}{Fore.LIGHTCYAN_EX}{rendered}{Style.RESET_ALL}"
    return rendered


def render_table(lines: list) -> str:
    """
    将收集到的表格行渲染为美化的 Unicode 表格
    返回渲染后的字符串（含换行）
    """
    # 清理空行
    clean_lines = [l.rstrip("\n") for l in lines if l.strip() != ""]
    if clean_lines:
        lines = clean_lines

    rows = []
    separator_index = -1
    for idx, line in enumerate(lines):
        if is_table_separator(line):
            separator_index = idx
            continue
        rows.append(_split_row(line))

    # 如果没有找到分隔符或没有数据行，回退为普通文本
    if not rows or separator_index == -1:
        styler = InlineStyler()
        return "".join(styler.feed(l + "\n") for l in lines)

    # 统一列数
    col_count = max(len(r) for r in rows)
    for r in rows:
        if len(r) < col_count:
            r.extend([""] * (col_count - len(r)))
        elif len(r) > col_count:
            r[:] = r[:col_count]

    # 渲染每个单元格（第一行为表头）
    rendered_rows = []
    for i, r in enumerate(rows):
        rendered_rows.append([
            _style_cell(r[j], is_header=(i == 0))
            for j in range(col_count)
        ])

    # 计算每列最大可见宽度
    widths = [0] * col_count
    for r in rendered_rows:
        for i, c in enumerate(r):
            widths[i] = max(widths[i], _visible_len(c))
    widths = [max(w + 2, 2) for w in widths]

    # 绘制表格边框辅助函数
    def hline(left, mid, right):
        return left + mid.join("─" * w for w in widths) + right

    out_lines = [hline("┌", "┬", "┐")]
    for i, styled_cells in enumerate(rendered_rows):
        padded_cells = []
        for j, cell in enumerate(styled_cells):
            pad_right = widths[j] - _visible_len(cell) - 1
            if pad_right < 1:
                pad_right = 1
            padded_cells.append(" " + cell + (" " * pad_right))
        line = "│" + "│".join(padded_cells) + "│"
        out_lines.append(line)
        if i == 0:
            out_lines.append(hline("├", "┼", "┤"))
    out_lines.append(hline("└", "┴", "┘"))
    return "\n".join(out_lines) + "\n"
