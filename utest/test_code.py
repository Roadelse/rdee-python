# coding=utf-8

import sys
import os
import unittest
import logging
import shutil
import inspect

sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))
from rdee import utest, code


class Test_PYCODE(utest.IFixture, unittest.TestCase):
    def test_get_imported_names(self):
        """
        Last Update: @2024-08-30 21:19:22
        ---------------------------------
        """
        #@ test-general
        if not code.use_libcst:
            print("Do not possess pycode_* apis in this python environment, skip this test")
            return
        
        pytext = [
            "import sys\nimport shutil, logging as lg",
            "from os import makedirs as mk, system, remove as rm",
            "import importlib.util"
        ]
        names = code.pycode_func.get_imported_names(pytext)
        self.assertSetEqual({"sys", "shutil", "lg", "mk", "system", "rm", "importlib.util"}, set(names))

        #@ test-string-arg
        pytext = "import sys"
        names = code.pycode_func.get_imported_names(pytext)
        self.assertSetEqual({"sys"}, set(names))

    
    def test_pycode_export(self):
        """
        Last Update: @2024-09-06 13:45:55
        ---------------------------------
        """
        if not code.use_libcst:
            print("Do not possess pycode_* apis in this python environment, skip this test")
            return
        
        import rdee
        pynode = code.pycode_module(rdee)
        pynode.export_fcs("a.py", "isinstanceAll")
        moda = rdee.funcs.load_module_from_path("a.py")
        self.assertTrue(inspect.isfunction(moda.isinstanceAll))