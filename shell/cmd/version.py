from colorama import init, Fore, Style
import constants
from shell.cmd import prefix

def run():
    init(autoreset=True)
    banner = f"{Style.BRIGHT}{Fore.YELLOW}Maren Code"
    ver = f"{Style.BRIGHT}{Fore.GREEN}{constants.VERSION}"
    print(f"{prefix()}{banner} {Fore.YELLOW}Version: {ver}")
