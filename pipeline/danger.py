"""
pipeline/danger.py — 危险命令审查系统
Coder -> Leader -> User 三级审查
"""
import json
from colorama import Fore, Style
from pipeline import dashboard
from shell.cmd.config import get_dangerous_commands


def check_dangerous(text: str) -> list:
    """检查文本中是否包含危险命令，返回匹配列表"""
    dangers = get_dangerous_commands()
    found = []
    lower = text.lower()
    for cmd in dangers:
        if cmd.lower() in lower:
            found.append(cmd)
    return found


def leader_review(cmd_list: list, leader_call_fn) -> str:
    """Leader 审查危险命令，返回 allow/deny/ask_user"""
    prompt = f"以下命令被标记为危险：{cmd_list}\n判断是否安全，回复 ALLOW 或 DENY 或 ASK_USER"
    reply = leader_call_fn(prompt)
    upper = reply.strip().upper()
    if "ALLOW" in upper:
        return "allow"
    if "DENY" in upper:
        return "deny"
    return "ask_user"


def ask_user_confirm(cmd_list: list) -> bool:
    """询问用户是否允许执行危险命令"""
    for cmd in cmd_list:
        dashboard.danger_warning(cmd)
    print(f"  {Fore.YELLOW}允许执行? (y/N): {Style.RESET_ALL}", end="")
    try:
        ans = input().strip().lower()
    except (EOFError, KeyboardInterrupt):
        return False
    return ans == "y"
