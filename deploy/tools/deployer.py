#!/usr/bin/env python
# coding=utf-8
# winexec=python


# @ Introduction
# Last Update @2024-10-28 13:22:04
# --------------------------------
# The script aims to deploy rdee-* series toolkits in Linux & Windows

# @ Prepare
# @ .import
# @ ..STL-libs
import platform
import sys
import os
import re
import glob
import argparse
import textwrap
import subprocess
import logging
import json
from typing import Optional, Union


if sys.version_info < (3, 10):
    print(f"This script requires Python version 3.10 or higher (damn simplified union type hint), now is {sys.version_info}")
    sys.exit(1)

__filedir__ = os.path.dirname(__file__)


def deploy(projdir: str, executables: list[str] | str = ""):
    """
    Last Update: @2024-09-04 17:04:01
    ---------------------------------
    This function aims to deploy this software into Linux/Windows environment
    """

    # @ Prepare
    # @ .base-info
    with open(f"{projdir}/VERSION") as f:
        version = f.read().strip()
    temparams = {
        "projdir": projdir,
        "version": version,
        "project": projname,
        "deploydir": deploydir,
        "rehome": args.rehome if args.rehome else os.getenv("HOME")
    }

    logger.debug(f"{executables=}")

    os.chdir(deploydir)

    # @ Core
    if platform.system() == "Linux":
        # @ .Linux
        logger.info(f"in Linux, WSL:{isWSL}")

        exportdir = f"{deploydir}/export.Linux"
        os.makedirs(f"{exportdir}", exist_ok=True)
        temparams["exportdir"] = exportdir

        tplfiles = []

        # @ ..link | link executables into bin
        if executables:
            logger.info("Linking executables")
            if not os.getenv("EXPORT_BIN_DIR"):
                export_bin_dir = f"{exportdir}/bin"
                os.makedirs(export_bin_dir, exist_ok=True)
                os.environ["EXPORT_BIN_DIR"] = export_bin_dir
                tplfiles.append(f"export PATH={export_bin_dir}:$PATH")
            else:
                export_bin_dir = os.getenv("EXPORT_BIN_DIR")
            logger.debug(f"{export_bin_dir=}")

            os.chdir(export_bin_dir)

            if isinstance(executables, str):
                executables = [executables]

            for exe in executables:
                if os.path.isdir(exe):
                    shrun(f"ln -sf {exe}/* .", ensure_noerror=True)
                elif os.path.isfile(exe):
                    shrun(f"ln -sf {exe} .", ensure_noerror=True)
                else:
                    raise UnReachableError
            if os.path.exists("__pycache__"):
                os.remove("__pycache__")
            os.chdir(deploydir)

        # @ ..read-templates | gathering setenv template files
        logger.info("Generating setenv script")
        setenvfile = f"{exportdir}/setenv.{projname}.sh"

        tpldir = f"{projdir}/deploy/template"
        tplfiles.append(f"{tpldir}/template.main.sh")
        if isWSL and os.path.exists(f"{tpldir}/template.wsl.sh"):
            temparams["winuser"] = shrun("echo %USERNAME%", shell="cmd", ensure_noerror=True)[1]
            logger.debug(f"winuser={temparams['winuser']}")
            tplfiles.append(f"{tpldir}/template.wsl.sh")

        if args.withlist:
            with_cmds = []
            for w in args.withlist:
                logger.info(f"  >> Handling additional repo: {w}")
                if os.path.exists(w):
                    deploy_dir_w = os.path.join(w, "deploy")
                else:
                    deploy_dir_w = os.path.abspath(f"{projdir}/../{w}/deploy")
                deploy_script = f"{deploy_dir_w}/deploy.py"
                assert os.path.exists(deploy_script)
                with_cmds.append(shrun(f"{deploy_script} -a -s -o {deploy_dir_w}", ensure_noerror=True)[1])
            with_cmds = [cmd if cmd.rstrip().endswith("load") else cmd + " load" for cmd in with_cmds]
            # print(with_cmds)
            tplfiles.append("\n".join(with_cmds))

        render_setenv_sh_with_revenv(tplfiles, setenvfile, params=temparams, source_only=True)

        # @ ..module | Generate moduelfiles
        if args.module:
            generate_modulefile_from_setenv(f"{exportdir}/modulefiles/{projname}/{version}", setenvfile)

        # @ ..addsource | add source/module statements into target script
        if args.addsource:
            add_source_to_script(exportdir, projname)

    elif platform.system() == "Windows":
        # @ .Windows
        logger.info("in Windows, the options will be ignored: --rehome/-r, --module/-m")

        # @ ..link | link executables into bin
        exportdir = f"{deploydir}\\export.Windows"
        temparams["exportdir"] = exportdir

        os.makedirs(f"{exportdir}", exist_ok=True)
        if executables:
            logger.info("Linking executables")
            os.makedirs(f"{exportdir}/bin", exist_ok=True)
            os.chdir(f"{exportdir}/bin")
            if isinstance(executables, str):
                executables = [executables]
            for exe in executables:
                if os.path.isdir(exe):
                    shrun(f"Get-ChildItem {exe} | ForEach-Object {{ New-Item -ItemType SymbolicLink -Target ($_.FullName) -Path $($_.Name) -Force | Out-Null }}", shell="pwsh", ensure_noerror=True)
                elif os.path.isfile(exe):
                    bname = os.path.basename(exe)
                    shrun(f"New-Item -ItemType SymbolicLink -Target {exe} -Path {bname} -Force | Out-Null", shell="pwsh", ensure_noerror=True)
                else:
                    raise UnReachableError
            os.chdir(deploydir)

        # @ ..setenv | Generate powershell module files
        logger.info("Generating setenv script")
        os.chdir(exportdir)
        if os.path.exists(f"{projdir}\\deploy\\template\\template.main.psm1"):
            use_module = True
            render_file(f"{projdir}\\deploy\\template\\template.main.psm1", f"{projname}.psm1", temparams)
            render_file(f"{projdir}\\deploy\\template\\template.main.psd1", f"{projname}.psd1", temparams)
            envscript = f"{projname}.psm1"
        elif glob.glob(f"{projdir}\\deploy\\template\\template.main.ps1"):
            use_module = False
            render_file(f"{projdir}\\deploy\\template\\template.main.ps1", f"{projname}.ps1", temparams)
            envscript = f"{projname}.ps1"
        else:
            logger.info("No powershell template, return now")

        if args.withlist:
            with open(envscript, "a") as f:
                for w in args.withlist:
                    logger.info(f"  >> Handling additional repo: {w}")
                    if os.path.exists(w):
                        deploy_dir_w = os.path.join(w, "deploy")
                    else:
                        deploy_dir_w = os.path.abspath(f"{deploydir}\\..\\..\\{w}/deploy")
                    deploy_script = f"{deploy_dir_w}\\deploy.py"
                    assert os.path.exists(deploy_script)
                    cmd = shrun(f"python {deploy_script} -a -s -o {deploy_dir_w}", shell="cmd", ensure_noerror=True)[1]
                    f.write(f"\n{cmd}\n")

        # @ ..addsource | Add Import-Module statement into target script
        if args.addsource:
            logger.info("args.addousrce detected")
            if use_module:
                asstr = textwrap.dedent(f"""\
                    # ************************ [{projname}]
                    Import-Module {exportdir}\\{projname}.psd1

                    """)
            else:
                asstr = textwrap.dedent(f"""\
                    # ************************ [{projname}]
                    . {exportdir}\\{projname}.ps1

                    """)
            if args.addsource == "stdout":
                print(asstr)
            else:
                target_script = args.addsource
                logger.debug(f">> Updating statement into {target_script}")
                update_block(target_script, asstr)

    # @ Done
    logger.info("Deployment done")
    return temparams


