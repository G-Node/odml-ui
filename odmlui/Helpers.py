import json
import os
import subprocess
import sys

from odml import fileio
from odml.dtypes import default_values
from odml.tools.parser_utils import SUPPORTED_PARSERS

from .treemodel import ValueModel

try:  # Python 3
    from urllib.parse import urlparse, unquote, urljoin
    from urllib.request import pathname2url
except ImportError:  # Python 2
    from urlparse import urlparse, urljoin
    from urllib import unquote, pathname2url


def uri_to_path(uri):
    file_path = urlparse(uri).path
    file_path = unquote(file_path)
    return file_path


def uri_exists(uri):
    file_path = uri_to_path(uri)
    if os.path.isfile(file_path):
        return True

    return False


def path_to_uri(path):
    uri = pathname2url(path)
    uri = urljoin('file:', uri)
    return uri


def get_extension(path):
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
    if file_type not in SUPPORTED_PARSERS:
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
    if len(prop._value) < 1:
        if prop.dtype:
            prop._value = [default_values(prop.dtype)]
        else:
            prop._value = [default_values('string')]

    create_pseudo_values([prop])


def create_pseudo_values(odml_properties):
    for prop in odml_properties:
        values = prop.value
        new_values = []
        for index in range(len(values)):
            val = ValueModel.Value(prop, index)
            new_values.append(val)
        prop.pseudo_values = new_values


def get_conda_root():
    """
    Checks for an active Anaconda environment.

    :return: Either the root of an active Anaconda environment or an empty string.
    """
    root_path = ""
    try:
        conda_json = subprocess.check_output("conda info --json",
                                             shell=True, stderr=subprocess.PIPE)
        if sys.version_info.major > 2:
            conda_json = conda_json.decode("utf-8")

        dec = json.JSONDecoder()
        root_path = dec.decode(conda_json)['default_prefix']
        if sys.version_info.major < 3:
            root_path = str(root_path)

    except Exception as ex:
        print("[Info] Conda check: %s" % ex)

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
