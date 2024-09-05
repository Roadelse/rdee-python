# coding=utf-8

import sys
import os
import unittest
import logging
import shutil

sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))
from rdee._o_logging import getLogger, fastLogger, resetLogger, rmLogger
from rdee import utest


class Test_LOGGING(utest.IFixture, unittest.TestCase):
    """
    This class contains several test functions in relation with logging
    """
    # def tearDown(self) -> None:
    #     """
    #     Go back to original workding directory
    #     """
    #     print("\n\n\n")

    def test_getLogger(self):
        """
        Get logger with config file
        """

        #@sk prepare write a local logging.config
        with open("logging.config", "w") as f:
            f.write("""
[loggers]
keys=root,test1

[handlers]
keys=console1,file1

[formatters]
keys=fmtfile,fmtcsl

[filters]
keys=ft1

[logger_root]
level=INFO
handlers=console1
qualname=root

[logger_test1]
level=DEBUG
handlers=file1
qualname=test1
; if set to 0, test1 logger will not trigger root logger handlers
propagate=1

[handler_console1]
class=StreamHandler
level=DEBUG
formatter=fmtcsl
args=(sys.stdout,)

[handler_file1]
class=logging.handlers.RotatingFileHandler
level=DEBUG
formatter=fmtfile
args=('test1.log', 'a', 20000, 5)

[formatter_fmtfile]
format=%(asctime)s  (%(name)s)  [%(levelname)s]  %(message)s
datefmt=%Y-%m-%d %H:%M:%S

[formatter_fmtcsl]
format=\033[4m%(asctime)s \033[0m (\033[33m%(funcName)s\033[0m)  [\033[32m%(levelname)s\033[0m]  %(message)s
datefmt=%Y-%m-%d %H:%M:%S

""")

        #@sk prepare remove the getLogger.configured so it can load the created local config file
        if hasattr(getLogger, "configured"):
            delattr(getLogger, "configured")

        #@sk <do desc="do the core statements">
        #@sk <basic desc="test basic functionality" />
        logger = getLogger("root")
        logger1 = getLogger("test1")
        logger2 = getLogger("test2", fpath="test2.log")
        logger.info("info from root")
        logger1.info("info from test1")
        logger2.info("info from test2")
        #@sk <envfilter desc="test envfilter" />
        logger1.info("2nd info from test1")
        logger2.info("2nd info from test2")
        #@sk </do>

        #@sk check
        self.assertTrue(os.path.exists("test1.log"))
        self.assertTrue(os.path.exists("test2.log"))

        self.assertEqual(2, len(open("test1.log").readlines()))
        self.assertEqual(2, len(open("test2.log").readlines()))

        resetLogger(logger)
        resetLogger(logger1)
        resetLogger(logger2)


    def test_logFilter(self):
        """
        Set env:reDebugTargets to debug selective targets
        """
        os.environ["PYTHON_LLSPEC_COMMA"] = "f2=Debug,f1=info"  #@ exp | Must be set prior to getLogger function call (@2024-08-29 23:30:33)
        logger = getLogger("temp", fpath="test_logFilter.log")  #@ exp | name is "root" by default
        def f1():
            logger.debug("in f1")
        
        def f2():
            logger.debug("in f2")

        # logger.addHandler(logging.FileHandler("test_logFilter.log"))
        f1()
        f2()
        with open("test_logFilter.log") as f:
            # self.assertEqual("in f2\n",  f.read())
            content = f.read()
        
        self.assertIn("in f2", content)
        self.assertNotIn("in f1", content)

        resetLogger(logger)

    def test_fastLogger(self):
        """
        Just ensure no errors
        """
        logger = fastLogger("test_fastLogger")
        logger.info("nothing")

        os.environ["LLTEMP1"] = "debug"
        logger2 = fastLogger("test_fastLogger_2", "LLTEMP1")
        logger2.debug("aha")
        resetLogger(logger)
        resetLogger(logger2)

    def test_resetLogger(self):
        logger1 = getLogger("test_resetLogger", fpath="a.log")
        self.assertEqual(2, len(logger1.handlers))
        resetLogger(logger1)
        self.assertEqual(0, len(logger1.handlers), str(logger1.handlers))

    def test_rmLogger(self):
        loggerDict = logging.Logger.manager.loggerDict
        logger1 = getLogger("test_rmLogger", fpath="a.log")
        self.assertTrue("test_rmLogger" in loggerDict)
        rmLogger("test_rmLogger")
        self.assertTrue("test_rmLogger" not in loggerDict)
        logger2 = getLogger("test_rmLogger", fpath="a.log")
        self.assertNotEqual(id(logger1), id(logger2))
        resetLogger(logger2)




