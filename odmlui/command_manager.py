"""
'command_manager' contains the 'CommandManager' class.

This class provides the core functionality of re- and undo
actions per tab / document in the application.
"""


class CommandManager(object):
    """
    The CommandManager class provides a re- and undo-stack
    of commands and the methods to properly apply the
    commands in each stack.
    """
    def __init__(self):
        self.undo_stack = []
        self.redo_stack = []

    def execute(self, cmd, redo=False):
        """
        *execute* runs a given command *cmd* and on
        success adds it to the undo stack.

        :param cmd: odmlui.Command object
        :param redo: Resets the redo stack if True
        """
        if not redo:
            self.redo_stack = []
            self.enable_redo(enable=False)

        try:
            cmd()
        except Exception as err:
            self.error_func(err)
            raise

        self.undo_stack.append(cmd)
        self.enable_undo()

    def undo(self):
        """
        *undo* removes the last Command object from the
        undo stack, adds it to the redo stack and executes
        the undo method of the Command object.
        """
        cmd = self.undo_stack.pop()
        self.redo_stack.append(cmd)

        if not self.undo_stack:
            self.enable_undo(enable=False)

        self.enable_redo()

        try:
            cmd.undo()
        except Exception as err:
            self.error_func(err)
            raise

    def redo(self):
        """
        *redo* removes the last Command object from the
        redo stack and hands it over to the execute method
        where it is run and added to the undo stack.
        """
        self.execute(self.redo_stack.pop(), redo=True)

        if not self.redo_stack:
            self.enable_redo(enable=False)

        self.enable_undo()

    def reset(self):
        """
        *reset* clears all objects from both undo and redo stack.
        """
        self.enable_undo(enable=False)
        self.enable_redo(enable=False)
        self.undo_stack = []
        self.redo_stack = []

    def __len__(self):
        return len(self.undo_stack)

    @property
    def is_modified(self):
        """
        *is_modified* returns True if the undo stack contains any object.
        """
        return bool(self.undo_stack)

    can_undo = is_modified

    @property
    def can_redo(self):
        """*can_redo* returns True if the redo stack contains any object"""
        return bool(self.redo_stack)

    def enable_undo(self, enable=True):
        """
        The actual method is set on the class at the point of usage.
        """
        pass

    def enable_redo(self, enable=True):
        """
        The actual method is set on the class at the point of usage.
        """
        pass

    def error_func(self, err):
        """
        *error_func* provides feedback to the user, if an error occurs.

        The actual method is set on the class at the point of usage.
        """
        pass
