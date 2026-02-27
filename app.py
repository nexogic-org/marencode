import sys
from utils import start_system

if __name__ == '__main__':
    try:
        start_system.start()
    except KeyboardInterrupt:
        sys.exit(0)

