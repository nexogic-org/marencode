from colorama import init, AnsiToWin32, Style, Fore
from utils import inited
import constants
import sys

init(autoreset=True)

sys.stdout = AnsiToWin32(sys.stdout).stream

# ── 主题色：暖色猫咪渐变（琥珀 → 奶油黄） ──
GRADIENT = [
    '\033[38;5;209m',  # 暖橘
    '\033[38;5;215m',  # 浅橘
    '\033[38;5;221m',  # 琥珀
    '\033[38;5;222m',  # 暖黄
    '\033[38;5;223m',  # 奶油
    '\033[38;5;229m',  # 浅奶油
    '\033[38;5;230m',  # 象牙白
]
RESET = '\033[0m'
DIM = '\033[38;5;242m'
ACCENT = '\033[38;5;222m'
WARM = '\033[38;5;209m'


def print_maren_logo():
    print()

    # Logo 第一部分: MAREN
    logo_part1 = [
        "███╗   ███╗ █████╗ ██████╗ ███████╗███╗   ██╗",
        "████╗ ████║██╔══██╗██╔══██╗██╔════╝████╗  ██║",
        "██╔████╔██║███████║██████╔╝█████╗  ██╔██╗ ██║",
        "██║╚██╔╝██║██╔══██║██╔══██╗██╔══╝  ██║╚██╗██║",
        "██║ ╚═╝ ██║██║  ██║██║  ██║███████╗██║ ╚████║",
        "╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═══╝",
    ]

    # Logo 第二部分: CODE
    logo_part2 = [
        " ██████╗ ██████╗ ██████╗ ███████╗",
        "██╔════╝██╔═══██╗██╔══██╗██╔════╝",
        "██║     ██║   ██║██║  ██║█████╗  ",
        "██║     ██║   ██║██║  ██║██╔══╝  ",
        "╚██████╗╚██████╔╝██████╔╝███████╗",
        " ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝",
    ]

    for i, (line1, line2) in enumerate(zip(logo_part1, logo_part2)):
        color = GRADIENT[i % len(GRADIENT)]
        print(f"  {color}{line1}  {line2}{RESET}")


def print_hello_page():
    print_maren_logo()

    # 分隔线
    w = 82
    print(f"  {DIM}{'─' * w}{RESET}")
    print()

    # 猫咪吉祥物 + 项目全称（居中）
    cat = f"{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}ᓚᘏᗢ{Style.RESET_ALL}"
    title_text = "ᓚᘏᗢ Maren Automatically Runs Executable Navigation Code"
    pad = max((w - len(title_text)) // 2, 0)
    print(f"{' ' * pad}{cat} {Style.BRIGHT}{ACCENT}Maren Automatically Runs Executable Navigation Code{RESET}")
    print()

    # 状态信息行
    is_init = inited.is_inited()
    init_icon = f"\033[38;5;114m✓{RESET}" if is_init else f"\033[38;5;203m✗{RESET}"
    init_text = "Ready" if is_init else "Not initialized"

    print(f"  {DIM}Version{RESET}  {ACCENT}{constants.VERSION}{RESET}"
          f"    {DIM}Author{RESET}  {ACCENT}{constants.AUTHOR}{RESET}"
          f"    {DIM}Status{RESET}  {init_icon} {init_text}"
          f"    {DIM}License{RESET}  {ACCENT}MIT{RESET}")

    # 底部分隔线
    print(f"  {DIM}{'─' * w}{RESET}")
    print()
