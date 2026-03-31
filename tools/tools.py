from .screen import ScreenTools
from .terminal import ShellSession
from .fcopy import Fcopy


def get_tool_registry(cwd="~"):
    shell = ShellSession(cwd=cwd)

    return {
        "screen": ScreenTools.get_screen_bytes,
        "terminal": shell.get_full_form,
        "fcopy": Fcopy.run,
        # "new_tool": NewToolClass.run,  <-- You can add a new tool
    }
