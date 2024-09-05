#!/usr/bin/env python
# coding=utf-8
# winexec=python

#@ Introduction
# The script provides an interface for executing various unittest cases of rdee-python
#    ● Support filtering
#@

import sys
import os
import glob
import shutil
import unittest
import functools
import inspect
import fnmatch
import logging

from ._o_funcs import load_module_from_path
from ._o_logging import fastLogger

def parameterized_UTMethod(params, use_subtest: bool = True):
    """
    Last Update: @2024-08-06 17:09:08
    -------------------------------------
    This function is a decorator for unittest test-methods

    :param params:          should be like [(eles, dict)], i.e., only have one dict for kwargs-style arguments
    :param use_subtest:     if use subtest or not
    """

    #@ nested-decorator-function
    def decorator(func):
        """
        True decorator, i.e., accepting only arg::func
        """

        #@ branch:subtest | use subtest for groups of parameters
        @functools.wrap(func)
        def wrapper(self):
            for p in params:
                args, kwargs = [], {}
                for ele in p:
                    if isinstance(ele, dict):
                        kwargs.update(ele)
                    else:
                        args.append(ele)

                with self.subTest(param_set=p):
                    func(self, *args, **kwargs)

        if use_subtest:
            return wrapper

        #@ branch:injection | inject different testcases with individual parameter into TestCase class
        clslocal = inspect.currentframe().f_back.f_locals

        for i_p, p in enumerate(params):
            args, kwargs = [], {}
            for ele in p:
                if isinstance(ele, dict):
                    kwargs.update(ele)
                else:
                    args.append(ele)

            #@ .closure | use closure auxiliary function to encapsulate test-method with specific arguments
            def make_pfunc(args, kwargs):
                def pfunc(self):
                    return func(self, *args, **kwargs)
                return pfunc

            test_name = f"{func.__name__}_{i_p+1}"

            #@ .inject
            clslocal[test_name] = make_pfunc(args, kwargs)

    return decorator


class IFixture:
    """
    Interface class implementing general setUpClass & setUp methods for the belowing TestCases
    """
    @classmethod
    def setUpClass(cls) -> None:
        cls.testDir: str = os.path.abspath(cls.__name__[5:])

        if os.path.exists(cls.testDir):
            shutil.rmtree(cls.testDir)
        os.makedirs(cls.testDir)
        os.chdir(cls.testDir)

        print(f"\n\n\n\033[38;5;227m***************************************************")
        print(f"TestCase: {cls.__name__[5:]}")
        print(f"***************************************************\033[0m")

    @classmethod
    def tearDownClass(cls) -> None:
        os.chdir(cls.testDir + "/..")
        if not os.getenv("UTEST_KEEP"):
            shutil.rmtree(cls.testDir)

    def setUp(self) -> None:
        """
        print start information via puer print()
        &
        prepare test directory and enter it
        """

        # mid = '.'.join(self.id().split(".")[-2:])
        mid = self.id().split(".")[-1]

        print(f"\n\n\033[38;5;155m>>>>> test method: {mid} <<<<<\033[0m")
        
        #@sk <get-path/>
        os.chdir(self.__class__.testDir)
        _, funcname = self.id().split(".")[-2:]
        self.testDir: str = f"{funcname[5:]}"

        #@sk <os-operation desc="mkdir -> rm -rf -> cd, and store the current working directory"/>
        if os.path.exists(self.testDir):
            shutil.rmtree(self.testDir)
        os.makedirs(self.testDir)
        os.chdir(self.testDir)


