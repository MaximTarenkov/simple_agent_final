import os
import json
import pathlib
from agent import Agent


def get_files(root_path, max_depth=2, exclude=None):
    base = pathlib.Path(root_path)
    exclude = exclude or {".png", ".jpg", ".jpeg", ".svg", ".lock", ".bin"}
    files = {}

    def scan(path, depth):
        for p in sorted(path.iterdir()):
            if p.name.startswith(".") or p.suffix in exclude:
                continue
            rel = "./" + str(p.relative_to(base))
            if p.is_file():
                files[rel] = p
            if p.is_dir() and depth < max_depth:
                scan(p, depth + 1)

    scan(base, 0)
    return files


def build_map(path, base, index, depth=0, max_depth=2):
    res = ""
    base_obj = pathlib.Path(base)
    items = sorted(
        p for p in pathlib.Path(path).iterdir() if not p.name.startswith(".")
    )

    for p in items:
        rel = "./" + str(p.relative_to(base_obj))
        indent = "  " * depth

        if p.is_file() and rel in index:
            res += f"{indent}{p.name}:\n{indent}  {index[rel]}\n"
        elif p.is_dir() and depth < max_depth:
            res += f"{indent}{p.name}/\n"
            res += build_map(p, base, index, depth + 1, max_depth)

    return res


root_dir = "../../"
json_file = "repo_index.json"
prompt_path = os.path.join("../prompts", "repo_analyzer.txt")

sys_prompt = (
    open(prompt_path, encoding="utf-8").read() if os.path.exists(prompt_path) else ""
)
user_ex = input("Exclude extensions (comma separated): ")
ex_set = set(user_ex.split(",")) if user_ex else None

index = {}
if os.path.exists(json_file):
    with open(json_file, "r", encoding="utf-8") as f:
        index = json.load(f)

files = get_files(root_dir, max_depth=2, exclude=ex_set)

for rel, path_obj in files.items():
    if rel in index and index[rel] and not index[rel].startswith("Error:"):
        continue

    print(f"Processing {rel}...")

    try:
        content = path_obj.read_text(encoding="utf-8", errors="replace")
        history = [["u", f"```\n{content}\n```"]]

        agent = Agent(
            history,
            model_name="cometapi/gemini-3-flash-preview",
            preset="custom",
            prompt=sys_prompt,
        )
        resp = agent.chat()

        if not resp or str(resp).strip() == "":
            index[rel] = "Error: Empty response from model"
        else:
            index[rel] = str(resp).strip()

    except Exception as e:
        print(f"Failed {rel}: {e}")
        index[rel] = f"Error: {str(e)}"

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=4)

tree_map = build_map(root_dir, root_dir, index)
print("\nRepository map for LLM context:\n")
print(tree_map)
