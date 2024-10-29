#!/usr/bin/env python3
# coding=utf-8
# winexec=python

import sys
import os
__filedir__ = os.path.dirname(__file__)
try:
    sys.path.append(f"{__filedir__}/../../rdee-core/deploy/tools")
    import deployer
except:
    from tools import deployer


if __name__ == "__main__":
    projname = os.path.abspath(os.path.join(__filedir__, ".."))
    deployer.main(projname)
