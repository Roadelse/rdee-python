#!/usr/bin/env python3
# coding=utf-8

"""
This module contains functions serving logging during script running
"""

#@sk <import>
import os.path
import sys
import logging
import logging.config
#@sk </import>


def getAllHandlers(lgr: logging.Logger) -> list[logging.Handler]:
    """
    This function aims to get all handlers for given logger, via go through all its ancestor loggers
    """
    rstList: list[logging.Handler] = []
    while lgr is not None:
        rstList.extend(lgr.handlers)
        lgr = lgr.parent
    return rstList


def has_stdout_handler(lgr: logging.Logger) -> bool:
    """
    This function aims to check if a logger has a stdout StreamHandler
    """
    ahs: list[logging.Handler] = getAllHandlers(lgr)
    for h in ahs:
        if isinstance(h, logging.StreamHandler) and h.stream is sys.stdout:
            return True
    return False



class ref_ColorFormatter(logging.Formatter):
    """
    from https://stackoverflow.com/questions/384076/how-can-i-color-python-logging-output
    """
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)



class ColorFormatter(logging.Formatter):
    """
    @2024-07-05 15:42:04
    """

    FORMATS = {
        logging.DEBUG: "\033[4m%(asctime)s\033[0m (\033[1m%(filename)s:%(lineno)d | %(funcName)s\033[0m) [%(levelname)s] %(message)s",
        logging.INFO: "\033[4m%(asctime)s\033[0m (\033[1m%(filename)s:%(lineno)d | %(funcName)s\033[0m) \033[36m[%(levelname)s]\033[0m %(message)s",
        logging.WARNING: "\033[4m%(asctime)s\033[0m (\033[1m%(filename)s:%(lineno)d | %(funcName)s\033[0m) \033[33m[%(levelname)s]\033[0m %(message)s",
        logging.ERROR: "\033[4m%(asctime)s\033[0m (\033[1m%(filename)s:%(lineno)d | %(funcName)s\033[0m)  \033[31m[%(levelname)s]\033[0m %(message)s",
        logging.CRITICAL: "\033[4m%(asctime)s\033[0m (\033[1m%(filename)s:%(lineno)d | %(funcName)s\033[0m) \033[31;1m[%(levelname)s]\033[0m %(message)s"
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        date_format = "%Y-%m-%d %H:%M:%S"
        formatter = logging.Formatter(log_fmt, datefmt=date_format)
        return formatter.format(record)


def fastLogger(name="root", level=logging.INFO):
    """
    @2024-07-05 15:35:43
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(level)
        sh = logging.StreamHandler(sys.stdout)
        # fmt = logging.Formatter("\033[4m%(asctime)s\033[0m  (\033[1m%(filename)s:%(lineno)d | %(funcName)s\033[0m) [%(levelname)s] - %(message)s")
        sh.setFormatter(ColorFormatter())
        # sh.setLevel(level)
        logger.addHandler(sh)
    return logger



def getLogger(name, configfile: str = "logging.config", clevel = logging.NOTSET, flevel = logging.NOTSET, fpath: str = "", propagate: bool = True) -> logging.Logger:
    """
    This function aims to get a logging.Logger according to arg:name, after loading local selected/default config file.
    :param name: target name for logger
    :param configfile: local config file path
    :param clevel: used to set console handler level during initializing a new logger 
    :param flevel: used to set file handler level during initializing a new logger   
    :param fpath: used to set logfile path for file handler during initializing a new logger 

    :return: a logging.Logger
    """

    #@sk <inner-functions>
    #@sk <config desc="load local configfile"/>
    def config():
        if os.path.exists(configfile):
            logging.config.fileConfig(configfile)

    #@sk <envfilter desc="add default environment filter"/>
    def envfilter(record: logging.LogRecord) -> bool:
        if record.levelno >= logging.WARNING:
            return True
        #@sk <once-through desc="get filter targets in this running"/>
        if not hasattr(envfilter, "targets"):
            targetStr = os.getenv("reDebugTargets")
            if targetStr:
                setattr(envfilter, "targets", targetStr.split(","))
            else:
                setattr(envfilter, "targets", None)

        #@sk <judge desc="judge if record should be filtered based on targets"/>
        targets = getattr(envfilter, "targets")
        if targets is None or "ALL" in targets:
            return True
        else:
            return record.funcName in targets
    #@sk </inner-functions>


    #@sk <once-through desc="load local config file"/>
    if not hasattr(getLogger, "configured"):
        config()
        setattr(getLogger, "configured", 1)

    #@sk <core desc="get logger, set logger">
    logger: logging.Logger = logging.getLogger(name)

    if envfilter not in logger.filters:  #@sk branch add filter at first get
        logger.addFilter(envfilter)
    
    if logger.handlers:  #@sk branch return if logger has been configured in local config or last call
        return logger
    
    #@sk <set-logger desc="setting logger based on arguments" />
    if os.getenv("reDebugTargets") or os.getenv("reDebug"):
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    if not has_stdout_handler(logger) and clevel is not None:  #@sk branch set console handler
        sh = logging.StreamHandler(sys.stdout)
        fmt = logging.Formatter('\033[4m%(asctime)s \033[0m (\033[33m%(funcName)s\033[0m) [\033[32m%(levelname)s\033[0m]  %(message)s', '%Y-%m-%d %H:%M:%S')
        sh.setFormatter(fmt)
        sh.setLevel(clevel)
        logger.addHandler(sh)

    if flevel is not None and fpath != "":  #@sk branch set file handler
        fh = logging.FileHandler(fpath)
        fmt = logging.Formatter('%(asctime)s (%(funcName)s) [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')
        fh.setFormatter(fmt)
        fh.setLevel(flevel)
        logger.addHandler(fh)
    
    #@sk </core>

    return logger

