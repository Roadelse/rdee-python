#!/usr/bin/env python3
# coding=utf-8


"""
This module serves as a global variable holder for the rdee package
"""

import platform
import os


system = platform.system()
inWSL, inWSL1, inWSL2 = False, False, False
hasBash = True
if system == "Linux" and os.getenv("WSL_DISTRO_NAME"):
    inWSL = True
    if inWSL:
        if os.getenv("WSL_DISTRO_NAME") == "wsl1":
            inWSL1 = True
        else:
            inWSL2 = True
