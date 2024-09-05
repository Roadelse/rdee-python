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

try:
    import libcst as cst
    use_libcst = True
except:
    use_libcst = False
    

class pycode_func:
    def __new__(self, *args, **kwargs):
        raise TypeError("Error! cannot initialize class pycode")
    
    @classmethod
    def has_return_value(func):
        """
        this function is used to check if a function has a return value
        """
        tree = ast.parse(inspect.getsource(func))
        return any(isinstance(node, ast.Return) for node in ast.walk(tree))

    def class2enum(cls):
        """
        this function is used to convert an enum-style class to a real enum class
        used in: 
            - pestc4py.PETSc.KSP.ConvergedReason
        """
        from enum import Enum
        attrs = {name: value for name, value in cls.__dict__.items() if not name.startswith('__') and not callable(value)}
        return Enum(cls.__name__ + 'Enum', attrs)

    if use_libcst:
        class _CallNameCollector(cst.CSTVisitor):
            """
            Last Update: @2024-08-29 10:01:22 
            ---------------------------------
            This class is used in libcst for collecting caller names from a libcst node, i.e., function name or class name
            """
            def __init__(self):
                self.calls = []

            def visit_Call(self, node: cst.Call):
                func_name = self.get_full_name(node.func)
                if func_name:
                    self.calls.append(func_name)

            def get_full_name(self, node) -> str:
                if isinstance(node, cst.Attribute):
                    return f"{self.get_full_name(node.value)}.{node.attr.value}"
                elif isinstance(node, cst.Name):
                    return node.value
                return ""

        class _GetImportObjNameCollector(cst.CSTVisitor):
            """
            Last Update: @2024-08-29 10:01:22
            ---------------------------------
            This class is used in libcst for collecting import names from a libcst node, i.e., the actual key in namespace
            For example:
                - import os
                    we get os
                - from os import makedirs
                    we got makedirs
                - from os import makedirs as mkd
                    we got mkd
            """
            def __init__(self, module):
                self.module = module
                self.import_obj_names = []

            def visit_ImportAlias(self, node: cst.Call):
                # print("visit import alias")
                code = self.module.code_for_node(node)
                # print(f"{code=}")
                name = re.search(r"([a-zA-Z0-9_.]+),?$", code.strip()).group(1)
                # print(f"{name=}")
                self.import_obj_names.append(name)

        def get_imported_names(pycodes: str | Sequence[str]) -> list[str]:
            """
            Last Update: @2024-08-30 21:29:21
            ---------------------------------
            This function aims to extract names from import statements

            :param pycodes: a string or a sequence of string representing python code text
            :return: a list of imported names
            """
            # print(f"{pycodes=}")
            if isinstance(pycodes, str):
                pass
            elif isinstance(pycodes, Sequence):  #@| Note str is Sequence as well (@2024-08-30 21:29:17)
                pycodes = "\n".join(pycodes)
            else:
                raise TypeError
            
            tr = cst.parse_module(pycodes)
            collector = pycode_func._GetImportObjNameCollector(tr)
            _ = tr.visit(collector)
            return collector.import_obj_names


def norm_skComment(C, level = 1, language = 'python', commentSymbol = None, style='default') : # normalize skeleton comments
    """
    this function is used to perform pretty and prescribed skeleton comments
    """
    import sys

    if commentSymbol:
        cl = commentSymbol
    else:
        if language == 'ncl' :
            cl = ';' # comment label
        elif language == 'python':
            cl = '#'
        else:
            raise RuntimeError('unknwon language : {}'.format(language))

    if style == 'default':
        if level == 1: # final 60
            charL = '>'
            charR = '<'
            lenCharL = ((59 - 4) - len(C)) // 2
            lenCharR = 59 - 4 - len(C) - lenCharL
            res = "{} {} {} {}".format(cl, charL * lenCharL, C, charR * lenCharR)
        elif level == 2:
            res = "{} {} {}".format(cl, '=' * 18, C)
        elif level == 3:
            res = "{} {} {}".format(cl, '~' * 10, C)
        elif level == 4:
            res = "{} {} {}".format(cl, '.' * 3, C)

    return res
    # print(res)


