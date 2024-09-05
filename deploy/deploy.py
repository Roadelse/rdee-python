#!/usr/bin/env python
# coding=utf-8
# winexec=python

import sys
import os
__filedir__ = os.path.dirname(__file__)
sys.path.append(f"{__filedir__}/../../rdee-core/deploy/tools")
import deployer


if __name__ == "__main__":
    deployer.main()