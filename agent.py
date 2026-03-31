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

        self.safety = Safety(confirm_mode=confirm_mode)
        self._generator = None

    def chat(self, t=0.7, thinking_budget=-1, loop=1):
        self._generator = self._loop(t, thinking_budget, loop)
        return self.confirm()

    def confirm(self):
        if self._generator:
            try:
                return next(self._generator)
            except StopIteration as e:
                self._generator = None
                return e.value
        return None

    def _loop(self, t, tb, loops):
        while loops > 0:
            last_msg = str(self.client.history[-1][1]) if self.client.history else ""
            if self.safety.check_input(last_msg):
                yield "Blocked input."

            resp = self.client.generate(t=t, thinking_budget=tb)

            if self.safety.check_output(resp):
                yield "Blocked output."

            func_name, fargs = self.client.check_function(resp)
            if not func_name:
                return resp

            print(f"Found {func_name} tool")
            if self.safety.pending("tool"):
                yield f"Pending tool: {func_name}."

            res = self._execute_tool(func_name, fargs)
            print(res)

            if self.safety.pending("result"):
                yield "Pending result."

            self.client.add_message(res, "u")
            loops -= 1

        return resp