def render_file(infile: str, ofile: str, params: dict):
    logger.debug(f"rendering {ofile} from template:{infile}, according to {params}")
    assert os.path.exists(infile)

    with open(infile, "r") as f:
        content = f.read()
    for k, v in params.items():
        if f"<<{k}>>" in content:
            content = content.replace(f"<<{k}>>", v)
    rerst = re.search(r"<<\w+>>", content)
    if rerst:
        logger.error(f"Missing items ({rerst.group()}) to be replaced in template!")
        raise RuntimeError

    with open(ofile, "w") as f:
        f.write(content)


def render_setenv_sh_with_revenv(instrL: str | list[str], ofile: str = "", params: dict | None = None, source_only: bool = False):
    """
    Last Update: @2024-09-05 10:12:28
    ---------------------------------
    Used to render setenv bash script with environment reverting statements

    :param instrL: one or more file path or direct string content, see code:Prepare
    :param ofile: output file, if not True, will return result string directly
    :param params: dict used to update the final input string
    :param source_only: add a source-check or not. If added, it can not be executed directly
    """

    # @ Prepare | Parse final input string from one or more given string or files
    if isinstance(instrL, str):
        instrL = [instrL]
    assert isinstance(instrL, list)
    instr = ""
    for s in instrL:
        if os.path.exists(s):
            with open(s) as f:
                s = f.read()
        instr += f"\n{s}\n"

    for k, v in params.items():
        instr = instr.replace(f"<<{k}>>", v)

    rst = ""
    if source_only:
        rst += textwrap.dedent("""\
            if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
                echo "The script can only be sourced rather than executed"
                exit 0
            fi
            """)

    rst += """\nif [[ -z "$1" || "$1" != "unload" ]]; then\n"""
    rst += instr

    projname_alpha_only = ''.join([x for x in projname if x.isalpha()])  # @ exp | i.e., remove special characters
    rmep_func = f"__rmep_{projname_alpha_only}"
    content_revert = revenv(instr, rmep_func=rmep_func)
    rst += "\nelse\n"
    if rmep_func in content_revert:
        rst += textwrap.dedent("""
            function %s(){
                local rst=$(echo :${!1} | sed "s|:$2||g")
                if [[ "$rst" =~ ^: ]]; then
                    export $1="${rst:1}"
                else
                    export $1="${rst}"
                fi
            }
            """ % rmep_func)
    rst += content_revert
    rst += f"unset -f {rmep_func}"
    rst += "\nfi\n"

    if ofile:
        with open(ofile, "w") as f:
            f.write(rst)
    else:
        return rst


