"""
display — 终端美化渲染包
统一导出流式渲染器、表格渲染、代码高亮、面板组件
"""
from display.stream import StreamRenderer
from display.table import render_table, is_table_line, is_table_separator
from display.code import highlight_code

__all__ = [
    "StreamRenderer",
    "render_table",
    "is_table_line",
    "is_table_separator",
    "highlight_code",
]
