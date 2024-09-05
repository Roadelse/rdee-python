#!/usr/bin/env python3
# coding=utf-8

"""
Last Update: @2024-09-04 15:31:40
---------------------------------
This module provides functionality concerning:
    - Operatiion system
    - Shell
    - File
"""

#@sk import
import platform
import sys
import os
import os.path
import shutil
import subprocess
import traceback

def rmrf(directory: str, remain_itself: bool = False, use_strict: bool = False) -> None:
    try:  #@ jbond
        from rdee import _o_state as ogs
        if ogs.strict:
            use_strict = True
    except:
        pass

    if os.path.isfile(file_path):
        os.unlink(directory)

    #@sk boundary if directory doesn't exist
    if not os.path.isdir(directory):
        if use_strict:
            raise RuntimeError("Error! Target to rmrf in not an existed directory")
        return None
    
    if not remain_itself:
        shutil.rmtree(directory)
        return

    #@sk core
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')
            if use_strict:  #@sk raise error if use_strict
                traceback.print_exc()
                raise
    
def shrun(cmd: str, shell="auto", logfile = "", ensure_noerror=False):
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
            raise RuntimeError(f"Error in {cmd=}, returncode={robj.returncode}")

    return (robj.returncode, robj.stdout.strip() if robj.stdout else "")


class FileOP:
    def __new__(self, *args, **kwargs):
        raise TypeError("Error! cannot initialize class pycode")
    
    @staticmethod
    def update_block(basefile, blocktext, cheader = None, replace_only = False):
        #@ prepare
        #@ .static-variables
        headerStock = {
            ".py": "#!/usr/bin/env python3\n# coding=utf-8",
            ".sh": "#!/bin/bash",
            "tmod": "#%Module1.0" 
        }

        #@ .handle-file
        if os.path.exists(blocktext):
            with open(blocktext) as f:
                blocktext = f.read()
        
        #@ core
        #@ .case:no-basefile
        if not os.path.exists(basefile):
            if cheader is not None:  #@ exp Empty string is allowed @2024-03-22 11:10:07
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

        #@ .locate
        baselines = open(basefile, encoding="utf-8").read().splitlines()
        blocklines = blocktext.splitlines()

        imatch = -1
        for i, L in enumerate(baselines):
            if L == blocklines[0]:
                assert imatch == -1, f"Error! Multiple matched lines, such as line:{imatch} and line:{i}"
                imatch = i
        
        #@ <.branch:append>
        if imatch == -1:
            if not replace_only:
                with open(basefile, "a") as f:
                    f.write("\n")
                    f.write(blocktext)
                    f.write("\n")
            else:
                print("Cannot find target code snippets for replacement, return")
            return

        #@ <.branch:replace>
        #@ <..locate-endline>
        jmatch = -1
        for j in range(imatch, len(baselines)):
            if baselines[j].rstrip() == blocklines[-1].rstrip():
                jmatch = j
                break
        assert jmatch != -1

        #@ <..output>
        with open(basefile, "w") as f:
            for i in range(imatch):
                f.write(baselines[i] + "\n")
            for L in blocklines[:-1]:
                f.write(L + "\n")
            f.write(baselines[jmatch] + "\n")
            for i in range(jmatch + 1, len(baselines)):
                f.write(baselines[i] + "\n")
        
        return
