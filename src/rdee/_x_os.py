#!/usr/bin/env python3
# coding=utf-8

"""
This module contains several functions for os oprations, which may not directly supported in STL:os
"""

#@sk import
import os
import os.path
import shutil
import subprocess

from rdee import _o_globalstate as ogs


def rmrf(directory: str, use_strict: bool = False, remain_itself: bool = False) -> None:
    #@sk prepare check if use strict
    if ogs.strict:
        use_strict = True

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
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')
            if use_strict:  #@sk raise error if use_strict
                raise
    
def shrun(cmd: str, logfile = "", error_on_fail=False, merge_stderr=True):
    """
    run bash commands
    @2024-07-05 15:49:53
    """
    if logfile:
        # arg:merge_stderr doesn't work here
        robj = subprocess.run(f"{cmd} >& {logfile}", shell=True, executable="/bin/bash", text=True)
    else:
        if merge_stderr:
            robj = subprocess.run(cmd, shell=True, executable="/bin/bash", text=True, stdout=subprocess.PIPE)
        else:
            robj = subprocess.run(cmd, shell=True, executable="/bin/bash", text=True, capture_output=True)


    if error_on_fail:
        if robj.returncode != 0:
            raise RuntimeError(f"Error in {cmd=}, returncode={robj.returncode}")

    if merge_stderr:
        return (robj.returncode, robj.stdout.strip())
    else:
        return (robj.returncode, robj.stdout.strip(), robj.stderr.strip())