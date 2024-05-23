#!/usr/bin/env python
# make executable in bash chmod +x PyRun

import sys
import inspect
import importlib
import os

if __name__ == "__main__":
    # I suppose this verifies whether the file exists in the current path or not
    cmd_folder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0]))
    if cmd_folder not in sys.path:
        sys.path.insert(0, cmd_folder)

    # get the second argument from the command line - name of function
    methodname = sys.argv[1]
    # split this into module, class and function name
    modulename, funcname = methodname.split(".")
    # get pointers to the objects based on the string names
    themodule = importlib.import_module(modulename)
    thefunc = getattr(themodule, funcname)

    # get the third argument - number of subjects whose files we want to read
    subs = sys.argv[2]

    # get the fourth argument - number of channels
    chans = sys.argv[3]

    # get the fifth argument - perform the normal or the hierarchical method
    method = sys.argv[4]

    # pass all the parameters for what the function needs & ignore the rest
    args = inspect.getfullargspec(thefunc)
    z = len(args[0]) + 2
    params=sys.argv[2:z]
    thefunc(*params)