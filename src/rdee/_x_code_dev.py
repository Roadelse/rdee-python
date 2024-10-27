# coding=utf-8

from __future__ import annotations

from typing import Sequence
import inspect
import re
import sys
import os
import abc
import warnings
import ast
import textwrap

from ._o_funcs import noinstance

try:
    import libcst as cst
    use_libcst = True
except:
    use_libcst = False

@noinstance
class PyCode:
    @noinstance
    class Tools:
        pass

    class Node(abc.ABC):
        def __init__(self, code="", object=None, cstnode=None, *args, **kwargs):
            """
            Last Update: @2024-09-09 17:15:34 | code.PyCode.Node
            ----------------------------------------------------
            Initialize base attributes for all PyCode.Node and its children classes
            Accept different kinds of input arguments, all is optional but at least provide one
            
            :param code: python code
            :param object: python object
            :param cstnode: libcst node 
            """
            self.obj = object
            
            if code:
                self.code = code
            elif object:
                self.code = inspect.getsource(object)
            elif cstnode:
                self.code = cst.Module([]).node_for_code(cstnode)
            else:
                raise TypeError("Must provide at least one argument, code/object/cstnode")

            if cstnode:
                self.cstnode = cstnode
            else:
                self.cstnode = cst.parse_module(self.code)

            self.module = None

    class Module(Node):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.submodules = []
            self.subfunctions = []
            self.subclasses = []
    
        def parse(self):
            for blk in self.cstnode.body:
                if isinstance(blk, cst.FunctionDef):
                    


    class Function(Node):
        pass

    class Class(Node):
        pass

    class Block(Node):
        pass

    class Statement(Block):
        pass

    class Object:
        pass

# class pycode_func:
#     pass


# class pycode_node(abc.ABC):
#     pass

# class pycode_module(pycode_node):
