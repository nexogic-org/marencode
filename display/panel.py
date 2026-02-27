"""
display/panel.py — 终端美化组件
进度条、状态面板、分隔线、角色标签
"""
from colorama import Fore, Style
import time
import sys


# ─── 角色颜色映射 ───
ROLE_COLORS = {
    "Leader":  Fore.LIGHTYELLOW_EX,
    "Coder":   Fore.LIGHTGREEN_EX,
    "Tester":  Fore.LIGHTCYAN_EX,
    "Chatter": Fore.LIGHTMAGENTA_EX,
}

ROLE_ICONS = {
    "Leader":  "👑",
    "Coder":   "⌨",
    "Tester":  "🔍",
    "Chatter": "💬",
}


def divider(char="─", width=60, color=Fore.LIGHTBLACK_EX):
    """打印分隔线"""
    print(f"{color}{char * width}{Style.RESET_ALL}")


def role_tag(role: str) -> str:
    """返回带颜色的角色标签，如 [Leader]"""
    color = ROLE_COLORS.get(role, Fore.WHITE)
    icon = ROLE_ICONS.get(role, "")
    return f"{Style.BRIGHT}{color}[{icon} {role}]{Style.RESET_ALL}"


def progress_bar(current: int, total: int, width=40, label="") -> str:
    """返回文本进度条字符串"""
    if total <= 0:
        ratio = 1.0
    else:
        ratio = min(current / total, 1.0)
    filled = int(width * ratio)
    bar = "█" * filled + "░" * (width - filled)
    pct = int(ratio * 100)
    prefix = f"{label} " if label else ""
    return f"{prefix}{Fore.LIGHTGREEN_EX}{bar}{Style.RESET_ALL} {pct}%"


def status_line(role: str, message: str, status="running"):
    """打印单行状态信息"""
    tag = role_tag(role)
    if status == "running":
        icon = f"{Fore.YELLOW}⟳{Style.RESET_ALL}"
    elif status == "done":
        icon = f"{Fore.GREEN}✓{Style.RESET_ALL}"
    elif status == "error":
        icon = f"{Fore.RED}✗{Style.RESET_ALL}"
    elif status == "waiting":
        icon = f"{Fore.LIGHTBLACK_EX}◌{Style.RESET_ALL}"
    else:
        icon = " "
    print(f"  {icon} {tag} {message}")


def task_panel(title: str, tasks: list):
    """
    打印任务面板
    tasks: [{"id": 1, "title": "...", "role": "Coder", "status": "pending"}]
    """
    cat = f"{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}ᓚᘏᗢ{Style.RESET_ALL}"
    print()
    print(f"  {cat} {Style.BRIGHT}{Fore.LIGHTYELLOW_EX}{title}{Style.RESET_ALL}")
    divider("─", 56, Fore.LIGHTBLACK_EX)
    for t in tasks:
        tid = t.get("id", "?")
        ttitle = t.get("title", "")
        role = t.get("role", "")
        st = t.get("status", "pending")
        tag = role_tag(role) if role else ""
        # 状态图标
        if st == "done":
            si = f"{Fore.GREEN}✓{Style.RESET_ALL}"
        elif st == "running":
            si = f"{Fore.YELLOW}⟳{Style.RESET_ALL}"
        elif st == "error":
            si = f"{Fore.RED}✗{Style.RESET_ALL}"
        else:
            si = f"{Fore.LIGHTBLACK_EX}◌{Style.RESET_ALL}"
        print(f"  {si} #{tid} {tag} {ttitle}")
    divider("─", 56, Fore.LIGHTBLACK_EX)
    print()
