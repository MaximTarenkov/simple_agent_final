from client import Client
from tools import ScreenTools, ShellSession
from google.genai import types

class Agent:
    def __init__(self, history: list = [], model_name: str = "gemini/gemini-flash-latest", preset="default", prompt=""):
        self.client = Client(history=history, model_name=model_name, preset=preset, prompt=prompt)
        self.history = self.client.history
        self.shell = ShellSession()

        self.tools = {
            0: (ScreenTools.get_screen_bytes, False),
            1: (self.shell.get_full_form, True)
        }

    def _execute_tool(self, func_id: int, args: str) -> str:
        if func_id not in self.tools:
            return f"Error: Tool ID {func_id} not found"

        func, needs_args = self.tools[func_id]
        
        print(f"[Agent] Executing tool {func_id} ID with args: {args}")

        try:
            result = func(args) if needs_args else func()
            
            return result
            
        except Exception as e:
            return f"Error executing tool: {e}"


    def chat(self, t=0.7, thinking_budget=-1, loop=1):
            response = None # Инициализация переменной
            
            for _ in range(loop):
                response = self.client.generate(t=t, thinking_budget=thinking_budget)

                print(response)

                func_id, args = self.client.check_function(response)

                # Если модель не хочет вызывать функцию — возвращаем ответ сразу
                if func_id is None:
                    return response 

                print(f"Finded {func_id} ID tool")
                
                tool_result = self._execute_tool(func_id, args)
                print(tool_result)

                self.client.add_message(tool_result, "u")
            
            # Если цикл закончился (достигнут лимит шагов), возвращаем последний полученный ответ
            return response