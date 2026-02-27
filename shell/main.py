import sys
from colorama import init, Fore, Style
from shell.cmd import version as version_cmd
from shell.cmd import exit as exit_cmd
from shell.cmd import init as init_cmd
from shell.cmd import chat as chat_cmd
from shell.cmd import skill as skill_cmd
from shell.cmd import hello as hello_cmd
from shell.cmd import run as run_cmd
from shell.cmd import config as config_cmd
from shell.cmd import new as new_cmd
from shell.cmd import status as status_cmd
from shell.cmd import prefix
import utils.inited as inited

def _readline():
    try:
        return input()
    except UnicodeDecodeError:
        try:
            raw = sys.stdin.buffer.readline()
            if raw.startswith(b'\xff\xfe'):
                return raw.decode('utf-16-le', errors='replace').rstrip('\r\n')
            if raw.startswith(b'\xfe\xff'):
                return raw.decode('utf-16-be', errors='replace').rstrip('\r\n')
            enc = getattr(sys.stdin, 'encoding', None) or 'utf-8'
            try:
                return raw.decode(enc, errors='replace').rstrip('\r\n')
            except Exception:
                return raw.decode('utf-8', errors='replace').rstrip('\r\n')
        except Exception:
            return ""
def main_maren():
    init(autoreset=True)
    ACCENT = '\033[38;5;222m'
    R = Style.RESET_ALL
    while True:
        try:
            print(f"{ACCENT}>>{R} ", end="", flush=True)
            command = _readline()
        except KeyboardInterrupt:
            print()
            print(f"{prefix()}{Style.BRIGHT}{Fore.YELLOW}Exiting...{Style.RESET_ALL}")
            sys.exit(0)
            
        if not command:
            continue
            
        parts = command.strip().split()
        if not parts:
            continue
            
        head = parts[0].lower()
        args = parts[1:]
        
        # 允许未初始化时执行的命令白名单
        # 注意：version, exit, help 是安全的
        # code init boot 是初始化入口
        
        is_init_cmd = (head == "init") or (head == "code" and args and args[0].lower() == "init")
        
        # 检查 code <cmd> 形式的白名单
        is_allowed_code_cmd = False
        if head == "code" and args:
            if args[0].lower() in ["version", "exit", "help", "hello"]:
                is_allowed_code_cmd = True

        if not inited.is_inited():
            if not is_init_cmd and not is_allowed_code_cmd and head not in ["version", "exit", "help", "hello"]:
                 print(f"{prefix()}{Style.BRIGHT}{Fore.RED}[ERROR]{Style.RESET_ALL} Maren Code is not initialized.")
                 print(f"{prefix()}Please run {Fore.GREEN}code init boot{Style.RESET_ALL} first.")
                 continue

        if head == "code" and args and args[0].lower() == "chat":
            if len(args) > 1 and args[1].lower() == "enter":
                chat_cmd.enter()
            elif len(args) > 1:
                chat_msg = " ".join(args[1:])
                chat_cmd.run(chat_msg)
            else:
                print(f"{prefix()}Usage: code chat <message> | code chat enter")
        elif head == "chat":
            if not args:
                print(f"{prefix()}Usage: chat <argument>")
            elif args and args[0].lower() == "enter":
                chat_cmd.enter()
            else:
                chat_msg = " ".join(args)
                chat_cmd.run(chat_msg)
        elif head == "version" or (head == "code" and args and args[0].lower() == "version"):
            version_cmd.run()
        elif head == "exit" or (head == "code" and args and args[0].lower() == "exit"):
            exit_cmd.run()
        elif head == "code" and args and args[0].lower() == "init":
            if len(args) > 1:
                 init_cmd.run(args[1:])
            else:
                 print(f"{prefix()}Usage: code init <argument>")
        elif head == "init":
            if args:
                 init_cmd.run(args)
            else:
                 print(f"{prefix()}Usage: init <argument>")
        elif head == "code" and args and args[0].lower() == "skill":
            # code skill list
            if len(args) > 1 and args[1].lower() == "list":
                 skill_cmd.run()
            else:
                 print(f"{prefix()}Usage: code skill <argument>")
        elif head == "skill":
            if args and args[0].lower() == "list":
                skill_cmd.run()
            else:
                print(f"{prefix()}Usage: skill <argument>")
        elif head == "code" and args and args[0].lower() == "run":
            if len(args) > 1:
                run_msg = " ".join(args[1:])
                run_cmd.run(run_msg)
            else:
                print(f"{prefix()}Usage: code run enter")
        elif head == "run":
            if args:
                run_msg = " ".join(args)
                run_cmd.run(run_msg)
            else:
                print(f"{prefix()}请使用 {Fore.GREEN}run enter{Style.RESET_ALL} 进入项目对话模式。")
        elif head == "hello" or (head == "code" and args and args[0].lower() == "hello"):
            hello_cmd.run()
        elif head == "config" or (head == "code" and args and args[0].lower() == "config"):
            if head == "config":
                config_cmd.run(args)
            else:
                config_cmd.run(args[1:])
        elif head == "new" or (head == "code" and args and args[0].lower() == "new"):
            if head == "new":
                if args:
                    new_cmd.run(" ".join(args))
                else:
                    print(f"{prefix()}Usage: new <需求描述>")
            else:
                if len(args) > 1:
                    new_cmd.run(" ".join(args[1:]))
                else:
                    print(f"{prefix()}Usage: code new <需求描述>")
        elif head == "status" or (head == "code" and args and args[0].lower() == "status"):
            status_cmd.run()
        elif head == "help":
             print(f"{prefix()}Available commands:")
             print(f"  {Fore.GREEN}code init boot{Style.RESET_ALL}   Initialize Maren Code")
             print(f"  {Fore.GREEN}new <desc>{Style.RESET_ALL}       Full auto pipeline (Chatter→Leader→Coder→Tester)")
             print(f"  {Fore.GREEN}run enter{Style.RESET_ALL}        Enter project dialog mode")
             print(f"  {Fore.GREEN}chat <msg>{Style.RESET_ALL}       Chat with Maren (one-shot)")
             print(f"  {Fore.GREEN}chat enter{Style.RESET_ALL}       Enter chat mode")
             print(f"  {Fore.GREEN}config{Style.RESET_ALL}           Show/set configuration")
             print(f"  {Fore.GREEN}skill list{Style.RESET_ALL}       List available skills")
             print(f"  {Fore.GREEN}status{Style.RESET_ALL}            Show system status (roles, models, keys)")
             print(f"  {Fore.GREEN}version{Style.RESET_ALL}          Show version")
             print(f"  {Fore.GREEN}hello{Style.RESET_ALL}            Greeting")
             print(f"  {Fore.GREEN}exit{Style.RESET_ALL}             Exit")
        else:
            print(f"{prefix()}{Style.BRIGHT}{Fore.RED}[ERROR]{Style.RESET_ALL} Unknown command: {Fore.YELLOW}{command.strip()}")
        
            