#**********************************************************************
# this function aims to reformat the skeleton comments
#**********************************************************************
def reformat_comments(content, style='default'):
    if isinstance(content, str):
        lines = content.splitlines()
    elif isinstance(content, list):
        lines = content
    else:
        raise TypeError
    
    for L in lines:
        if L[0] in ('#', '!', ';', '%'):
            commentSymbol = L[0]
        elif L[:2] in ('//'):
            commentSymbol = L[:2]
        else:
            raise RuntimeError("Unknown comment type or no comment at all!")
        break

    for i in range(len(lines)):
        L = lines[i]
        if not L.lstrip().startswith(commentSymbol):
            continue
        
        rst = re.search(rf' *{commentSymbol} *<L(\d)>', L)
        if rst:
            rerst = re.search(r'( *).*?<L(\d)> (.*)', L)
            actual_comment = rerst.group(3)
            cLevel = int(rerst.group(2))
            leadingSpaces = rerst.group(1)
            lines[i] = f"{leadingSpaces}{norm_skComment(actual_comment, cLevel, commentSymbol=commentSymbol, style=style)}"
    
    return '\n'.join(lines)



# #**********************************************************************
# # this function is used to check if a function has a return value
# # Use dir(), pkgutil. may work as well
# #   * cannot use __all__ since it only works in module
# #**********************************************************************
# def get_submodules(module, alias: str = None):
#     import types
    
#     assert isinstance(module, types.ModuleType)

#     if not hasattr(get_submodules, 'obj_set'):
#         outermost_flag = 1
#         setattr(get_submodules, 'obj_set', set())

#     get_submodules.obj_set.add(module.__name__)
    
#     try:  #>- check fully initialized
#         dir(module)
#     except:
#         return []
        
#     # print(mod_str)
#     # time.sleep(0.1)
#     for img in dir(module):
#         if img.startswith('_'):
#             continue
#         attr_str = f'module.{img}'
#         try:
#             attr = eval(attr_str)
#         except:
#             continue
#         if isinstance(attr, types.ModuleType) and \
#            attr.__name__ not in get_submodules.obj_set and \
#            attr.__name__.startswith(module.__name__):
#             # >- 1. check module; 2. ensure no circular; 3.avoid external module
#             get_submodules(attr)
    
#     # >>>>>>> remove the obj_set after the whole statistics
#     if 'outermost_flag' in locals():
#         rst = get_submodules.obj_set
#         delattr(get_submodules, 'obj_set')
#         if alias is not None:
#             rst = {_.replace(module.__name__, alias, 1) for _ in rst}
#         return list(rst)


# def get_apis(module):
#     import types

#     submodules = get_submodules(module, 'module')
#     rst = []
#     for sm in submodules:
#         for item in dir(sm):
#             if sm.startswith("_"):
#                 continue
            
#             attr_str = f'{sm}.{item}'
#             try:
#                 itemO = eval(attr_str)
#             except:
#                 continue
            
#             if isinstance(itemO, types.ModuleType):
#                 continue
            
#             rst.append()

#         try:
#             if hasattr(eval(sm), api):
#                 rst.append(f'{sm}.{api}')
#         except:
#             continue


# #**********************************************************************
# # this function is used to search apis for a given object
# #**********************************************************************
# def search_api(module, api: str, alias: str = None) -> list[str]:
#     submodules = get_submodules(module, 'module')

#     rst = []
#     for sm in submodules:
#         try:
#             if hasattr(eval(sm), api):
#                 rst.append(f'{sm}.{api}')
#         except:
#             continue

#     return [_.replace('module', module.__name__ if alias is None else alias) for _ in rst]



#**********************************************************************
# Class for re-building api tree
#**********************************************************************

