import os

__author__ = "Alexander Rusakevich"

CURR_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

__version__ = (
    open(os.path.join(CURR_SCRIPT_DIR, "VERSION.txt"), "r", encoding="utf8")
    .read()
    .strip()
)
