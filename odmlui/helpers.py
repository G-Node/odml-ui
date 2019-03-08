"""
The 'helpers' module provides various helper functions.
"""

import getpass
import json
import os
import subprocess
import sys

from odml import fileio
from odml.dtypes import default_values
from odml.tools.parser_utils import SUPPORTED_PARSERS

from .treemodel import value_model

try:  # Python 3
    from urllib.parse import urlparse, unquote, urljoin
    from urllib.request import pathname2url
except ImportError:  # Python 2
    from urlparse import urlparse, urljoin
    from urllib import unquote, pathname2url


def uri_to_path(uri):
    """
    *uri_to_path* parses a uri into a OS specific file path.

    :param uri: string containing a uri.
    :return: OS specific file path.
    """
    net_locator = urlparse(uri).netloc
    curr_path = unquote(urlparse(uri).path)
    file_path = os.path.join(net_locator, curr_path)
    # Windows specific file_path handling
    if os.name == "nt" and file_path.startswith("/"):
        file_path = file_path[1:]

    return file_path


def path_to_uri(path):
    """
    Converts a passed *path* to a URI GTK can handle and returns it.
    """
    uri = pathname2url(path)
    uri = urljoin('file:', uri)
    return uri


def get_extension(path):
    """
    Returns the upper case file extension of a file
    referenced by a passed *path*.
    """
    ext = os.path.splitext(path)[1][1:]
    ext = ext.upper()
    return ext


def get_parser_for_uri(uri):
    """
    Sanitize the given path, and also return the
    odML parser to be used for the given path.
    """
    path = uri_to_path(uri)
    parser = get_extension(path)

    if parser not in SUPPORTED_PARSERS:
        parser = 'XML'

    return parser


def get_parser_for_file_type(file_type):
    """
    Checks whether a provided file_type is supported by the currently
    available odML parsers.

    Returns either the identified parser or XML as the fallback parser.
    """
    parser = file_type.upper()
    if parser not in SUPPORTED_PARSERS:
        parser = 'XML'
    return parser


def handle_section_import(section):
    """
    Augment all properties of an imported section according to odml-ui needs.

    :param section: imported odml.BaseSection
    """
    for prop in section.properties:
        handle_property_import(prop)

    # Make sure properties down the rabbit hole are also treated.
    for sec in section.sections:
        handle_section_import(sec)


def handle_property_import(prop):
    """
    Every odml-ui property requires at least one default value according
    to its dtype, otherwise the property is currently broken.
    Further the properties are augmented with 'pseudo_values' which need to be
    initialized and added to each property.

    :param prop: imported odml.BaseProperty
    """
    if len(prop.values) < 1:
        if prop.dtype:
            prop.values = [default_values(prop.dtype)]
        else:
            prop.values = [default_values('string')]

    create_pseudo_values([prop])


def create_pseudo_values(odml_properties):
    """
    Creates a treemodel.Value for each value in an
    odML Property and appends the resulting list
    as *pseudo_values* to the passed odML Property.
    """
    for prop in odml_properties:
        values = prop.values
        new_values = []
        for index in range(len(values)):
            val = value_model.Value(prop, index)
            new_values.append(val)
        prop.pseudo_values = new_values


def get_conda_root():
    """
    Checks for an active Anaconda environment.

    :return: Either the root of an active Anaconda environment or an empty string.
    """
    # Try identifying conda the easy way
    if "CONDA_PREFIX" in os.environ:
        return os.environ["CONDA_PREFIX"]

    # Try identifying conda the hard way
    try:
        conda_json = subprocess.check_output("conda info --json",
                                             shell=True, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as exc:
        print("[Info] Conda check: %s" % exc)
        return ""

    if sys.version_info.major > 2:
        conda_json = conda_json.decode("utf-8")

    dec = json.JSONDecoder()
    try:
        root_path = dec.decode(conda_json)['default_prefix']
    except ValueError as exc:
        print("[Info] Conda check: %s" % exc)
        return ""

    if sys.version_info.major < 3:
        root_path = str(root_path)

    return root_path


def run_odmltables(file_uri, save_dir, odml_doc, odmltables_wizard):
    """
    Saves an odML document to a provided folder with the file
    ending '.odml' in format 'XML' to ensure an odmltables
    supported file. It then executes odmltables with the provided wizard
    and the created file.

    :param file_uri: File URI of the odML document that is handed over to
                     odmltables.
    :param save_dir: Directory where the temporary file is saved to.
    :param odml_doc: An odML document.
    :param odmltables_wizard: supported values are 'compare', 'convert',
                              'filter' and 'merge'.
    """

    tail = os.path.split(uri_to_path(file_uri))[1]
    tmp_file = os.path.join(save_dir, ("%s.odml" % tail))
    fileio.save(odml_doc, tmp_file)

    try:
        subprocess.Popen(['odmltables', '-w', odmltables_wizard, '-f', tmp_file])
    except Exception as exc:
        print("[Warning] Error running odml-tables: %s" % exc)


def get_username():
    """
    :return: Full name or username of the current user
    """
    username = getpass.getuser()

    try:
        # this only works on linux
        import pwd
        fullname = pwd.getpwnam(username).pw_gecos
        if fullname:
            username = fullname
    except ImportError:
        pass

    return username.rstrip(",")