def dotest(targets: list[str], test_directory: str = ".") -> None :
    """
    Last Update: @2024-08-29 10:44:18
    ---------------------------------
    This function aims to execute target unit tests with easy selection
    Target specification rules:
        - SuiteName
        - MethodName
        - SuiteName.MethodName
    Each part can neglect the test_/Test_ prefix and use fnmatch
    For example:
        - python -m rdee utest -d ../utest OS       # will trigger Test_OS.test_shrun
        - python -m rdee utest -d ../utest *Logger  # will trigger Test_Logging.test_getLogger and Test_Logging.test_fastLogger

    :param targets: a list of to-be-tested targets, from positional command-line-arguments for subparser utest
    :param test_directory: specifying directory containing valid test[._]*.py scripts
    """
    #@ Prepare
    logger = fastLogger("dotest", "LOGLEVEL_DOTEST")


    #@ Main
    #@ .get-files | Search potential test files and import as modules
    logger.info("Searching test scripts")
    testfiles = glob.glob(f"{test_directory}/test[._]*.py")
    if not testfiles:
        logger.warn(f"Warning! Cannot find python scripts with test[._] prefix in {test_directory}")
        return
    logger.debug(f"valid test scripts: {testfiles}")

    #@ .load-files | import found test scripts into modules, via load_module_from_path
    logger.info("Loading test scripts")
    modules = []
    for tf in testfiles:
        try:
            modules.append(load_module_from_path(tf))
        except:
            logger.fatal(f"Failed to load {tf}")
            raise
    
    #@ .get-all-CFs | get all TestCases and TestFunctions from loaded modules
    logger.info("Parsing loaded modules")
    allTestCases = {}
    allTestFunctions = {}
    for m in modules:
        for name, obj in m.__dict__.items():
            if inspect.isclass(obj) and issubclass(obj, unittest.TestCase):
                allTestCases[name] = obj

    for tcn, tc in allTestCases.items():
        for method_name in dir(tc):
            if method_name.startswith("test_"):
                allTestFunctions[f"{tcn}.{method_name}"] = (tc, method_name)
    logger.debug(f"allTestCases contains:{','.join(allTestCases.keys())}")
    logger.debug(f"allTestFunctions contains:{','.join(allTestFunctions.keys())}")

    #@ .filter | filter CFs via based on targets
    logger.info("Filtering targets")
    targetTCs: list[str] = []
    targetTMs: list[str] = []
    for target in targets:
        if "." in target:
            tcn, tmn = target.split('.')
            if not (tcn.startswith("*") or tcn.startswith("Test_")):
                tcn = "Test_" + tcn
            if not (tmn.startswith("*") or tmn.startswith("test_")):
                tmn = "test_" + tmn
            tms = fnmatch.filter(list(allTestFunctions.keys()), f"{tcn}.{tmn}")
            targetTMs.extend(tms)
            if not tms:
                logger.warn(f"Cannot find corresponding test functions for {target=}")
        else:
            if not (target.startswith("*") or target.startswith("Test_")):
                tcn = "Test_" + target
            else:
                tcn = target
            tcs = fnmatch.filter(list(allTestCases.keys()), tcn)
            targetTCs.extend(tcs)

            if not (target.startswith("*") or target.startswith("test_")):
                tmn = "test_" + target
            else:
                tmn = target
            tms = fnmatch.filter(list(allTestFunctions.keys()), f"*.{tmn}")
            targetTMs.extend(tms)

            if not targetTCs and not targetTMs:
                logger.warn(f"Cannot find corresponding test functions for {target=}")

    if not targets:
        logger.info("  no targets specified, take all CFs")
        targetTCs = list(allTestCases.keys())

    targetTCs_uniq = set(targetTCs)
    targetTMs_uniq = set(targetTMs)
    logger.debug(f"target TestCases contains: {targetTCs_uniq}")
    logger.debug(f"target TestMethods contains: {targetTMs_uniq}")
    if not targetTCs_uniq and not targetTMs_uniq:
        logger.error("No valid targets after filtering, check your filter!")
        return

    #@ .run-unittest | create suite, loader and runner, then load targetTCs & targetTMs, finally run it
    logger.info("Running tests")
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    runner = unittest.TextTestRunner()

    for tc in targetTCs_uniq:
        suite.addTests(loader.loadTestsFromTestCase(allTestCases[tc]))
    for tm in targetTMs_uniq:
        tcn, tmn = tm.split(".")
        if tcn in targetTCs_uniq:
            continue
        suite.addTest(allTestCases[tcn](tmn))

    rst = runner.run(suite)
    if not rst.wasSuccessful():
        sys.exit(101)
