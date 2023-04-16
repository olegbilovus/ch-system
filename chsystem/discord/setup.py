import os
import sys
from pathlib import Path

from dotenv import load_dotenv


def setup():
    load_dotenv()
    if os.getenv('DB_URI') is not None:
        print('Loaded successfully env variables')
    else:
        sys.exit('Failed to load env variables')

    modules = [Path('../utility'), Path('../database')]

    for module in modules:
        if module not in sys.path:
            sys.path.insert(0, str(module))
            print(f'Added {module} to sys.path')
