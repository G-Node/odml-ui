#!/usr/bin/env python
import os

import pygtkcompat

import gtk

import odmlui

from .editor import register_stock_icons, EditorWindow
from .helpers import path_to_uri

pygtkcompat.enable()
pygtkcompat.enable_gtk(version='3.0')


def main(filenames=None, debug=False):
    """
    Start the editor, with a new empty document
    or load all passed *filenames* as tabs.

    Returns the tab object.
    """
    odmlui.DEBUG = debug
    register_stock_icons()
    editor = EditorWindow()

    if not filenames:
        filenames = []

    # Convert relative path to absolute path, if any
    for i, file in enumerate(filenames):
        if not os.path.isabs(file):
            filenames[i] = os.path.abspath(file)

    file_uris = list(map(path_to_uri, filenames))
    tabs = list(map(editor.load_document, file_uris))

    if len(filenames) == 0:
        editor.welcome()

    return tabs


def run():
    """
    handle all initialisation and start main() and gtk.main()
    """
    try:
        # this works only on linux
        from ctypes import cdll
        libc = cdll.LoadLibrary("libc.so.6")
        libc.prctl(15, 'odMLEditor', 0, 0, 0)
    except ImportError:
        pass

    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('--debug', help='Print debug messages', action='store_true')
    parser.add_argument('--files', nargs='+', default=[], help='List of files to open')
    args = parser.parse_args()
    main(filenames=args.files, debug=args.debug)
    gtk.main()


if __name__ == "__main__":
    run()
