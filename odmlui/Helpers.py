
import os

from odml.tools.odmlparser import allowed_parsers

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
    '''
        Sanitize the given path, and also return the odML parser to be used 
        for the given path.
    '''
    path = uri_to_path(uri)
    parser = get_extension(path)

    if parser not in allowed_parsers:
        parser = 'XML'

    return parser
