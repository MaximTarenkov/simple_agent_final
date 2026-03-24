import inspect
from client import Client
from tools import ScreenTools, ShellSession

class Agent:
    def __init__(self, history=None, model_name: str = "gemini/gemini-flash-latest", preset="default", prompt=""):
        self.shell = ShellSession()
        
        self.tools = {
            "screen": ScreenTools.get_screen_bytes,
            "terminal": self.shell.get_full_form
        }

        self.client = Client(history=history, model_name=model_name, tool_names=list(self.tools.keys()), preset=preset, prompt=prompt)
        self.history = history if history is not None else []

    def _execute_tool(self, func_name: str, args: str):
        if func_name not in self.tools:
            return f"Error: Tool {func_name} not found"

        func = self.tools[func_name]
        
        print(f"[Agent] Executing tool {func_name} with args: {args}")

        try:
            sig = inspect.signature(func)
            return func(args) if len(sig.parameters) > 0 and args else func()
        except Exception as e:
            return f"Error executing tool: {e}"

    def chat(self, t=0.7, thinking_budget=-1, loop=1):
        response = None
        
        for _ in range(loop):
            response = self.client.generate(t=t, thinking_budget=thinking_budget)

            print(response)

            func_name, args = self.client.check_function(response)

            if func_name is None:
                return response 

            print(f"Found {func_name} tool")
            
            tool_result = self._execute_tool(func_name, args)
            print(tool_result)

            self.client.add_message(tool_result, "u")
        
        return response