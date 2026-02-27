"""
shell/cmd/config.py — 配置管理命令
code config show
code config mode quality|saving
code config loops <number>
code config model add <name> <base_url> <api_key>
code config model set <role> <model_name>
code config model list
code config danger add <command>
code config danger list
code config danger remove <command>
"""
import json
import os
from colorama import Fore, Style
from shell.cmd import prefix
import utils.inited as inited


CONFIG_FILE = "config.json"


def _config_path():
    return os.path.join(inited.maren_dir_path(), CONFIG_FILE)


def _load_config():
    path = _config_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return _default_config()


def _default_config():
    return {
        "mode": "quality",
        "max_loops": 5,
        "extra_models": {},
        "role_model_override": {},
        "dangerous_commands": [
            "rm -rf /", "rm -rf ~", "del /f /s /q",
            "format", "DROP TABLE", "DROP DATABASE",
            "shutdown", "reboot", "mkfs",
            "dd if=", "> /dev/sda", ":(){ :|:& };:",
            "chmod -R 777 /", "chown -R", "kill -9 1",
            "wget|sh", "curl|bash"
        ]
    }


def _save_config(cfg):
    os.makedirs(inited.maren_dir_path(), exist_ok=True)
    with open(_config_path(), "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=4)


def get_config():
    """公共接口：供其他模块读取配置"""
    return _load_config()


def get_mode():
    """获取当前模式: quality 或 saving"""
    return _load_config().get("mode", "quality")


def get_max_loops():
    """获取最大循环次数"""
    cfg = _load_config()
    mode = cfg.get("mode", "quality")
    return cfg.get("max_loops", 5 if mode == "quality" else 3)


def get_dangerous_commands():
    """获取危险命令列表"""
    return _load_config().get("dangerous_commands", [])


def get_role_model_override(role: str):
    """获取角色模型覆盖，返回 model_name 或 None"""
    return _load_config().get("role_model_override", {}).get(role.lower())


def _show(cfg):
    mode = cfg.get("mode", "quality")
    loops = cfg.get("max_loops", 5)
    mode_color = Fore.CYAN if mode == "quality" else Fore.YELLOW
    mode_label = "质量优先 (Quality)" if mode == "quality" else "节省优先 (Saving)"

    print(f"\n{prefix()}{Style.BRIGHT}━━━ 当前配置 ━━━{Style.RESET_ALL}\n")
    print(f"  {Fore.LIGHTBLACK_EX}模式:{Style.RESET_ALL}     {mode_color}{Style.BRIGHT}{mode_label}{Style.RESET_ALL}")
    print(f"  {Fore.LIGHTBLACK_EX}最大循环:{Style.RESET_ALL} {Fore.GREEN}{loops}{Style.RESET_ALL}")

    overrides = cfg.get("role_model_override", {})
    if overrides:
        print(f"\n  {Fore.LIGHTBLACK_EX}角色模型覆盖:{Style.RESET_ALL}")
        for role, model in overrides.items():
            print(f"    {Fore.LIGHTYELLOW_EX}{role:<12}{Style.RESET_ALL} → {Fore.CYAN}{model}{Style.RESET_ALL}")

    extras = cfg.get("extra_models", {})
    if extras:
        print(f"\n  {Fore.LIGHTBLACK_EX}额外模型:{Style.RESET_ALL}")
        for name, info in extras.items():
            if isinstance(info, dict):
                url = info.get("base_url", "")
                key = info.get("api_key", "")
                masked = key[:4] + "****" + key[-4:] if len(key) > 8 else "****"
                print(f"    {Fore.CYAN}{name}{Style.RESET_ALL}: {url} ({masked})")
            else:
                masked = info[:4] + "****" + info[-4:] if len(str(info)) > 8 else "****"
                print(f"    {Fore.CYAN}{name}{Style.RESET_ALL}: {masked}")

    dangers = cfg.get("dangerous_commands", [])
    if dangers:
        print(f"\n  {Fore.LIGHTBLACK_EX}危险命令 ({len(dangers)}):{Style.RESET_ALL}")
        for cmd in dangers[:5]:
            print(f"    {Fore.RED}⚠ {cmd}{Style.RESET_ALL}")
        if len(dangers) > 5:
            print(f"    {Fore.LIGHTBLACK_EX}... 还有 {len(dangers)-5} 条{Style.RESET_ALL}")
    print()


def run(args):
    """config 命令入口"""
    if not args:
        _show(_load_config())
        return

    sub = args[0].lower()
    cfg = _load_config()

    if sub == "show":
        _show(cfg)

    elif sub == "mode":
        if len(args) < 2:
            print(f"{prefix()}用法: config mode quality|saving")
            return
        mode = args[1].lower()
        if mode not in ("quality", "saving"):
            print(f"{prefix()}{Fore.RED}模式只能是 quality 或 saving{Style.RESET_ALL}")
            return
        cfg["mode"] = mode
        cfg["max_loops"] = 5 if mode == "quality" else 3
        _save_config(cfg)
        c = Fore.CYAN if mode == "quality" else Fore.YELLOW
        label = "质量优先" if mode == "quality" else "节省优先"
        print(f"{prefix()}模式已设为 {c}{Style.BRIGHT}{label}{Style.RESET_ALL} (循环上限: {cfg['max_loops']})")

    elif sub == "loops":
        if len(args) < 2:
            print(f"{prefix()}用法: config loops <1-10>")
            return
        try:
            n = int(args[1])
            if n < 1 or n > 10:
                raise ValueError
        except ValueError:
            print(f"{prefix()}{Fore.RED}循环次数必须是 1-10 的整数{Style.RESET_ALL}")
            return
        cfg["max_loops"] = n
        _save_config(cfg)
        print(f"{prefix()}最大循环次数已设为 {Fore.GREEN}{n}{Style.RESET_ALL}")

    elif sub == "model":
        _handle_model(args[1:], cfg)

    elif sub == "danger":
        _handle_danger(args[1:], cfg)

    elif sub == "url":
        _handle_url(args[1:], cfg)

    else:
        print(f"{prefix()}{Fore.RED}未知子命令: {sub}{Style.RESET_ALL}")
        _print_usage()


def _handle_model(args, cfg):
    if not args:
        _print_model_usage()
        return
    action = args[0].lower()

    if action == "add" and len(args) >= 4:
        name = args[1]
        base_url = args[2]
        api_key = args[3]
        cfg.setdefault("extra_models", {})[name] = {
            "base_url": base_url,
            "api_key": api_key
        }
        _save_config(cfg)
        print(f"{prefix()}已添加模型 {Fore.CYAN}{name}{Style.RESET_ALL}")

    elif action == "set" and len(args) >= 3:
        role = args[1].lower()
        model_name = args[2]
        valid_roles = ["coder", "leader", "tester", "chatter", "icon_designer"]
        if role not in valid_roles:
            print(f"{prefix()}{Fore.RED}角色必须是: {', '.join(valid_roles)}{Style.RESET_ALL}")
            return
        cfg.setdefault("role_model_override", {})[role] = model_name
        _save_config(cfg)
        print(f"{prefix()}{Fore.LIGHTYELLOW_EX}{role}{Style.RESET_ALL} 将使用模型 {Fore.CYAN}{model_name}{Style.RESET_ALL}")

    elif action == "list":
        extras = cfg.get("extra_models", {})
        if not extras:
            print(f"{prefix()}暂无额外模型")
        else:
            print(f"{prefix()}{Style.BRIGHT}已添加的模型:{Style.RESET_ALL}")
            for name, info in extras.items():
                if isinstance(info, dict):
                    print(f"  {Fore.CYAN}{name}{Style.RESET_ALL}: {info.get('base_url', '')}")
                else:
                    print(f"  {Fore.CYAN}{name}{Style.RESET_ALL}")

    elif action == "remove" and len(args) >= 2:
        name = args[1]
        extras = cfg.get("extra_models", {})
        if name in extras:
            del extras[name]
            _save_config(cfg)
            print(f"{prefix()}已移除模型 {Fore.CYAN}{name}{Style.RESET_ALL}")
        else:
            print(f"{prefix()}{Fore.RED}模型 {name} 不存在{Style.RESET_ALL}")
    else:
        _print_model_usage()


def _handle_danger(args, cfg):
    if not args:
        _print_danger_usage()
        return
    action = args[0].lower()

    if action == "add" and len(args) >= 2:
        cmd = " ".join(args[1:])
        dangers = cfg.setdefault("dangerous_commands", [])
        if cmd not in dangers:
            dangers.append(cmd)
            _save_config(cfg)
            print(f"{prefix()}已添加危险命令: {Fore.RED}{cmd}{Style.RESET_ALL}")
        else:
            print(f"{prefix()}{Fore.YELLOW}该命令已在列表中{Style.RESET_ALL}")

    elif action == "list":
        dangers = cfg.get("dangerous_commands", [])
        if not dangers:
            print(f"{prefix()}危险命令列表为空")
        else:
            print(f"{prefix()}{Style.BRIGHT}危险命令列表:{Style.RESET_ALL}")
            for i, cmd in enumerate(dangers, 1):
                print(f"  {Fore.RED}{i}.{Style.RESET_ALL} {cmd}")

    elif action == "remove" and len(args) >= 2:
        cmd = " ".join(args[1:])
        dangers = cfg.get("dangerous_commands", [])
        if cmd in dangers:
            dangers.remove(cmd)
            _save_config(cfg)
            print(f"{prefix()}已移除: {cmd}")
        else:
            print(f"{prefix()}{Fore.RED}未找到该命令{Style.RESET_ALL}")
    else:
        _print_danger_usage()


def _print_usage():
    print(f"{prefix()}可用子命令:")
    print(f"  {Fore.GREEN}config show{Style.RESET_ALL}                    查看配置")
    print(f"  {Fore.GREEN}config mode quality|saving{Style.RESET_ALL}     设置模式")
    print(f"  {Fore.GREEN}config loops <1-10>{Style.RESET_ALL}            设置循环次数")
    print(f"  {Fore.GREEN}config model add|set|list|remove{Style.RESET_ALL}")
    print(f"  {Fore.GREEN}config danger add|list|remove{Style.RESET_ALL}")
    print(f"  {Fore.GREEN}config url set|list|remove{Style.RESET_ALL}     角色独立 base_url")


def _print_model_usage():
    print(f"{prefix()}用法:")
    print(f"  {Fore.GREEN}config model add <名称> <base_url> <api_key>{Style.RESET_ALL}")
    print(f"  {Fore.GREEN}config model set <角色> <模型名>{Style.RESET_ALL}")
    print(f"  {Fore.GREEN}config model list{Style.RESET_ALL}")
    print(f"  {Fore.GREEN}config model remove <名称>{Style.RESET_ALL}")


def _print_danger_usage():
    print(f"{prefix()}用法:")
    print(f"  {Fore.GREEN}config danger add <命令>{Style.RESET_ALL}")
    print(f"  {Fore.GREEN}config danger list{Style.RESET_ALL}")
    print(f"  {Fore.GREEN}config danger remove <命令>{Style.RESET_ALL}")


def _handle_url(args, cfg):
    """处理角色独立 base_url 配置"""
    if not args:
        _print_url_usage()
        return
    action = args[0].lower()
    valid_roles = ["coder", "leader", "tester", "chatter", "icon_designer"]

    if action == "set" and len(args) >= 3:
        role = args[1].lower()
        url = args[2]
        if role not in valid_roles:
            print(f"{prefix()}{Fore.RED}角色必须是: {', '.join(valid_roles)}{Style.RESET_ALL}")
            return
        cfg.setdefault("role_base_urls", {})[role] = url
        _save_config(cfg)
        print(f"{prefix()}{Fore.LIGHTYELLOW_EX}{role}{Style.RESET_ALL}"
              f" base_url 已设为 {Fore.CYAN}{url}{Style.RESET_ALL}")

    elif action == "list":
        urls = cfg.get("role_base_urls", {})
        if not urls:
            print(f"{prefix()}暂无角色独立 base_url 配置")
        else:
            print(f"{prefix()}{Style.BRIGHT}角色 base_url 配置:{Style.RESET_ALL}")
            for role, url in urls.items():
                print(f"  {Fore.LIGHTYELLOW_EX}{role:<16}{Style.RESET_ALL}"
                      f" → {Fore.CYAN}{url}{Style.RESET_ALL}")

    elif action == "remove" and len(args) >= 2:
        role = args[1].lower()
        urls = cfg.get("role_base_urls", {})
        if role in urls:
            del urls[role]
            _save_config(cfg)
            print(f"{prefix()}已移除 {Fore.LIGHTYELLOW_EX}{role}{Style.RESET_ALL} 的独立 base_url")
        else:
            print(f"{prefix()}{Fore.RED}{role} 没有独立 base_url 配置{Style.RESET_ALL}")
    else:
        _print_url_usage()


def _print_url_usage():
    print(f"{prefix()}用法:")
    print(f"  {Fore.GREEN}config url set <角色> <base_url>{Style.RESET_ALL}  设置角色独立 URL")
    print(f"  {Fore.GREEN}config url list{Style.RESET_ALL}                   查看所有角色 URL")
    print(f"  {Fore.GREEN}config url remove <角色>{Style.RESET_ALL}          移除角色独立 URL")
