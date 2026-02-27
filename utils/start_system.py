from utils import print_hello_page
from utils import inited
from colorama import init, Fore, Style
from shell import main

def start():
    print_hello_page.print_hello_page()
    if not inited.is_inited():
        init(autoreset=True)
        DIM = Fore.LIGHTBLACK_EX
        ACCENT = '\033[38;5;222m'
        R = Style.RESET_ALL
        print(f"  {Fore.RED}[!]{R} Not initialized. Run {ACCENT}code init boot{R} to set up.")
        print()

    main.main_maren()
