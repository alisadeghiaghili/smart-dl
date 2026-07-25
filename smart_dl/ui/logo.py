"""ASCII logo and header/footer display."""
import sys
import shutil
from rich.text import Text
from rich.align import Align
from rich.rule import Rule

from smart_dl import VERSION
from smart_dl.ui import console

LOGO = r"""
 ____                       _   ____  _
/ ___| _ __ ___   __ _ _ __| |_|  _ \| |
\___ \| '_ ` _ \ / _` | '__| __| | | | |
 ___) | | | | | | (_| | |  | |_| |_| | |___
|____/|_| |_| |_|\__,_|_|   \__|____/|_____|
"""


def print_header():
    w = shutil.get_terminal_size(fallback=(120, 24)).columns
    lines = LOGO.strip('\n').split('\n')
    block_w = max(len(l) for l in lines)
    left = " " * max(0, (w - block_w) // 2)
    sys.stdout.write("\n")
    for line in lines:
        sys.stdout.write("\033[96;1m" + left + line + "\033[0m\n")
    sys.stdout.flush()
    console.print(Align(Text("v" + VERSION + "  ·  Smart YouTube & Podcast Downloader  ·  Ctrl+C to stop", style="dim"), align="center"))
    console.print(Align(Text("by Hellch!ef  ·  if u know u know", style="dim italic"), align="center"))
    console.print(Align(Text("\u2615  buymeacoffee.com/alisadeghil", style="bold yellow"), align="center"))
    console.print(Rule(style="cyan"))
    console.print()


def bye():
    console.print()
    console.print(Rule(style="cyan"))
    console.print(Align(Text("bye \u2764", style="bold cyan"), align="center"))
    console.print(Align(Text("\u2615  buymeacoffee.com/alisadeghil", style="bold yellow"), align="center"))
    console.print(Rule(style="cyan"))
    console.print()
