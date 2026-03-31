import os
from client import Client
from tools import ScreenTools, ShellSession, Fcopy


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

        self.confirm_mode = confirm_mode
        self._bl_in = set()
        self._bl_out = set()
        self._pending = None
        self._state = {}

    def blacklist_input(self, add=None, remove=None):
        if add:
            self._bl_in.update(add)
        if remove:
            self._bl_in.difference_update(remove)

    def blacklist_output(self, add=None, remove=None):
        if add:
            self._bl_out.update(add)
        if remove:
            self._bl_out.difference_update(remove)

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
        self._state = {"t": t, "tb": thinking_budget, "loops": loop, "res": None}
        self._pending = ("_step",)
        return self.confirm()

    def confirm(self):
        while self._pending:
            task, *args = self._pending
            self._pending = None

            if task == "_step":
                if self._state["loops"] <= 0:
                    return self._state["res"]
                last_msg = (
                    str(self.client.history[-1][1]) if self.client.history else ""
                )
                if any(w in last_msg for w in self._bl_in):
                    self._pending = ("_do_gen",)
                    return "Blocked input."
                self._pending = ("_do_gen",)

            elif task == "_do_gen":
                resp = self.client.generate(
                    t=self._state["t"], thinking_budget=self._state["tb"]
                )
                self._state["res"] = resp
                if any(w in resp for w in self._bl_out):
                    self._pending = ("_process", resp)
                    return "Blocked output."
                self._pending = ("_process", resp)

            elif task == "_process":
                func_name, fargs = self.client.check_function(args[0])
                if not func_name:
                    self._state["loops"] = 0
                    self._pending = ("_step",)
                    continue

                print(f"Found {func_name} tool")
                if self.confirm_mode in ["tool", "all"]:
                    self._pending = ("_exec", func_name, fargs)
                    return f"Pending tool: {func_name}."
                self._pending = ("_exec", func_name, fargs)

            elif task == "_exec":
                res = self._execute_tool(args[0], args[1])
                print(res)
                if self.confirm_mode in ["result", "all"]:
                    self._pending = ("_add", res)
                    return "Pending result."
                self._pending = ("_add", res)

            elif task == "_add":
                self.client.add_message(args[0], "u")
                self._state["loops"] -= 1
                self._pending = ("_step",)

        return self._state.get("res")

    def add(self, content, role="u"):
        return self.client.add_message(content, role=role)
