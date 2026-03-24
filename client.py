import os
import re
from google import genai
from google.genai import types


class Client:
    def __init__(self, history: list = [], model_name: str = "gemini-3.1-flash-lite-preview", prompt_preset: str = "default", prompt: str = ""):
        self.history = history
        self.client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
        self.model_name = model_name
        if prompt_preset == "default":
            self.system_prompt = " "
        if prompt_preset == "tools":
            self.system_prompt = """
            Ты системный агент.
            Ты можешь вызывать только одну функцию в одном сообщении. Вызывай в последней строке.
            Не запускай интерактивные программы типа nano, vim, python console.

            Формат вызова функций: /call_function name(ARGS)
            
            1. get_screen() - функция для получения скриншота в чат. Делает просто сырой скриншот (практически никогда не нужен). 
            /call_function get_screen() 
            
            2. terminal() Позволяет работать с bash системы.
            /call_function terminal(ls)
            /call_function terminal(echo "hello")

            Примечание: если аргумент многострочный, то можно записать функцию так:

            /call_function
            ```terminal
            #начало аргумента
            ... тут какой-то текст ...
            #конец аргумента
            ```
            """
        if prompt_preset == "custom":
            if prompt == "": print("""Custom system prompt is undefined. Use the "default" or "tools" preset, or define the "prompt" argument.""")
            else: self.system_prompt = prompt


    def _build_history(self, raw_history: list) -> list[types.Content]:
        contents = []
        
        for role_id, message_data in raw_history:
            role_id = str(role_id)
            if role_id in ["0", "m", "model", "assistant"]: role_str = 'model'  
            elif role_id in ["1", "u", "user"]: role_str = 'user'
            else: raise ValueError(f"Unknown role: {role_id}. Use correct role.")
            
            parts = []
            
            if not isinstance(message_data, list):
                message_data = [message_data]

            for item in message_data:
                if isinstance(item, bytes):
                    part = types.Part.from_bytes(data=item, mime_type="image/png")
                    parts.append(part)
                else:
                    part = types.Part.from_text(text=str(item))
                    parts.append(part)

            content = types.Content(role=role_str, parts=parts)
            contents.append(content)

        return contents

    def add_message(self, content, role='u'):
        if content is None: raise ValueError("Content is None!")
        self.history.append([role, content])
    

    def check_function(self, text: str):
        if not text: return None, None

        match = re.search(r"/call_function\s+(\w+)\s*\((.*)\)", text, re.DOTALL)

        if match:
            func_name = match.group(1)
            args = match.group(2).strip()

            if len(args) >= 2 and (
                (args.startswith('"') and args.endswith('"')) or 
                (args.startswith("'") and args.endswith("'"))
            ):
                args = args[1:-1]

            if func_name in ["get_screen", "screen", "screenshot"]: return 0, None

            if func_name in ["terminal", "bash", "run", "cmd"]: return 1, args

        return None, None


    def generate(self, t=0.7, thinking_budget=0) -> list:
        contents = self._build_history(self.history)
        
        gen_config = types.GenerateContentConfig(
                temperature=t,
                thinking_config=types.ThinkingConfig(thinking_budget=thinking_budget),
                system_instruction=[types.Part.from_text(text=self.system_prompt),],
            )

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=gen_config
        )

        text_resp = response.text if response.text else " "
        
        self.add_message(text_resp, "m")
        
        return text_resp