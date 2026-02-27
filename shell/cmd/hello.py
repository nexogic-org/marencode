import random
from colorama import Fore, Style, Back
from shell.cmd import prefix
from datetime import datetime

def run():
    # prefix() 已经包含了一只猫 (ᓚᘏᗢ)，所以这里不需要再手动打印猫了
    # 我们只打印问候语
    
    greetings = [
        f"{Fore.CYAN}Hello, developer! Ready to write some clean code?{Style.RESET_ALL}",
        f"{Fore.GREEN}Hi there! Maren Code is at your service.{Style.RESET_ALL}",
        f"{Fore.MAGENTA}Greetings! Let's solve some problems today.{Style.RESET_ALL}",
        f"{Fore.BLUE}Salutations! Your CLI companion is online.{Style.RESET_ALL}",
        f"{Fore.YELLOW}Howdy! Hope your coffee is strong and your bugs are few.{Style.RESET_ALL}",
        f"{Fore.LIGHTBLUE_EX}Bonjour! Creativity awaits.{Style.RESET_ALL}",
        f"{Style.BRIGHT}{Fore.WHITE}System operational. Waiting for your command.{Style.RESET_ALL}",
        f"{Fore.LIGHTRED_EX}Let's build something awesome together!{Style.RESET_ALL}"
    ]
    
    # 获取当前时间段
    hour = datetime.now().hour
    time_msg = ""
    if 5 <= hour < 12:
        time_msg = f"{Fore.LIGHTYELLOW_EX}Good morning!{Style.RESET_ALL}"
    elif 12 <= hour < 18:
        time_msg = f"{Fore.LIGHTCYAN_EX}Good afternoon!{Style.RESET_ALL}"
    elif 18 <= hour < 22:
        time_msg = f"{Fore.LIGHTMAGENTA_EX}Good evening!{Style.RESET_ALL}"
    else:
        time_msg = f"{Fore.BLUE}Burning the midnight oil?{Style.RESET_ALL}"

    print(f"{prefix()} {time_msg}")
    print(f"{prefix()} {random.choice(greetings)}")
