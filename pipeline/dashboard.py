"""
pipeline/dashboard.py — 精美 CLI 实时进度面板
项目进度、任务状态、文件写入进度实时展示
"""
import sys
import time
from colorama import Fore, Style


CAT = f"{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}ᓚᘏᗢ{Style.RESET_ALL}"

PHASE_ICONS = {
    "chatter":  f"{Fore.LIGHTMAGENTA_EX}💬{Style.RESET_ALL}",
    "leader":   f"{Fore.LIGHTYELLOW_EX}👑{Style.RESET_ALL}",
    "coder":    f"{Fore.LIGHTGREEN_EX}⌨{Style.RESET_ALL}",
    "designer": f"{Fore.LIGHTBLUE_EX}🎨{Style.RESET_ALL}",
    "tester":   f"{Fore.LIGHTCYAN_EX}🔍{Style.RESET_ALL}",
}

STATUS_ICONS = {
    "pending":  f"{Fore.LIGHTBLACK_EX}◌{Style.RESET_ALL}",
    "running":  f"{Fore.YELLOW}⟳{Style.RESET_ALL}",
    "done":     f"{Fore.GREEN}✓{Style.RESET_ALL}",
    "error":    f"{Fore.RED}✗{Style.RESET_ALL}",
    "waiting":  f"{Fore.LIGHTBLACK_EX}…{Style.RESET_ALL}",
    "review":   f"{Fore.CYAN}⊙{Style.RESET_ALL}",
}


def _phase_color(phase: str):
    m = {"chatter": Fore.LIGHTMAGENTA_EX, "leader": Fore.LIGHTYELLOW_EX,
         "coder": Fore.LIGHTGREEN_EX, "designer": Fore.LIGHTBLUE_EX,
         "tester": Fore.LIGHTCYAN_EX}
    return m.get(phase, Fore.WHITE)


def banner(title: str, color=Fore.LIGHTYELLOW_EX):
    w = 58
    print()
    print(f"  {color}{'═' * w}{Style.RESET_ALL}")
    print(f"  {CAT} {Style.BRIGHT}{color}{title}{Style.RESET_ALL}")
    print(f"  {color}{'═' * w}{Style.RESET_ALL}")
    print()


def phase_start(phase: str, msg: str):
    icon = PHASE_ICONS.get(phase, "")
    c = _phase_color(phase)
    print(f"  {icon} {Style.BRIGHT}{c}[{phase.upper()}]{Style.RESET_ALL} {msg}")


def phase_done(phase: str, msg: str):
    c = _phase_color(phase)
    print(f"  {STATUS_ICONS['done']} {Style.BRIGHT}{c}[{phase.upper()}]{Style.RESET_ALL} {msg}")


def phase_error(phase: str, msg: str):
    c = _phase_color(phase)
    print(f"  {STATUS_ICONS['error']} {Style.BRIGHT}{c}[{phase.upper()}]{Style.RESET_ALL} {msg}")


def progress_bar(current: int, total: int, width=30, label="") -> str:
    ratio = min(current / total, 1.0) if total > 0 else 1.0
    filled = int(width * ratio)
    bar = "█" * filled + "░" * (width - filled)
    pct = int(ratio * 100)
    pre = f"{label} " if label else ""
    return f"{pre}{Fore.LIGHTGREEN_EX}{bar}{Style.RESET_ALL} {pct}%"


def task_list(tasks: list):
    """打印任务列表面板"""
    print(f"  {Fore.LIGHTBLACK_EX}{'─' * 56}{Style.RESET_ALL}")
    for t in tasks:
        tid = t.get("id", "?")
        title = t.get("title", "")
        role = t.get("role", "")
        st = t.get("status", "pending")
        si = STATUS_ICONS.get(st, " ")
        c = _phase_color(role.lower())
        tag = f"{Style.BRIGHT}{c}[{role}]{Style.RESET_ALL}" if role else ""
        print(f"  {si} #{tid} {tag} {title}")
    print(f"  {Fore.LIGHTBLACK_EX}{'─' * 56}{Style.RESET_ALL}")
    print()


def file_written(path: str):
    """文件写入成功提示"""
    print(f"    {Fore.GREEN}✓{Style.RESET_ALL} 写入 {Fore.CYAN}{path}{Style.RESET_ALL}")


def file_error(path: str, err: str):
    """文件写入失败提示"""
    print(f"    {Fore.RED}✗{Style.RESET_ALL} 失败 {path}: {err}")


def loop_info(current: int, max_loops: int, mode: str):
    """循环信息提示"""
    mc = Fore.CYAN if mode == "quality" else Fore.YELLOW
    ml = "质量优先" if mode == "quality" else "节省优先"
    print(f"\n  {CAT} {Style.BRIGHT}测试循环 {current}/{max_loops}{Style.RESET_ALL} ({mc}{ml}{Style.RESET_ALL})")
    print(f"  {Fore.LIGHTBLACK_EX}{'─' * 56}{Style.RESET_ALL}")


def danger_warning(cmd: str):
    """危险命令警告"""
    print(f"\n  {Fore.RED}{Style.BRIGHT}⚠ 危险命令检测{Style.RESET_ALL}")
    print(f"  {Fore.RED}│{Style.RESET_ALL} {cmd}")
    print(f"  {Fore.RED}└{'─' * 40}{Style.RESET_ALL}")
