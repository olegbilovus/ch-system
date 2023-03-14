import sys
import os

from pathlib import Path
from dotenv import load_dotenv


def setup():
    load_dotenv()

    modules = [Path('../utility'), Path('../database')]

    for module in modules:
        if module not in sys.path:
            sys.path.insert(0, str(module))
            print(f'Added {module} to sys.path')


setup()
