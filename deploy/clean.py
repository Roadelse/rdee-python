#!/usr/bin/env python3
# coding=utf-8
# winexec=python

import platform
import sys
import os
import shutil

__filedir__ = os.path.dirname(__file__)


if __name__ == "__main__":
    if platform.system() == "Linux":
        shutil.rmtree(f"{__filedir__}/export.Linux", ignore_errors=True)
    elif platform.system() == "Windows":
        shutil.rmtree(f"{__filedir__}/export.Windows", ignore_errors=True)
    else:
        raise TypeError("Unknown system")
