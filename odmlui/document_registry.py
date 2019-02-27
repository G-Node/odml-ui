"""
Provides a document registry to enable working on
multiple documents in the same application.
"""

import weakref


class DocumentRegistry(object):
    """
    A registry keeping track of all documents in the current
    application's workspace.

    References are kept as weak references, as such, elements do not have to be
    removed explicitly.

    The unique id is computed using the hash() function (which in turn relies on
    the memory address of the object), so it should be unique unless the function
    is overridden.
    """
    def __init__(self):
        self.docs = weakref.WeakValueDictionary()

    def add(self, doc):
        """
        Add a document to the registry and return its hash as id.
        """
        doc_id = hash(doc)
        self.docs[doc_id] = doc
        return doc_id

    def get(self, doc_id):
        """
        Return a document from the registry based on its unique id.
        """
        return self.docs[doc_id]

    @staticmethod
    def get_id(doc):
        """
        Return the hash of a document.
        """
        return hash(doc)
