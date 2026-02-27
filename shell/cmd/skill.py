"""
shell/cmd/skill.py — 技能列表命令
美化展示所有已加载的技能及其角色归属
"""
import json
import os
from colorama import Style, Fore
from shell.cmd import prefix
from utils.inited import skill_json_path


def run():
    """展示已加载的技能列表（美化表格）"""
    cat = f"{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}ᓚᘏᗢ{Style.RESET_ALL}"
    path = skill_json_path()

    if not os.path.exists(path):
        print(f"{prefix()}{Fore.RED}未找到 skill.json: {path}{Style.RESET_ALL}")
        return

    try:
        with open(path, "r", encoding="utf-8") as f:
            skills = json.load(f)
    except Exception as e:
        print(f"{prefix()}{Fore.RED}[ERROR] 加载技能失败: {e}{Style.RESET_ALL}")
        return

    if not skills:
        print(f"{prefix()}{Fore.YELLOW}暂无已配置的技能{Style.RESET_ALL}")
        return

    # 打印标题
    print()
    w = 56
    print(f"  {Fore.LIGHTGREEN_EX}{'─' * w}{Style.RESET_ALL}")
    print(f"  {cat} {Style.BRIGHT}{Fore.LIGHTGREEN_EX}"
          f"已加载技能 ({len(skills)} 个){Style.RESET_ALL}")
    print(f"  {Fore.LIGHTGREEN_EX}{'─' * w}{Style.RESET_ALL}")
    print()

    # 按角色分组展示
    role_skills = {}
    for skill in skills:
        for role in skill.get("roles", ["未分配"]):
            role_skills.setdefault(role, []).append(skill)

    # 角色颜色映射
    role_colors = {
        "Chatter": Fore.LIGHTMAGENTA_EX,
        "Coder": Fore.LIGHTGREEN_EX,
        "Leader": Fore.LIGHTYELLOW_EX,
        "Tester": Fore.LIGHTCYAN_EX,
    }

    for role, role_skill_list in role_skills.items():
        color = role_colors.get(role, Fore.WHITE)
        print(f"  {Style.BRIGHT}{color}[{role}]{Style.RESET_ALL}")

        for s in role_skill_list:
            name = s.get("name", "?")
            desc = s.get("description", "")
            # 技能名称左对齐，描述右侧
            print(f"    {Fore.GREEN}•{Style.RESET_ALL} "
                  f"{Fore.CYAN}{name:<20}{Style.RESET_ALL} "
                  f"{Fore.LIGHTBLACK_EX}{desc}{Style.RESET_ALL}")
        print()

    print(f"  {Fore.LIGHTBLACK_EX}{'─' * w}{Style.RESET_ALL}")
    print()
