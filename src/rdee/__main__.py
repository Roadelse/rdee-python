# coding=utf-8


# ................. standard lib
import sys
import os
import argparse
# ................. project lib
import rdee


def main():
    parser = argparse.ArgumentParser(description="""library test & information""")
    subparsers = parser.add_subparsers(dest='task', help='Sub-command help')
    
    parser_utest = subparsers.add_parser("utest", help="Do unit-test based on test[._]*.py files")
    parser_utest.add_argument('utest', nargs='*', default=None, help='select test targets')
    parser_utest.add_argument('--directory', "-d", default=".", help='select test directory')
    parser_utest.add_argument('--remainTest', "-r", action="store_true", help='utest will not delete the test directory if this option is set')

    parser_export = subparsers.add_parser("export", help="Execute a target function based on command line arguments")
    parser_export.add_argument("fcs", nargs="+", help="functions and classes to be exported")
    parser_export.add_argument("--outfile", "-o", default="rdeext.py", help="functions and classes to be exported")


    parser_func = subparsers.add_parser("execfunc", help="Execute a target function based on command line arguments")
    parser_func.add_argument('--function', "-f", default=None, help='select target function')
    parser_func.add_argument('--arguments', "-a", nargs='*', default=None, help='set function arguments')


    args = parser.parse_args()
    # print(args.utest)
    if args.task == "utest":
        if args.remainTest:
            os.environ["UTEST_KEEP"] = "1"
        rdee.utest.dotest(args.utest, args.directory)
    elif args.task == "execfunc":
        print("to be dev")
    elif args.task == "export":
        pym = rdee.code.pycode_module(rdee)
        pym.export_fcs(args.outfile, fcs=args.fcs)


if __name__ == '__main__':
    main()
