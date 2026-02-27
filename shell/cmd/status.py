"""
shell/cmd/status.py — code status 命令
显示所有角色、模型、API密钥（脱敏）、配置等系统状态信息
"""
import json
import os
from datetime import datetime
from colorama import Fore, Style
from shell.cmd import prefix
import utils.inited as inited
import constants


# ── 主题色常量 ──
DIM = Fore.LIGHTBLACK_EX
ACCENT = Fore.LIGHTYELLOW_EX
CYAN = Fore.CYAN
GREEN = Fore.GREEN
RED = Fore.RED
YELLOW = Fore.YELLOW
CAT = f"{Style.BRIGHT}{ACCENT}ᓚᘏᗢ{Style.RESET_ALL}"
R = Style.RESET_ALL
B = Style.BRIGHT


def _mask_key(key: str) -> str:
    """API密钥脱敏：显示前4位 + *** + 后3位"""
    if not key or len(key) < 8:
        return "****"
    return f"{key[:4]}***{key[-3:]}"


def _load_maren_config():
    """加载 maren.json 配置"""
    path = inited.maren_json_path()
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _load_project_info():
    """加载 project.json 项目信息"""
    path = os.path.join(inited.maren_dir_path(), "project.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _load_user_config():
    """加载 config.json 用户配置"""
    path = os.path.join(inited.maren_dir_path(), "config.json")
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _load_role_skills():
    """加载角色技能映射"""
    path = inited.role_skills_json_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


# ── 角色图标与颜色 ──
ROLE_META = {
    "coder":         ("⌨", Fore.LIGHTGREEN_EX),
    "leader":        ("👑", Fore.LIGHTYELLOW_EX),
    "tester":        ("🔍", Fore.LIGHTCYAN_EX),
    "chatter":       ("💬", Fore.LIGHTMAGENTA_EX),
    "icon_designer": ("🎨", Fore.LIGHTRED_EX),
}


def _print_header():
    """打印状态面板头部"""
    w = 58
    print()
    print(f"  {ACCENT}{'═' * w}{R}")
    print(f"  {CAT} {B}{ACCENT}Maren Code · System Status{R}")
    print(f"  {ACCENT}{'═' * w}{R}")


def _print_section(title: str):
    """打印分节标题"""
    print(f"\n  {B}{ACCENT}┌─ {title}{R}")


def _print_row(label: str, value: str, indent=2):
    """打印单行键值"""
    pad = " " * indent
    print(f"  {DIM}│{R}{pad}{DIM}{label}:{R} {value}")


def _print_footer():
    w = 58
    print(f"\n  {ACCENT}{'═' * w}{R}")
    print()


def run():
    """status 命令入口"""
    if not inited.is_inited():
        print(f"{prefix()}{B}{RED}[ERROR]{R} Not initialized. Run {GREEN}code init boot{R} first.")
        return

    config = _load_maren_config()
    if not config:
        print(f"{prefix()}{B}{RED}[ERROR]{R} Failed to load maren.json")
        return

    user_cfg = _load_user_config()
    project = _load_project_info()
    role_skills = _load_role_skills()
    mc = config.get("model", {})

    _print_header()

    # ── 基本信息 ──
    _print_section("General")
    _print_row("Version", f"{CYAN}{constants.VERSION}{R}")
    _print_row("Language", f"{CYAN}{config.get('lang', 'N/A')}{R}")
    _print_row("Base URL", f"{CYAN}{mc.get('base_url', 'N/A')}{R}")
    mode = user_cfg.get("mode", "quality")
    mode_c = CYAN if mode == "quality" else YELLOW
    mode_label = "Quality" if mode == "quality" else "Saving"
    _print_row("Mode", f"{mode_c}{mode_label}{R}")
    _print_row("Max Loops", f"{GREEN}{user_cfg.get('max_loops', 5)}{R}")

    # ── 项目信息 ──
    if project:
        _print_section("Project")
        _print_row("Name", f"{CYAN}{project.get('name', 'N/A')}{R}")
        _print_row("Created", f"{DIM}{project.get('created', 'N/A')}{R}")
        desc = project.get("description", "")
        if desc:
            _print_row("Description", f"{desc}")

    # ── 角色 & 模型 & 密钥 ──
    _print_section("Roles & Models")
    api_keys = mc.get("api_key", {})
    role_urls = mc.get("role_base_urls", {})
    overrides = user_cfg.get("role_model_override", {})

    roles = [
        ("coder", "Coder"),
        ("leader", "Leader"),
        ("tester", "Tester"),
        ("chatter", "Chatter"),
        ("icon_designer", "Icon Designer"),
    ]

    for role_key, role_label in roles:
        icon, color = ROLE_META.get(role_key, ("", Fore.WHITE))
        role_cfg = mc.get(role_key, {})
        model = overrides.get(role_key) or role_cfg.get("model_name", "N/A")
        key = api_keys.get(role_key, "")
        masked = _mask_key(key)
        temp = role_cfg.get("temperature", "N/A")
        max_t = role_cfg.get("max_tokens", "N/A")
        url = role_urls.get(role_key, "")

        print(f"  {DIM}│{R}")
        print(f"  {DIM}│{R}  {icon} {B}{color}{role_label}{R}")
        print(f"  {DIM}│{R}    {DIM}Model:{R}  {CYAN}{model}{R}")
        print(f"  {DIM}│{R}    {DIM}Key:{R}    {YELLOW}{masked}{R}")
        print(f"  {DIM}│{R}    {DIM}Temp:{R}   {GREEN}{temp}{R}"
              f"   {DIM}MaxTok:{R} {GREEN}{max_t}{R}")

        if url:
            print(f"  {DIM}│{R}    {DIM}URL:{R}    {CYAN}{url}{R}")

        # 技能列表
        skills = role_skills.get(role_label, [])
        if skills:
            skill_str = f"{DIM}, {R}".join(
                f"{GREEN}{s}{R}" for s in skills
            )
            print(f"  {DIM}│{R}    {DIM}Skills:{R} {skill_str}")

    # ── 额外模型 ──
    extras = user_cfg.get("extra_models", {})
    if extras:
        _print_section("Extra Models")
        for name, info in extras.items():
            if isinstance(info, dict):
                url = info.get("base_url", "")
                key = info.get("api_key", "")
                masked = _mask_key(key)
                print(f"  {DIM}│{R}  {CYAN}{name}{R}: {url} ({YELLOW}{masked}{R})")
            else:
                print(f"  {DIM}│{R}  {CYAN}{name}{R}")

    # ── .maren 目录文件状态 ──
    _print_section("Config Files")
    files_check = [
        ("maren.json", inited.maren_json_path()),
        ("skill.json", inited.skill_json_path()),
        ("role_skills.json", inited.role_skills_json_path()),
        ("project.json", os.path.join(inited.maren_dir_path(), "project.json")),
        ("config.json", os.path.join(inited.maren_dir_path(), "config.json")),
    ]
    for fname, fpath in files_check:
        exists = os.path.exists(fpath)
        icon = f"{GREEN}✓{R}" if exists else f"{DIM}✗{R}"
        print(f"  {DIM}│{R}  {icon} {fname}")

    _print_footer()
