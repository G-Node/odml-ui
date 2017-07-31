
import os

try:  # Python 3
    from urllib.parse import urlparse, unquote
except ImportError:  # Python 2
    from urlparse import urlparse
    from urllib import unquote 

def uri_to_path(uri):
    file_path = urlparse(uri).path
    file_path = unquote(file_path)
    return file_path

def uri_exists(uri):
    file_path = uri_to_path(uri)
    if os.path.isfile(file_path):
        return True

    return False
