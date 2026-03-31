import os
from client import Client
from tools import ScreenTools, ShellSession, Fcopy
from safety import Safety


class Agent:
    def __init__(
        self,
        history=None,
        model_name: str = "gemini/gemini-flash-latest",
        preset="default",
        prompt="",
        cwd="~",
        tools=None,
        confirm_mode="auto",
    ):
        self.shell = ShellSession(cwd=cwd)

        all_tools = {
            "screen": ScreenTools.get_screen_bytes,
            "terminal": self.shell.get_full_form,
            "fcopy": Fcopy.run,
        }

        tool_keys = tools if tools is not None else list(all_tools.keys())
        self.tools = {k: all_tools[k] for k in tool_keys if k in all_tools}

        self.client = Client(
            history=history,
            model_name=model_name,
            tool_names=list(self.tools.keys()),
            preset=preset,
            prompt=prompt,
        )

        self.safety = Safety(self, confirm_mode=confirm_mode)

    def _execute_tool(self, func_name: str, args: str):
        if func_name not in self.tools:
            return f"Error: Tool {func_name} not found"

        func = self.tools[func_name]

        print(f"[Agent] Executing tool {func_name} with args: {args}")

        try:
            return func(args) if args is not None else func()
        except Exception as e:
            return f"Error executing tool: {e}"

    def chat(self, t=0.7, thinking_budget=-1, loop=1):
        self.safety._state = {"t": t, "tb": thinking_budget, "loops": loop, "res": None}
        self.safety._pending = ("_step",)
        return self.confirm()

    def confirm(self):
        return self.safety.confirm()

    def add(self, content, role="u"):
        return self.client.add_message(content, role=role)
