import os
import re
import base64
import litellm

class Client:
    def __init__(self, history: list = [], model_name: str = "gemini/gemini-flash-latest", preset: str = "default", prompt: str = ""):
        self.history = history
        self.model_name = model_name

        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        if preset == "default":
            self.system_prompt = " "
        elif preset == "tools":
            self.system_prompt = open(os.path.join(base_dir, "prompts", "tools.txt"), encoding='utf-8').read()
        elif preset == "custom":
            if prompt == "":
                print("""Custom system prompt is undefined. Use the "default" or "tools" preset, or define the "prompt" argument.""")
            else:
                self.system_prompt = prompt

    def _build_history(self, raw_history: list) -> list:
        messages = [{"role": "system", "content": self.system_prompt}]
        
        for role_id, message_data in raw_history:
            role_str = 'assistant' if str(role_id) in ["0", "m", "model", "assistant"] else 'user'
            
            parts = []
            if not isinstance(message_data, list):
                message_data = [message_data]

            for item in message_data:
                if isinstance(item, bytes):
                    b64_img = base64.b64encode(item).decode('utf-8')
                    parts.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{b64_img}"}
                    })
                else:
                    parts.append({"type": "text", "text": str(item)})

            if len(parts) == 1 and parts[0]["type"] == "text":
                messages.append({"role": role_str, "content": parts[0]["text"]})
            else:
                messages.append({"role": role_str, "content": parts})

        return messages

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

    def generate(self, t=0.7, thinking_budget=0) -> str:
        messages = self._build_history(self.history)
        
        response = litellm.completion(
            model=self.model_name,
            messages=messages,
            temperature=t
        )

        text_resp = response.choices[0].message.content or " "
        
        self.add_message(text_resp, "m")
        
        return text_resp