def generate_modulefile_from_setenv(modulefile: str, setenvfile: str):
    """
    Last Update: @2024-09-05 10:18:18
    ---------------------------------
    Generate modulefile from setenv file supporting load and unload actions
    """
    logger.info(f"Generating modulefile")
    logger.debug(f"  {modulefile=}")

    assert os.path.exists(setenvfile)
    moddir = os.path.dirname(modulefile)
    os.makedirs(moddir, exist_ok=True)

    with open(modulefile, "w") as f:
        f.write(textwrap.dedent(f"""\
            #%Module1.0

            if {{ [module-info mode load] }} {{
                puts "source {setenvfile} load"
            }}
            if {{ [module-info mode remove] }} {{
                puts "source {setenvfile} unload"
            }}
            """))


def add_source_to_script(exportdir: str, projname: str):
    """
    Last Update: @2024-09-05 10:25:47
    ---------------------------------
    Handle add source functionality
    """
    logger.info("handling args.addousrce")
    if args.module:
        asstr = textwrap.dedent(f"""\
            # ************************ [{projname}]
            module use {exportdir}/modulefiles
            module load {projname}
                                                    
            """)
    else:
        asstr = textwrap.dedent(f"""\
            # ************************ [{projname}]
            source {exportdir}/setenv.{projname}.sh load

            """)
    if args.addsource == "stdout":
        print(asstr)
    else:
        target_script = args.addsource
        logger.debug(f">> Updating statement into {target_script}")
        update_block(target_script, asstr)


def main(projdir: str):
    global args, logger, isWSL, deploydir, projname

    assert os.path.exists(projdir)

    isWSL = bool(os.getenv("WSL_DISTRO_NAME"))

    parser = argparse.ArgumentParser(description=f"""rdee-* series deployment script""")
    parser.add_argument('--rehome', '-r', help='Set home directory')
    parser.add_argument('--deploydir', '-o', default=".", help='Set deployment directory')
    parser.add_argument('--module', '-m', action="store_true", help='use module')
    parser.add_argument('--executables', '-e', nargs='+', default=None, help='Select executables or executables directory to be linked')

    parser.add_argument('--debug', '-d', action="store_true", help='show debug message')
    parser.add_argument('--silent', '-s', action="store_true", help='hide general message')
    parser.add_argument('--addsource', '-a', default=None, nargs='?', const="stdout", help='add source statement in target script')
    parser.add_argument('--withlist', '-w', nargs="+", help='Union some other tools together')

    args = parser.parse_args()

    if args.debug:
        loglevel = "debug"
    elif args.silent:
        loglevel = "warning"
    else:
        loglevel = "info"

    deploydir = os.path.abspath(args.deploydir)
    # assert os.path.basename(deploydir) == "deploy"
    projname = os.path.basename(projdir)

    logger = fastLogger(name=projname, level=loglevel)
    logger.debug(f"{deploydir=}")

    if args.executables:
        exes = args.executables
    else:
        exes = glob.glob(f"{projdir}/src/**/bin", recursive=True)
    return deploy(projdir, exes)


