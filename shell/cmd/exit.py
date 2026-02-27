from colorama import init, Fore, Style
import sys
from shell.cmd import prefix

def run():
    init(autoreset=True)
    print(f"{prefix()}{Style.BRIGHT}{Fore.YELLOW}Bye. Exiting Maren CLI.")
    sys.exit(0)
