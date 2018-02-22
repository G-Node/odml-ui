import os
import json

here = os.path.dirname(__file__)

with open(os.path.join(here, "info.json")) as infofile:
    infodict = json.load(infofile)

VERSION = infodict["VERSION"]
AUTHOR = infodict["AUTHOR"]
COPYRIGHT = infodict["COPYRIGHT"]
CONTACT = infodict["CONTACT"]
HOMEPAGE = infodict["HOMEPAGE"]
CLASSIFIERS = infodict["CLASSIFIERS"]
ODMLTABLES_VERSION = infodict["ODMLTABLES_VERSION"]