# @ rdeexpo
# @ Below is the supporting functions for the main logic above, and most are exported from rdee-python
# @ Code below is maintained and updated manually since the deployer.py script should be stable.


# *********************************************************
# error
# *********************************************************
class UnReachableError(Exception):
    pass


# *********************************************************
# fastLogger
# *********************************************************
VERBOSE = 15
logging.addLevelName(VERBOSE, "VERBOSE")


def verbose(self, message, *args, **kws):
    if self.isEnabledFor(VERBOSE):
        self._log(VERBOSE, message, args, stacklevel=2, **kws)


logging.Logger.verbose = verbose


class ColorFormatter(logging.Formatter):
    """
    Last Update: @2024-08-30 14:51:26
    ---------------------------------
    Colorful format for logging text

    reference: https://stackoverflow.com/questions/384076/how-can-i-color-python-logging-output
    """

    FORMATS = {
        logging.DEBUG: "\033[38;5;51m%(name)s:\033[0m \033[4m%(asctime)s\033[0m (\033[1m%(filename)s:%(lineno)d | %(funcName)s\033[0m) \033[35m[%(levelname)s]\033[0m %(message)s",
        15: "\033[38;5;51m%(name)s:\033[0m \033[4m%(asctime)s\033[0m (\033[1m%(filename)s:%(lineno)d | %(funcName)s\033[0m) \033[32m[%(levelname)s]\033[0m %(message)s",
        logging.INFO: "\033[38;5;51m%(name)s:\033[0m \033[4m%(asctime)s\033[0m (\033[1m%(filename)s:%(lineno)d | %(funcName)s\033[0m) \033[36m[%(levelname)s]\033[0m %(message)s",
        logging.WARNING: "\033[38;5;51m%(name)s:\033[0m \033[4m%(asctime)s\033[0m (\033[1m%(filename)s:%(lineno)d | %(funcName)s\033[0m) \033[33m[%(levelname)s]\033[0m %(message)s",
        logging.ERROR: "\033[38;5;51m%(name)s:\033[0m \033[4m%(asctime)s\033[0m (\033[1m%(filename)s:%(lineno)d | %(funcName)s\033[0m) \033[31m[%(levelname)s]\033[0m %(message)s",
        logging.CRITICAL: "\033[38;5;51m%(name)s:\033[0m \033[4m%(asctime)s\033[0m (\033[1m%(filename)s:%(lineno)d | %(funcName)s\033[0m) \033[31;1m[%(levelname)s]\033[0m %(message)s"
    }

    def format(self, record):  # @| required method for class logging.Formatter
        log_fmt = self.FORMATS.get(record.levelno)
        if os.getenv("PYTHON_LOGGING_TIME") == "DATETIME":
            date_format = "%Y-%m-%d %H:%M:%S"
        else:
            date_format = "%H:%M:%S"
        formatter = logging.Formatter(log_fmt, datefmt=date_format)
        return formatter.format(record)


def _get_llspec_from_env() -> Optional[dict]:
    llspec = None

    jsf = os.getenv("PYTHON_LLSPEC_JSON")
    if jsf:
        try:
            with open(jsf) as f:
                llspec = json.load(f)
        except:
            raise RuntimeError("env:PYTHON_LLSPEC_JSON points to an invalid json file")
    else:
        spec_commas = os.getenv("PYTHON_LLSPEC_COMMA")
        if spec_commas:
            llspec = dict(item.split("=") for item in spec_commas.split(","))

    if llspec:
        llspec = {k: _v2ll(v) for k, v in llspec.items()}

    return llspec


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

        target_name = record.funcName if record.funcName != "<module>" else record.module  # @ exp | For compatiability with module-level statements

        baselevel = logging.INFO if "base" not in llspec else llspec["base"]
        if target_name in llspec:
            return record.levelno >= llspec[target_name]
        else:
            return record.levelno >= baselevel


