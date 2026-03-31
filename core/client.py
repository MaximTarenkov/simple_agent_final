import os
import re
import base64
import litellm

litellm.drop_params = True


class Client:
    def __init__(
        self,
        history,
        model_name: str = "gemini/gemini-flash-latest",
        tool_names: list = None,
        preset: str = "default",
        prompt: str = "",
    ):
        self.history = history if history is not None else []
        self.model_name = model_name
        tool_names = tool_names or []

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.system_prompt = ""

        if preset == "default":
            self.system_prompt = " "
        elif preset == "tools":
            base_path = os.path.join(base_dir, "prompts", "tools.txt")
            if os.path.exists(base_path):
                with open(base_path, encoding="utf-8") as f:
                    self.system_prompt = f.read()

            for tool in tool_names:
                tool_path = os.path.join(base_dir, "prompts", f"{tool}.txt")
                if os.path.exists(tool_path):
                    with open(tool_path, encoding="utf-8") as f:
                        self.system_prompt += f"\n{f.read()}"
        elif preset == "custom":
            self.system_prompt = prompt
            if not prompt:
                print(
                    """Custom system prompt is undefined. Use the "default" or "tools" preset, or define the "prompt" argument."""
                )

    def _build_history(self, raw_history: list) -> list:
        messages = [{"role": "system", "content": self.system_prompt}]

        for role_id, message_data in raw_history:
            role_str = (
                "assistant"
                if str(role_id) in ["0", "m", "model", "assistant"]
                else "user"
            )

            parts = []
            if not isinstance(message_data, list):
                message_data = [message_data]

            for item in message_data:
                if isinstance(item, bytes):
                    b64_img = base64.b64encode(item).decode("utf-8")
                    parts.append(
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{b64_img}"},
                        }
                    )
                else:
                    parts.append({"type": "text", "text": str(item)})

            if len(parts) == 1 and parts[0]["type"] == "text":
                messages.append({"role": role_str, "content": parts[0]["text"]})
            else:
                messages.append({"role": role_str, "content": parts})

        return messages

    def add_message(self, content, role="u"):
        if content is None:
            raise ValueError("Content is None!")
        self.history.append([role, content])

    def check_function(self, text: str):
        if not text:
            return None, None

        call_match = re.search(
            r"<call[^>]*>(.*?)</call>", text, re.DOTALL | re.IGNORECASE
        )
        if not call_match:
            return None, None

        call_block = call_match.group(1)

        name_match = re.search(
            r"<name[^>]*>\s*(.*?)\s*</name>", call_block, re.DOTALL | re.IGNORECASE
        )
        if not name_match:
            return None, None

        func_name = name_match.group(1).strip()

        args_match = re.search(
            r"<args[^>]*>\s*(.*?)\s*</args>", call_block, re.DOTALL | re.IGNORECASE
        )
        args = args_match.group(1).strip() if args_match else None

        return func_name, args

    def generate(self, t=0.7, thinking_budget=0) -> str:
        messages = self._build_history(self.history)

        kwargs = {"model": self.model_name, "messages": messages, "temperature": t}
        if thinking_budget > 0:
            kwargs["thinking"] = {"type": "enabled", "budget_tokens": thinking_budget}

        response = litellm.completion(**kwargs)

        msg = response.choices[0].message
        reasoning = getattr(msg, "reasoning_content", None)
        text_resp = msg.content or ""

        if reasoning:
            text_resp = f"<thought>\n{reasoning}\n</thought>\n\n{text_resp}"

        self.add_message(text_resp, "m")
        return text_resp
