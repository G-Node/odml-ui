import pygtkcompat

import gtk

pygtkcompat.enable()
pygtkcompat.enable_gtk(version='3.0')


class MessageDialog(gtk.MessageDialog):

    def __init__(self, parent, primary_msg, secondary_msg):
        super(MessageDialog, self).__init__()
        self.add_button('OK', 1)
        self.set_property('text', primary_msg)
        self.set_property('secondary-text', secondary_msg)
        self.set_transient_for(parent)

    def display(self):
        self.run()
        self.destroy()


class ErrorDialog(MessageDialog):

    def __init__(self, parent, primary_msg, secondary_msg):
        super(ErrorDialog, self).__init__(parent, primary_msg, secondary_msg)
        self.set_property('message-type', gtk.MessageType.ERROR)
        self.display()


class InfoDialog(MessageDialog):

    def __init__(self, parent, primary_msg, secondary_msg):
        super(InfoDialog, self).__init__(parent, primary_msg, secondary_msg)
        self.set_property('message-type', gtk.MessageType.INFO)
        self.display()


class WarnDialog(MessageDialog):

    def __init__(self, parent, primary_msg, secondary_msg):
        super(WarnDialog, self).__init__(parent, primary_msg, secondary_msg)
        self.set_property('message-type', gtk.MessageType.WARNING)
        self.display()


class DecisionDialog(gtk.MessageDialog):
    """
    A decision dialog window providing
    - Window title
    - Message
    - Secondary message
    - OK and Cancel button
    """

    def __init__(self, parent, title, primary_msg, secondary_msg):
        super(DecisionDialog, self).__init__()
        self.title = title
        self.set_property('text', primary_msg)
        self.set_property('secondary-text', secondary_msg)
        self.set_transient_for(parent)
        self.add_button("Cancel", gtk.ResponseType.CANCEL)
        self.add_button("Ok", gtk.ResponseType.OK)

    def display(self):
        response = self.run()
        self.destroy()
        if response == gtk.ResponseType.OK:
            return True
        return False


class WaitDialog(gtk.MessageDialog):

    def __init__(self, parent, primary_msg, secondary_msg):
        super(WaitDialog, self).__init__()
        self.set_property('text', primary_msg)
        self.set_property('secondary-text', secondary_msg)
        self.set_transient_for(parent)

    def change(self, msg):
        self.set_property('secondary-text', msg)