def fastLogger(name="root", level: Union[str, int, None] = None) -> logging.Logger:
    """
    Last Update: @2024-09-21 19:45:11
    ---------------------------------
    Get a logging.Logger with flexible logging level setting via several environment variables, including :
        - env:  PYTHON_LLSPEC_JSON
            - A json file for specific level settings, i.e., {"base": "INFO", "a_func_name":"DEBUG"}
        - env:  PYTHON_LLSPEC_COMMA
            - A string for specific level settings (can be considered as a serialization for PYTHON_LLSPEC_JSON content), e.g., "base=INFO,a_func_name=DEBUG"
        - env:  arg(level)
            - Just set the level for the whole logger

    :param name: logger name
    :param level: used to set level for the whole logger
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        llspec = _get_llspec_from_env()
        if llspec is not None:
            print(f"Specifying logging level: {llspec=}")
            logger.setLevel(logging.DEBUG)
            logger.llspec = llspec
            logger.addFilter(EnvFilter(logger))
        else:
            logger.setLevel(_v2ll(level))

        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(ColorFormatter())
        logger.addHandler(sh)
        logger.propagate = False
    return logger


def _v2ll(v: Union[str, int, None]) -> int:
    """
    Last Update: @2024-10-22 22:58:23
    ---------------------------------
    This function parses a variable to logging Level with a flexible method, including direct int, string match and environment variable
    """

    # ~~~~~~~~~~~~~~~~~~ default
    if v is None:
        return logging.INFO

    # ~~~~~~~~~~~~~~~~~~ int
    if isinstance(v, int):
        return v

    # ~~~~~~~~~~~~~~~~~~ string
    if isinstance(v, str):
        # ----- int-string
        try:
            v_int = int(v)
            return _v2ll(v_int)
        except:
            pass

        # ----- level-string
        vU = v.upper()
        if vU.startswith("INFO"):
            return logging.INFO
        if vU.startswith("VERBOSE"):
            return 15
        if vU.startswith("DEBUG"):
            return logging.DEBUG
        if vU.startswith("WARN"):
            return logging.WARNING
        if vU.startswith("ERROR"):
            return logging.ERROR
        if vU.startswith("FATAL"):
            return logging.FATAL

        # ----- environment-variable
        envval = os.getenv(v)

        if envval:
            return _v2ll(envval)

        return logging.INFO

    raise TypeError(f"Error! Unkown value for log-level type: {type(v)}")


# *********************************************************
# shrun & update_block
# *********************************************************
def shrun(cmd: str, shell="auto", logfile="", ensure_noerror=False):
    """
    Last Update: @2024-08-01 17:22:30
    -----------------------------------
    Executable shell command, supporting bash, cmd.exe & powershell.exe (pwsh.exe)

    :param cmd:         target command to be executed
    :param shell:       target shell, supporting bash, cmd.exe & powershell.exe (pwsh.exe)
    :param logfile:     if set, will export stdout & stderr into the logfile
    :param ensure_noerror:     raise an error if command return code is not 0
    :return:            (command-return-code, stdout), if logfile is set, stdout would be empty string
    """

    mysys = platform.system()
    if shell == "auto":
        if mysys == "Linux":
            shell = "bash"
        elif mysys == "Windows":
            shell = "cmd"
        else:
            raise RuntimeError(f"Unsupported system: {mysys}")

    if shell == "bash":
        cmd_option = "-c"
    elif shell.startswith("cmd"):
        shell = "cmd.exe"
        cmd_option = "/C"
    elif shell.startswith("pwsh"):
        shell = "pwsh.exe"
        cmd_option = "-Command"
    elif shell.startswith("powershell"):
        shell = "powershell.exe"
        cmd_option = "-Command"
    else:
        raise TypeError(f"Unknown arg:shell = {shell}, should be one of bash, cmd, pwsh or powershell")

    if logfile:
        try:
            ostream = open(logfile, "w")
        except:
            raise IOError(f"Cannot open logfile: {logfile}")
    else:
        ostream = subprocess.PIPE

    robj = subprocess.run([shell, cmd_option, cmd], text=True, stdout=ostream, stderr=subprocess.STDOUT)

    if ensure_noerror:
        if robj.returncode != 0:
            raise RuntimeError(f"Error in {cmd=}, returncode={robj.returncode}, info={robj.stdout}")

    return (robj.returncode, robj.stdout.strip() if robj.stdout else "")


def update_block(basefile, blocktext, cheader=None, replace_only=False):
    # @ prepare
    # @ .static-variables
    headerStock = {
        ".py": "#!/usr/bin/env python3\n# coding=utf-8",
        ".sh": "#!/bin/bash",
        "tmod": "#%Module1.0"
    }

    # @ .handle-file
    if os.path.exists(blocktext):
        with open(blocktext) as f:
            blocktext = f.read()

    # @ core
    # @ .case:no-basefile
    if not os.path.exists(basefile):
        if cheader is not None:  # @ exp Empty string is allowed @2024-03-22 11:10:07
            if cheader in headerStock:
                header = headerStock[cheader]
            else:
                header = cheader
        else:
            ext = os.path.splitext(basefile)[1]
            header = headerStock.get(ext, "\n")
        with open(basefile, "w") as f:
            f.write(header.replace(r"\n", "\n") + "\n\n")
            f.write(blocktext)
        return

    # @ .locate
    baselines = open(basefile, encoding="utf-8").read().splitlines()
    blocklines = blocktext.splitlines()

    imatch = -1
    for i, L in enumerate(baselines):
        if L == blocklines[0]:
            assert imatch == -1, f"Error! Multiple matched lines, such as line:{imatch} and line:{i}"
            imatch = i

    # @ <.branch:append>
    if imatch == -1:
        if not replace_only:
            with open(basefile, "a") as f:
                f.write("\n")
                f.write(blocktext)
                f.write("\n")
        else:
            print("Cannot find target code snippets for replacement, return")
        return

    # @ <.branch:replace>
    # @ <..locate-endline>
    jmatch = -1
    for j in range(imatch, len(baselines)):
        if baselines[j].rstrip() == blocklines[-1].rstrip():
            jmatch = j
            break
    assert jmatch != -1

    # @ <..output>
    with open(basefile, "w") as f:
        for i in range(imatch):
            f.write(baselines[i] + "\n")
        for L in blocklines[:-1]:
            f.write(L + "\n")
        f.write(baselines[jmatch] + "\n")
        for i in range(jmatch + 1, len(baselines)):
            f.write(baselines[i] + "\n")

    return


# *********************************************************
# revenv
# *********************************************************
def revenv(codelines: str | list[str], rmep_func: str = "rmep"):
    """
    Last Update: @2024-09-04 13:40:40
    ---------------------------------
    This function aims to revert environemnt setting statements.
    Supports:
        - alias
        - export A=1
        - export B=2:$B
        - function 
    some complex statemetns are not supported now, reuqiring more powerful parsing functionality maybe

    :param codelines: bash code in a string or string by lines
    """
    if isinstance(codelines, str):
        codelines = codelines.splitlines()
    assert isinstance(codelines, list)

    rst = ""
    inFunc = False
    for L in codelines:
        if inFunc:
            if L.strip() == "}":
                inFunc = False
            continue
        if L.startswith("alias "):
            aliasname = re.search(r"alias .*?(\S+)=", L).group(1)
            rst += f"unalias {aliasname}\n"
        elif L.startswith("function "):
            funcname = re.search(r"function +(\w+)", L).group(1)
            rst += f"unset -f {funcname}\n"
            inFunc = True
        elif L.startswith("export"):
            evname = re.search(r"export +(\w+)", L).group(1)
            if ":" in L:
                rhs = re.search(r"export +\w+=(.*)", L).group(1).split(":")
                rhs.remove("$" + evname)
                for rh in rhs:
                    rst += f"{rmep_func} {evname} {rh}\n"
            else:
                rst += f"unset {evname}\n"
        elif re.search(r"^source +.*\.sh +load$", L):  # @ exp | Special case for rdee-* series deployment
            rst += L.replace(" load", " unload\n")
        else:
            rst += f"{L}\n"

    return rst
