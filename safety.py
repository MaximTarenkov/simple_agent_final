class Safety:
    def __init__(self, agent, confirm_mode="auto"):
        self.agent = agent
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

    def confirm(self):
        while self._pending:
            task, *args = self._pending
            self._pending = None

            if task == "_step":
                if self._state["loops"] <= 0:
                    return self._state["res"]
                last_msg = (
                    str(self.agent.client.history[-1][1])
                    if self.agent.client.history
                    else ""
                )
                if any(w in last_msg for w in self._bl_in):
                    self._pending = ("_do_gen",)
                    return "Blocked input."
                self._pending = ("_do_gen",)

            elif task == "_do_gen":
                resp = self.agent.client.generate(
                    t=self._state["t"], thinking_budget=self._state["tb"]
                )
                self._state["res"] = resp
                if any(w in resp for w in self._bl_out):
                    self._pending = ("_process", resp)
                    return "Blocked output."
                self._pending = ("_process", resp)

            elif task == "_process":
                func_name, fargs = self.agent.client.check_function(args[0])
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
                res = self.agent._execute_tool(args[0], args[1])
                print(res)
                if self.confirm_mode in ["result", "all"]:
                    self._pending = ("_add", res)
                    return "Pending result."
                self._pending = ("_add", res)

            elif task == "_add":
                self.agent.client.add_message(args[0], "u")
                self._state["loops"] -= 1
                self._pending = ("_step",)

        return self._state.get("res")
