#!/usr/bin/env python3
# coding=utf-8

"""
Last Update: @2024-08-30 11:22:01
---------------------------------
This module extends python's standard logging module, mainly for getLogger encapsulation with EnvFilter.
Besides, some useful functions are provided as well

@Roadelse
"""

#@ import
import os.path
import sys
import logging
import json
#@


def getAllHandlers(lgr: logging.Logger) -> list[logging.Handler]:
    """
    Last Update: @2024-08-30 11:23:32
    ---------------------------------
    This function aims to get all handlers for given logger, via go through all its ancestor loggers
    Since log context will be transported to all its ancestor loggers

    :param lgr: logging.Logger instance
    """
    rstList: list[logging.Handler] = []
    while lgr is not None:
        rstList.extend(lgr.handlers)
        lgr = lgr.parent
    return rstList


def has_stdout_handler(lgr: logging.Logger) -> bool:
    """
    Last Update: @2024-08-30 14:50:48
    ---------------------------------
    This function aims to check if a logger has a stdout StreamHandler
    """
    ahs: list[logging.Handler] = getAllHandlers(lgr)  #@| ahs -> AllHandlerS
    for h in ahs:
        if isinstance(h, logging.StreamHandler) and h.stream is sys.stdout:
            return True
    return False



class ColorFormatter(logging.Formatter):
    """
    Last Update: @2024-08-30 14:51:26
    ---------------------------------
    Colorful format for logging text

    reference: from https://stackoverflow.com/questions/384076/how-can-i-color-python-logging-output
    """

    FORMATS = {
        logging.DEBUG: "\033[38;5;51m%(name)s:\033[0m \033[4m%(asctime)s\033[0m (\033[1m%(filename)s:%(lineno)d | %(funcName)s\033[0m) [%(levelname)s] %(message)s",
        logging.INFO: "\033[38;5;51m%(name)s:\033[0m \033[4m%(asctime)s\033[0m (\033[1m%(filename)s:%(lineno)d | %(funcName)s\033[0m) \033[36m[%(levelname)s]\033[0m %(message)s",
        logging.WARNING: "\033[38;5;51m%(name)s:\033[0m \033[4m%(asctime)s\033[0m (\033[1m%(filename)s:%(lineno)d | %(funcName)s\033[0m) \033[33m[%(levelname)s]\033[0m %(message)s",
        logging.ERROR: "\033[38;5;51m%(name)s:\033[0m \033[4m%(asctime)s\033[0m (\033[1m%(filename)s:%(lineno)d | %(funcName)s\033[0m) \033[31m[%(levelname)s]\033[0m %(message)s",
        logging.CRITICAL: "\033[38;5;51m%(name)s:\033[0m \033[4m%(asctime)s\033[0m (\033[1m%(filename)s:%(lineno)d | %(funcName)s\033[0m) \033[31;1m[%(levelname)s]\033[0m %(message)s"
    }

    def format(self, record):  #@| required method for class logging.Formatter
        log_fmt = self.FORMATS.get(record.levelno)
        date_format = "%Y-%m-%d %H:%M:%S"
        formatter = logging.Formatter(log_fmt, datefmt=date_format)
        return formatter.format(record)


class EnvFilter(logging.Filter):
    """
    Last Update: @2024-08-30 14:52:38
    ---------------------------------

    This class provides a subclass of logging.Filter, aiming to set logging level by functions.
    It stores the logger instance for retrieving llspec afterwards.
    Don't consider top-level log by now
    """
    def __init__(self, logger: logging.Logger):
        super().__init__()
        self.logger: logging.Logger = logger

    def filter(self, record: logging.LogRecord) -> bool:
        if record.levelno >= logging.WARNING:
            return True
        llspec = self.logger.llspec

        baselevel = logging.INFO if "base" not in llspec else llspec["base"]
        if record.funcName in llspec:
            return record.levelno >= llspec[record.funcName]
        else:
            return record.levelno >= baselevel

