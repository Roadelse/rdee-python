#!/usr/bin/env python3
# coding=utf-8

# this file contains some useful functions which are commonly used by myself
# rdee - roadelse

"""
rdee python package, within repository rdeeToolkit

This personal custom package is incubated and extended during my daily research, work and life.
It contains several components, which are arranged via MUEXO protocol.

Author:
    Roadelse - roadelse@qq.com
"""

import os

from . import _o_state as state
from . import _o_funcs as funcs
from . import _o_error as error
from . import _o_logging as logging
from . import _o_osf as osf

from . import _x_utest as utest
from . import _x_code as code

# from ._x_os import rmrf, shrun
# from ._x_string import String   
# from ._x_win import createShortCut, GetShortCut, path2wsl, path2win

# if os.getenv("RDEEDEV"):
#     from rdee.__dev__ import update_jj2
#     update_jj2()

# from ._array import *
# from ._x_time import Time
# from ._xx_redtime import realevel, freetime
# from ._geo import *
# from ._io import *
# from ._code import *
# from ._research import *
# from ._plot import *
# from ._string import *
# from ._oop import *
