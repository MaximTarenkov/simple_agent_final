import json, time
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel


def tail_json(path):
    console = Console()
    idx = 0
    while True:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if len(data) > idx:
                for r, c in data[idx:]:
                    content = (
                        c.replace("<thought>", "> Thought\n")
                        .replace("</thought>", "")
                        .replace("<call>", "```xml\n")
                        .replace("</call>", "```")
                    )
                    console.print(
                        Panel(
                            Markdown(content),
                            title="User" if r == "u" else "Assistant",
                            border_style="green" if r == "u" else "blue",
                        )
                    )
                idx = len(data)
        except (json.JSONDecodeError, PermissionError, FileNotFoundError):
            pass
        time.sleep(0.5)


if __name__ == "__main__":
    tail_json("chat.json")
