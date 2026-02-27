from typing import List
from colorama import init, Fore, Style
from utils import inited

# 初始化 colorama
init(autoreset=True)

PROMPT_COLOR = Fore.YELLOW
CAT_COLOR = Fore.LIGHTYELLOW_EX
GRADIENT = [
    Fore.RED,
    Fore.LIGHTRED_EX,
    Fore.YELLOW,
    Fore.LIGHTYELLOW_EX
]

def get_gradient_text(text, colors, start_index=0):
    """
    生成渐变色文本
    :param text: 要渲染的文本
    :param colors: 颜色列表
    :param start_index: 颜色起始索引
    """
    result = ""
    for i, char in enumerate(text):
        color = colors[(start_index + i) % len(colors)]
        result += f"{color}{char}"
    return result + Style.RESET_ALL

def gradient_text(text, start_index=0):
    return get_gradient_text(text, GRADIENT, start_index)

def read_required():
    """读取必填输入，为空则报错"""
    try:
        value = input().strip()
    except EOFError:
        return None
    if not value:
        print(f"{Fore.RED}[ERROR] Parameter cannot be empty.{Style.RESET_ALL}")
        return None
    return value

def read_required_url():
    value = read_required()
    if value is None:
        return None
    if not (value.startswith("http://") or value.startswith("https://")):
        print(f"{Fore.RED}[ERROR] Parameter must start with http:// or https://.{Style.RESET_ALL}")
        return None
    return value

def print_wizard_header():
    """
    打印 Maren Code Setup Wizard 头部
    """
    # T ᓚᘏᗢ Maren Code Setup Wizard
    # 分段处理，确保猫符号颜色独立，同时保持渐变连贯
    
    part1_text = "T  "
    part1 = f"{Fore.LIGHTBLACK_EX}{part1_text}{Style.RESET_ALL}"

    cat = f"{Style.BRIGHT}{CAT_COLOR}ᓚᘏᗢ{Style.RESET_ALL}"
    part2_text = " Maren Code Setup Wizard"
    part2 = gradient_text(part2_text, start_index=0)

    print(part1 + cat + part2)

def run(args: List[str]):
    if not args:
        return
    cmd = args[0].lower()
    if cmd == "inited":
        cat = f"{Style.BRIGHT}{CAT_COLOR}ᓚᘏᗢ{Style.RESET_ALL}"
        if inited.is_inited():
            print(f"{cat} {Fore.GREEN}✓{Style.RESET_ALL}")
        else:
            print(f"{cat} {Fore.YELLOW}✗{Style.RESET_ALL}")
        return
    if cmd != "boot":
        return

    # 检查是否已初始化，如果已初始化则尝试修复/补全文件，而不是报错或覆盖
    if inited.is_inited():
        print(f"{Fore.YELLOW}Maren Code is already initialized.{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Do you want to re-initialize? (y/N): {Style.RESET_ALL}", end="")
        choice = input().strip().lower()
        if choice != 'y':
            # 即使不重新初始化，也确保 .maren 下的文件完整
            # is_inited 内部已经做了这个检查，所以直接调用一次即可
            inited.is_inited()
            print(f"{Fore.GREEN}Configuration check passed.{Style.RESET_ALL}")
            return

    # 1. 打印 Logo
    print_wizard_header()
    
    # Step 1: API Base URL
    print(f"{Fore.LIGHTBLACK_EX}|{Style.RESET_ALL}")
    # 引导语使用主题色
    print(f"{Fore.GREEN}*{Style.RESET_ALL}  {PROMPT_COLOR}Please enter your API base URL{Style.RESET_ALL}")
    print(f"{Fore.LIGHTBLACK_EX}|{Style.RESET_ALL}  ", end="")
    
    api_base = read_required_url()
    if api_base is None:
        return

    print(f"{Fore.LIGHTBLACK_EX}|{Style.RESET_ALL}")
    print(f"{Fore.GREEN}*{Style.RESET_ALL}  {PROMPT_COLOR}Please enter your language (BCP 47){Style.RESET_ALL}")
    print(f"{Fore.LIGHTBLACK_EX}|{Style.RESET_ALL}  ", end="")

    language = read_required()
    if language is None:
        return

    # Step 2: Model Selection
    print(f"{Fore.LIGHTBLACK_EX}|{Style.RESET_ALL}")
    print(f"{Fore.GREEN}*{Style.RESET_ALL}  {PROMPT_COLOR}Please choose a large model for your Maren Character:{Style.RESET_ALL}")
    
    models = {}
    roles = [
        ("Coder", "coder"),
        ("Leader", "leader"),
        ("Tester", "tester"),
        ("Chatter", "chatter"),
        ("Icon Designer(Raw image AI)", "icon_designer")
    ]
    
    for role_label, role_key in roles:
        print(f"{Fore.LIGHTBLACK_EX}|{Style.RESET_ALL}  {PROMPT_COLOR}{role_label}:{Style.RESET_ALL} ", end="")
        model = read_required()
        if model is None:
            return
        models[role_key] = model

    # Step 3: API Key
    print(f"{Fore.LIGHTBLACK_EX}|{Style.RESET_ALL}")
    print(f"{Fore.GREEN}*{Style.RESET_ALL}  {PROMPT_COLOR}Please enter your API key{Style.RESET_ALL}")
    
    keys = {}
    role_keys = [
        ("Coder", "coder"),
        ("Leader", "leader"),
        ("Tester", "tester"),
        ("Chatter", "chatter"),
        ("Icon Designer", "icon_designer")
    ]
    
    for role_label, role_key in role_keys:
        print(f"{Fore.LIGHTBLACK_EX}|{Style.RESET_ALL}  {PROMPT_COLOR}{role_label}:{Style.RESET_ALL} ", end="")
        key = read_required()
        if key is None:
            return
        keys[role_key] = key

    # Step 4: Complete
    print(f"{Fore.LIGHTBLACK_EX}|{Style.RESET_ALL}")
    print(f"{Fore.GREEN}*{Style.RESET_ALL}  {PROMPT_COLOR}Initialization complete!{Style.RESET_ALL}")
    print(f"{Fore.LIGHTBLACK_EX}|{Style.RESET_ALL}  {PROMPT_COLOR}You can try:{Style.RESET_ALL}")
    print(f"{Fore.LIGHTBLACK_EX}|{Style.RESET_ALL}    {PROMPT_COLOR}- code chat \"What is your name?\"{Style.RESET_ALL}")
    print(f"{Fore.LIGHTBLACK_EX}—{Style.RESET_ALL}")
    inited.init_maren(api_base, language, models, keys)
