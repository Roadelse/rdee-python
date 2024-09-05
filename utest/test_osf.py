# coding=utf-8

import sys
import os
import unittest
import logging
import shutil
import platform

sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))
from rdee._o_logging import getLogger, fastLogger
from rdee import utest, state
from rdee._o_osf import shrun, FileOP


class Test_OSH(utest.IFixture, unittest.TestCase):
    def test_shrun(self):
        rcode, rst = shrun("echo 'hello'")
        self.assertEqual("hello" if platform.system() == "Linux" else "'hello'", rst)
        self.assertEqual(0, rcode)

        rcode, rst = shrun("echo 'hello'", logfile="ade.txt")
        self.assertEqual("", rst)
        self.assertEqual(0, rcode)
        with open("ade.txt", "r") as f:
            self.assertEqual("hello\n" if platform.system() == "Linux" else "'hello'\n", f.read())
        
        if state.inWSL or state.system == "Windows":
            rcode, rst = shrun("echo hello", "pwsh")
            self.assertEqual("hello", rst)
            self.assertEqual(0, rcode)

            rcode, rst = shrun("echo 'hello'", "cmd")
            self.assertEqual("'hello'", rst)
            self.assertEqual(0, rcode)
    

class Test_FILEOP(utest.IFixture, unittest.TestCase):
    def test_update_block(self):
        with open("base.py", "w") as f:
            f.write("123\n456\n789\n101\n\n")
        with open("ra.py", "w") as f:
            f.write("""123\n000\n789""")

        FileOP.update_block("base.py", "ra.py")
        baseContent = open("base.py", encoding="utf-8").read()
        self.assertEqual(baseContent, "123\n000\n789\n101\n\n")

        s2 = "789\n103\n\n"
        FileOP.update_block("base.py", s2)
        baseContent = open("base.py", encoding="utf-8").read()
        self.assertEqual(baseContent, "123\n000\n789\n103\n\n")
