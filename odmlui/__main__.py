#!/usr/bin/env python
import pygtkcompat
pygtkcompat.enable()
pygtkcompat.enable_gtk(version='3.0')

import gtk
import os

import odmlui
from . import Editor
from . import Helpers

def main(filenames=[], debug=False):
    """
    start the editor, with a new empty document
    or load all *filenames* as tabs

    returns the tab object
    """
    odmlui.DEBUG = debug
    Editor.register_stock_icons()
    editor = Editor.EditorWindow()

    # Convert relative path to absolute path, if any
    for i, file in enumerate(filenames):
        if not os.path.isabs(file):
            filenames[i] = os.path.abspath(file)

    file_uris = list(map(Helpers.path_to_uri, filenames))
    tabs = list(map(editor.load_document, file_uris))

    if len(filenames) == 0:
        editor.welcome()
    return tabs

def run():
    """
    handle all initialisation and start main() and gtk.main()
    """
    try: # this works only on linux
        from ctypes import cdll
        libc = cdll.LoadLibrary("libc.so.6")
        libc.prctl(15, 'odMLEditor', 0, 0, 0)
    except:
        pass
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('--debug', help='Print debug messages', action='store_true')
    parser.add_argument('--files', nargs='+', default=[], help='List of files to open')
    args = parser.parse_args()
    main(filenames=args.files, debug=args.debug)
    gtk.main()

if __name__=="__main__":
    run()
