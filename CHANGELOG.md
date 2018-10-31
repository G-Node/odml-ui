# Changelog

Used to document all changes from previous releases and collect changes 
until the next release.

# Latest changes in master

## Edit terminology values fixes

In some cases the values of terminology loaded Properties could not
be edited anymore, since the required "pseudo_value" attribute was
missing. Now every time a document is loaded or saved, all Properties
are checked and modified in case the "pseudo_value" attribute is missing.

## Fixes

- Fixes background errors when deleting Properties or Document root Sections. See #99.
- Fixes various occasions where the "Add Property" and "Add Value" icons were not 
    properly deactivated. See #90.
- The PropertyView is now properly reset when the last Section is removed from a
    Document making sure there are no stale leftover Properties on display.

# Version 1.4.1

## Icons fixes

- The Icon search path is now updated for system wide, local, virtualenv and conda installs as well. See #128, #130.
- "Undo" and "Redo" are added to the list of inactive icons when no document is available. See #131. 

## Missing welcome page fix

- The welcome page now is always displayed when there is no open tab. See #131.

## Other

- The README now contains a notice how to properly use odmlui with conda on macOS as well as updated documentation. See #130.


# Version 1.4.0
## Breaking changes

This release depends on [python-odml v1.4.0](
https://github.com/G-Node/python-odml/releases/tag/v1.4.0) which was a breaking change 
from v1.3. Due to this fact the current version is partially incompatible with the 
previous releases.

### Import of previous format odML files
odML files with file format "1" cannot be normally opened with the current release of 
odml-ui. They have to be converted into the new format using the `File - Import` feature, 
which will create, save and open a new, odML v1.4 compatible file. The original file 
remains untouched to ensure that no information is lost due to the conversion. See #127.

### 'Value' handling
- The `Value` attributes `encoder` and `checksum` have been removed.
- The `Value` attributes `unit`, `uncertainty`, `type` and `reference` can now only be 
    specified once for a Property.
- The `Value` attribute `filename` has been renamed to `value_origin`.
- The `Value` odML datatype `binary` has been removed. Adding binary content to odML 
    files is discouraged in lieu of providing the `URL` to the original file containing 
    the actual content.

### Mapping has been removed
Any mapping functionality has been removed from odml-ui. See #84.

## Features and updates
- Adds a confirmation dialog when `Save as` would replace an existing file. See #74.
- The validation is now always run before saving and only a valid odML file may be saved. 
    Otherwise the validation window with the encountered validation errors is displayed. 
    See #58.
- The default odML terminology repository used in the document wizard has been changed 
    to `http://portal.g-node.org/odml/terminologies/v1.1/terminologies.xml`.
- When a new document is created, the corresponding tab is automatically 
    selected. See #71.
- When a section with children sections is selected in the "Section View", this section 
    is now automatically expanded. See #73.
- A selected property now always expands, if it contains multiple values. See #70.
- The content of all multiple values can be voluntarily overwritten when the value entry 
    of the parent Property is set.
- Removes the wizard intro page; See #103 
- Increases the "Validation Window" size. See #75.
- Uses different main app starting window sizes (800x600 or 1024x768) depending on the 
    available screen size. See #113.
- Adjusts the height of the "Attribute View" to always display all attributes. See #113.
- Reorders the "Property View" columns; See #89.

### The odmtables plugin
- odml-ui provides access to [python-odmltables](
    https://github.com/INM-6/python-odmltables).
- odml-ui does not require odmltables to be installed, but rather provides buttons to 
    open the current odML document with the selected odmltables wizard plugins at all 
    times. If the required odmltables version cannot be found, an appropriate install 
    required version message is displayed. If odmltables is installed in the required 
    version, the selected wizard is opened in a new window with the odML document from 
    the currently active odml-ui tab.
- The currently supported odmltables wizard plugins are `compare`, `convert`, `filter` 
    and `merge`.
- Currently odmltables only supports XML files with the file ending `.odml`. Therefore, 
    any odML document that is passed from odml-ui to one of the supported odmltables 
    wizards is saved as an XML file with the ".odml" file ending in the temporary odML 
    folder also used for the terminologies and then passed along to odmltables.

## Fixes
- Fixes various breaking changes introduced in python-odml during the v1.3 - v1.4 
    transition. See #120 and #124.
- Fixes that all files were saved as `XML`, even when the `JSON` or `YAML` formats had 
    been selected. See #62.
- Fixes that all multiple values of a Property can be overwritten by the `pseudo_value` 
    placeholder text `n/a` by just escaping the edit state. See #69.
- Fixes that multiple values of a Property were only accessible after a refresh of the 
    "Property View". See #64.
- Fixes a Value error when its content was starting with "<". See #65
- Fixes the Wizard author display. See #53.
- Fixes missing size refresh of the "Validation Window" when the content tree has 
    updated. See #67.
- Fixes inactive entry selection in the "Validation Window". See #68.
- Fixes that loading of an invalid odML file leads to a broken document. See #57.
- Fixes an `AttributeError` when opening the validation window. See #60.
- Fixes an error message display in `EditorTab` on fail to save. See #66.
- Fixes Wizard crashes on empty repository and missing parent section. See #66.
- Fixes missing `create_pseudo_value` import in `EditorTab`. See #66.
- Fixes the validation warning character display for Python 2. See #75.
- Fixes "Section View" and "Property View" update issues when creating empty documents and 
    switching tabs. See #72 and #81.
- Removes a hardcoded breakpoint to avoid application freeze; See #108.
- Refactors code to avoid GTK deprecation warnings; See #98.


# Version 1.3.2
## Updates to dependency version handling
- In the light of future, incompatible versions of python-odml, the python-odml dependency 
    now supports a version number range (>=1.3.3, <1.4.*) on install.
- The same is true for the optional plug-in [odml-tables](
    https://github.com/INM-6/python-odmltables/) with the supported version number 
    range >=0.2.0, <=0.9.9)

Depends on [python-odml v1.3.4](https://github.com/G-Node/python-odml/releases/tag/v1.3.4).


# Version 1.3.1
## Fixes
- Single monitor startup bug.
- Potential installation issues due to import from `info.py`.
- Readme updates regarding MacOS conda installation.

Depends on [python-odml v1.3.4](https://github.com/G-Node/python-odml/releases/tag/v1.3.4).


# Version 1.3.0
First viable release since the UI functionality has been extracted from [python-odml](
    https://github.com/G-Node/python-odml).

Depends on python-odml v1.3.3.