def fastLogger(name="root", level: str|int|None = None):
    """
    Last Update: @2024-08-29 22:18:39
    ---------------------------------
    This function aims to retrieve a logger in a faster way, which would always contain a file handler with color formatter
    However, it still supports level specification via v2ll, i.e., supporting environment control

    :param name: logger name
    :param level: used to set level via func:v2ll
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        _level = v2ll(level)
        logger.setLevel(_level)

        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(ColorFormatter())
        logger.addHandler(sh)
    return logger


def v2ll(v: str|int|None) -> int:
    """
    Last Update: @2024-08-29 20:57:20
    ---------------------------------
    This function parses a more felxible varible to logging Level
    """
    if v is None:
        return logging.INFO
    
    if isinstance(v, int):
        return v

    if isinstance(v, str):
        vU = v.upper()
        if vU.startswith("INFO"):
            return logging.INFO
        if vU.startswith("DEBUG"):
            return logging.DEBUG
        if vU.startswith("WARN"):
            return logging.WARNING
        if vU.startswith("ERROR"):
            return logging.ERROR
        if vU.startswith("FATAL"):
            return logging.FATAL
        envval = os.getenv(v)
        if envval:
            return v2ll(envval)
        
        return logging.INFO
        # raise TypeError(f"Error! Unkown value for log-level string: {v}")
    
    raise TypeError(f"Error! Unkown value for log-level type: {type(v)}")


def getLogger(name, configfile: str = "logging.config", clevel = logging.NOTSET, flevel = logging.NOTSET, fpath: str = "", propagate: bool = True) -> logging.Logger:
    """
    Last Update: @2024-08-30 14:58:48
    ---------------------------------
    
    This function aims to get a logging.Logger according to arg:name, after loading local selected/default config file.
    It generally supports 3 ways of customizing a logger
        1. fileConfig, the same as STL logging functionality
        2. EnvFilter, supporting specifying logging level via environment variable, i.e., direct commands or a json file
        3. default, set logging levels via function arguments
    
    Unit test in ../../utest
        * python -m rdee utest getLogger
    
    ---------------------------------
    :param name: target name for logger
    :param configfile: local config file path
    :param clevel: used to set console handler level during initializing a new logger 
    :param flevel: used to set file handler level during initializing a new logger   
    :param fpath: used to set logfile path for file handler during initializing a new logger 

    :return: a logging.Logger
    """
    import logging.config

    #@sk <inner-functions>
    #@sk <config desc="load local configfile"/>
    def config():
        if os.path.exists(configfile):
            logging.config.fileConfig(configfile)


    def get_llspec():
        jsf = os.getenv("PYTHON_LLSPEC_JSON")
        llspec = None
        if jsf:
            with open(jsf) as f:
                llspec = json.load(f)
        else:
            spec_commas = os.getenv("PYTHON_LLSPEC_COMMA")
            if spec_commas:
                llspec = dict(item.split("=") for item in spec_commas.split(","))
        
        if llspec:
            llspec = {k:v2ll(v) for k,v in llspec.items()}
        
        return llspec

    #@sk <once-through desc="load local config file"/>
    if not hasattr(getLogger, "configured"):
        config()
        setattr(getLogger, "configured", 1)

    #@sk <core desc="get logger, set logger">
    logger: logging.Logger = logging.getLogger(name)
    if logger.handlers:  #@sk branch return if logger has been configured in local config or last call
        return logger
    
    logger.setLevel(logging.DEBUG)
    logger.llspec = get_llspec()
    if logger.llspec:
        logger.addFilter(EnvFilter(logger))

    #@sk <set-logger desc="setting logger based on arguments" />
    if not has_stdout_handler(logger) and clevel is not None:  #@sk branch set console handler
        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(ColorFormatter())
        sh.setLevel(clevel)
        logger.addHandler(sh)

    if flevel is not None and fpath != "":  #@sk branch set file handler
        fh = logging.FileHandler(fpath)
        fmt = logging.Formatter("%(asctime)s (%(filename)s:%(lineno)d | %(funcName)s) [%(levelname)s] %(message)s")
        fh.setFormatter(fmt)
        fh.setLevel(flevel)
        logger.addHandler(fh)
    
    #@sk </core>

    return logger


def resetLogger(name_or_logger: str|logging.Logger = "root"):
    logger_dict = logging.Logger.manager.loggerDict

    if isinstance(name_or_logger, str):
        name = name_or_logger
        if name != "root" or name not in logger_dict:
            return
        logger = logger_dict[name]
    elif isinstance(name_or_logger, logging.Logger):
        logger = name_or_logger
    else:
        raise TypeError
    

    for handler in logger.handlers:
        handler.close()
    logger.handlers.clear()
    logger.filters.clear()

    logger.setLevel(logging.NOTSET)

def rmLogger(name_or_logger: str|logging.Logger = "root"):
    logger_dict = logging.Logger.manager.loggerDict
    if isinstance(name_or_logger, str):
        name = name_or_logger
        if name == "root":
            resetLogger(name)
            return
        elif name not in logger_dict:
            return
        logger = logger_dict[name]
    elif isinstance(name_or_logger, logging.Logger):
        logger = name_or_logger
        name = logger.name
    else:
        raise TypeError
    
    for handler in logger.handlers:
        handler.close()
    logger.handlers.clear()
    del logger_dict[name]
    del logger