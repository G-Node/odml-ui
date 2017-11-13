
import odmlui

class CommandManager(object):
    def __init__(self):
        self.undo_stack = []
        self.redo_stack = []

    def execute(self, cmd, redo=False):
        if odmlui.DEBUG:
            print("run", cmd)
        if not redo:
            self.redo_stack = []
            self.enable_redo(enable=False)

        failed = False
        try:
            cmd()
        except Exception as e:
            failed = True
            self.error_func(cmd, e)

        self.undo_stack.append(cmd)
        self.enable_undo()
        if failed:
            return False

        return True

    def undo(self):
        cmd = self.undo_stack.pop()
        self.redo_stack.append(cmd)
        if len(self.undo_stack) == 0:
            self.enable_undo(enable=False)
        self.enable_redo()
        failed = False
        try:
            cmd.undo()
        except Exception as e:
            self.error_func(cmd, e)
            raise

        return True

    def redo(self):
        self.execute(self.redo_stack.pop(), redo=True)
        if len(self.redo_stack) == 0:
            self.enable_redo(enable=False)
        self.enable_undo()

    def reset(self):
        """clears the command stack"""
        self.enable_undo(enable=False)
        self.enable_redo(enable=False)
        self.undo_stack = []
        self.redo_stack = []

    def __len__(self):
        return len(self.undo_stack)

    @property
    def is_modified(self):
        return bool(self.undo_stack)

    can_undo = is_modified
    @property
    def can_redo(self):
        return bool(self.redo_stack)

    def enable_undo(self, enable=True):
        pass

    def enable_redo(self, enable=True):
        pass