if use_libcst:
    class pycode_node(abc.ABC):
        def __init__(self, obj, alias, parent):

            self._obj = obj
            
            self.alias = set()
            if alias:
                self.alias.add(alias)
        
            try:
                self._code = textwrap.dedent(inspect.getsource(obj))
            except:
                warnings.warn(f"Warning! Cannot get source code for object {self.name}")
                self._code = ""
            
            self._parent = None
            if parent:
                assert isinstance(parent, pycode_module)
                self._parent = parent

            self.import_statements = None
            self.extern_list = None
            self.parsed = False
            self.calls_parsed = False
        
        @property
        def obj(self):
            return self._obj

        @property
        def code(self):
            return self._code
        
        @property
        def name(self):
            return self.obj.__name__

        @property
        def parent(self):
            return self._parent

        def get_root(self):
            node = self
            while node.parent:
                node = node.parent
            return node
        
        def parse_import_statements(self):
            self.import_statements = []
            for L in self.code.splitlines():
                if L.startswith("#") or L.startswith(" "):
                    continue
                if re.match(r"import ", L) or " import " in L:
                    self.import_statements.append(L)

        def parse(self):
            self.parse_externs()

        def parse_externs(self):
            if self.import_statements is None:
                self.parse_import_statements()

            self.extern_list = []
            root_name = self.get_root().name
            for st in self.import_statements:
                if re.match(r"from .", st) or re.match(r"import +{root_name}", st):
                    continue
                inames = pycode_func.get_imported_names(st)
                for n in inames:
                    self.extern_list.append(n)

    class pycode_module(pycode_node):
        def __init__(self, obj, alias="", parent=None, parse: bool = False):
            assert inspect.ismodule(obj), f"Error! arg:obj must be a python module object, now is {type(obj)}"
            pycode_node.__init__(self, obj, alias, parent)

            
            self.submodules: dict[str, pycode_module] = {}
            self.funclss: dict[str, pycode_funcls] = {}
            self.others = {}

            if parse:
                self.parse()
        
        def get_all_funclss(self):
            fcsA = self.funclss.copy()
            for sm, node in self.submodules.items():
                fcsA.update(node.get_all_funclss())
            return fcsA

        def parse(self):
            # print("parsing " + self.name)
            pycode_node.parse(self)
            for name, obj in inspect.getmembers(self._obj):
                if name.startswith("_"):
                    continue
                if inspect.ismodule(obj) and obj.__name__.startswith(self.name):
                    if obj.__name__ in self.submodules:
                        self.submodules[obj.__name__].alias.add(name)
                    modT = pycode_module(obj, alias=name, parse=True)
                    self.submodules[obj.__name__] = modT
                elif inspect.isfunction(obj) or inspect.isclass(obj):
                    if obj.__name__ in self.funclss:
                        self.funclss[obj.__name__].alias.add(name)
                    fcT = pycode_funcls(obj, alias=name, parent=self, parse=True)
                    self.funclss[obj.__name__] = fcT
                else:
                    self.others[name] = obj

            self.parse_calls()
            self.parsed = True
        
        def parse_calls(self):
            for name, node in self.get_all_funclss().items():
                node.parse_calls(rootmod=self)
            self.calls_parsed = True

        def show(self, recursive: bool = False):
            if not self.parsed:
                self.parse()
            
            print("Class:")
            for cf in self.funclss:
                if cf.type == "class":
                    print(f"{cf}")

            print("Function:")
            for cf in self.funclss:
                if cf.type == "function":
                    print(f"{cf}")

            print("Sub-modules:")
            for sm, obj in self.submodules.items():
                print(f"{obj.alias}")


        def export_fcs(self, outfile: str, fcs) -> None:
            from ._o_funcs import isinstanceAll

            if not self.parsed:
                self.parse()
            import_statements = []
            if isinstance(fcs, dict):
                _objs = list(fcs.values())
            elif isinstance(fcs, str):
                fcsA = self.get_all_funclss()
                if fcs not in fcsA:
                    raise RuntimeError(f"Error! Cannot locate {fcs} in module")
                _objs = [fcsA[fcs]]
            elif isinstance(fcs,pycode_funcls):
                _objs = [fcs]
            elif isinstanceAll(fcs, pycode_funcls):
                _objs = fcs
            elif isinstanceAll(fcs, str):
                fcsA = self.get_all_funclss()
                _objs = []
                for n in fcs:
                    if n not in fcsA:
                        raise RuntimeError(f"Error! Cannot locate {n} in module")
                _objs = [fcsA[n] for n in fcs]
            else:
                raise TypeError(f"Illegal type for objs: {type(fcs)}")

            _objsDict = {}
            for o in _objs:
                _objsDict.update(o.get_all_dependencies())
            _objs2 = list(_objsDict.values())
            # print(_objsDict)
            
            for roj in _objs2:
                import_statements.extend(roj.parent.import_statements)
            import_statements_U = [x for x in list(set(import_statements)) if 'from .' not in x]
        
            objCodes = "\n\n"
            for robj in _objs2:
                print(f"exporting {robj.name}")
                objCodes += f"{robj.code}\n"
            # print(objCodes)
            
            import_statements_UV = []
            for L in import_statements_U:
                imported_obj_names = pycode_func.get_imported_names(L)
                
                found = False
                for iobjn in imported_obj_names:
                    # print(f"searching |{iobjn}|")
                    # print(re.search(rf'\b{iobjn}\b', objCodes))
                    if re.search(rf'\b{iobjn}\b', objCodes):
                        found = True
                        break
        
                if not found:
                    print(f"Skipping {L}")
                else:
                    import_statements_UV.append(L)
            
            
            with open(outfile, "w") as f:
                f.write("#!/usr/bin/env python\n")
                f.write("# coding=utf-8\n")
                f.write("# winexec=python\n\n")
        
                for L in import_statements_UV:
                    f.write(f"{L}\n")
        
                f.write(f"\n\n{objCodes}")


    class pycode_funcls(pycode_node):
        def __init__(self, obj, alias="", parent=None, parse: bool = False):
            if inspect.isfunction(obj):
                self.type = "function"
            elif inspect.isclass(obj):
                self.type = "class"
            else:
                raise TypeError(f"Illegal type for {self.name=}, {obj=}")
            pycode_node.__init__(self, obj, alias, parent)

            if parse:
                self.parse()

        def parse_calls(self, rootmod=None):
            collector = pycode_func._CallNameCollector()
            # print("------------------------------------------------")
            # print(self.code)
            # print("=============================")

            cstree = cst.parse_module(self.code)
            cstree.visit(collector)
            self.calls = collector.calls.copy()
            self.innerCalls = {}
            if rootmod is None:
                rootmod = self.parent
                # print(self.name)
                while rootmod.parent:
                    rootmod = rootmod.parent
            else:
                assert isinstance(rootmod, pycode_module)
            all_objs = rootmod.get_all_funclss()
            for cn in self.calls:
                cn_start = cn.split(".")[0]
                if cn_start in self.extern_list or cn_start in self.parent.extern_list:
                    continue
                cn_end = cn.split(".")[-1]
                if cn_end in all_objs:
                    self.innerCalls[cn_end] = all_objs[cn_end]

        def get_all_dependencies(self):
            rst = self.innerCalls.copy()
            rst[self.name] = self
            for name, node in self.innerCalls.items():
                # print(f"searching {name}")
                if name != self.name:  #@ note | Condition 1: self-recursive function; Condition 2: functions with same last name, i.e., rdee.logging.getLogger vs. logging.getLogger @2024-08-28 14:10:29
                    rst.update(node.get_all_dependencies())
            return rst
            

class shcode_func:
    def __new__(self, *args, **kwargs):
        raise TypeError("Error! cannot initialize class shcode")

    @staticmethod
    def remove_comment(S: str):
        if S.startswith("#"):
            return ""
        try:
            cmidx = S.index(" #")
            return S[:cmidx]
        except:
            return S

    @staticmethod
    def revenv(codelines: str|list[str]):
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
                aliasname = re.search(r"alias +([a-zA-Z0-9._]+)=", L).group(1)
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
                        rst += f"rmep {evname} {rh}\n"
                else:
                    rst += f"unset {evname}\n"
            elif re.search(r"^source .*setenv\..*\.sh +load$", L): #@ exp | Special case for rdee-* series deployment
                rst += L.replace(" load", " unload\n")
            else:
                rst += f"{L}\n"
        
        return rst
