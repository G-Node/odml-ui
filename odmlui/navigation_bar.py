"""
'navigation_bar' contains the 'NavigationBar' class.

This class provides functionality to browse from
a currently selected model object to the document root.
"""

import pygtkcompat

import gtk

pygtkcompat.enable()
pygtkcompat.enable_gtk(version='3.0')


class NavigationBar(gtk.Label):
    """
    The NavigationBar widget provides an interactive
    link list from the Document root of the currently
    active Document to the object that is currently
    selected in the data model of the main application window.

    Activating any of the links selects the respective object
    and updates the application window accordingly.
    """
    def __init__(self, *args, **kargs):
        super(NavigationBar, self).__init__(*args, **kargs)
        self._document = None
        self._current_object = None
        self._current_hierarchy = []

        self.show()
        self.set_use_markup(True)
        self.set_justify(gtk.JUSTIFY_RIGHT)
        # all free space left, and most top of widget
        self.set_alignment(1, 0.9)
        self.connect("activate-link", self.switch)
        self.possible_move = None

    @property
    def document(self):
        """
        :return: The currently active document.
        """
        return self._document

    @document.setter
    def document(self, doc):
        if self._document is not None:
            self._document.remove_change_handler(self.on_section_changed)

        self._document = doc
        self.set_model(doc)
        doc.add_change_handler(self.on_section_changed)

    @property
    def current_object(self):
        """
        :return: The currently selected object.
        """
        return self._current_object

    @current_object.setter
    def current_object(self, obj):
        """
        Update the internal selected object with provided *obj*
        and update the view accordingly.
        """
        self._current_object = obj
        self.update_display()
        self.on_selection_change(obj)

    def switch(self, _, path):
        """
        Retrieve the object corresponding to a provided path and
        make it the selected one, updating the view. If no path
        was provided use the NavigationBar's document as a
        fallback object to update the view.

        Called if a link in the NavigationBar's Label widget is clicked.
        """
        if path:
            path = [int(i) for i in path.split(":")]
            obj = self._document.from_path(path)
        else:
            obj = self._document
        self.current_object = obj
        return True

    def set_model(self, obj):
        """
        Show the hierarchy for object *obj* and make it
        the selected one, updating the view.
        """
        self._current_hierarchy = [obj]

        cur = obj
        while hasattr(obj, "parent") and obj.parent is not None:
            obj = obj.parent
            self._current_hierarchy.append(obj)

        self.current_object = cur

    def update_display(self):
        """
        Update the NavigationBar's label text with a
        list of object links from the Document root
        to the currently selected object.
        """
        names = []
        cur = self._current_object
        for obj in self._current_hierarchy:
            name = "Document"
            if hasattr(obj, "name"):
                name = obj.name
            elif hasattr(obj, "value"):
                name = obj.get_display()

            names.append((("<b>%s</b>" if obj is cur else "%s") % name,
                          ":".join([str(i) for i in obj.to_path()])))

        self.set_markup("Attributes | " + ": ".join(
            ['<a href="%s">%s</a>' % (path, name) for name, path in names[::-1]]
            ) + " ")

    def on_selection_change(self, obj):
        """
        Called whenever a new object *obj* in the underlying
        data model is selected.

        The actual method is set on the class at the point of usage.
        """
        pass

    def on_section_changed(self, context):
        """
        Refresh the NavigationBar display after the content
        of the currently displayed document has been changed.
        """
        if context.cur is not self._document:
            return

        # Handle only post change events
        if not context.post_change:
            return

        if context.action == "set":
            name, _ = context.val
            if name != "name":
                return

            for obj in self._current_hierarchy:
                if context.obj is obj:
                    self.update_display()

        if context.action == "remove":
            # an object is removed, two reasons possible:
            # a) move (an append-action will take care of everything later,
            #    however we don't know yet)
            # b) remove
            for obj in self._current_hierarchy:
                if context.val is obj:
                    self.possible_move = (obj, self.current_object)
                    # set the view to the parent
                    self.set_model(context.obj)

        if context.action in ["append", "insert"]:
            if self.possible_move is None:
                return
            obj, cur = self.possible_move

            if context.val is obj:
                self.set_model(cur)
            self.possible_move = None
