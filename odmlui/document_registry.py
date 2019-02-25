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
        add a document to the registry and return its unique id
        """
        # odML.Document is unhashable. Converting to string before hashing
        doc_id = hash(doc)
        self.docs[doc_id] = doc
        return doc_id

    def get(self, doc_id):
        """
        return a document from the registry based on its unique id
        """
        return self.docs[doc_id]

    @staticmethod
    def get_id(doc):
        # odML.Document is unhashable. Converting to string before hashing.
        return hash(doc)
