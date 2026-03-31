import shlex
from pathlib import Path


class Fcopy:
    @staticmethod
    def run(args: str = "") -> str:
        p_args = shlex.split(args or "")
        rec = "-R" in p_args
        ext = next((a[1:] for a in p_args if a.startswith("-") and a != "-R"), "")
        paths = [a for a in p_args if not a.startswith("-")]
        out = []

        for path in paths:
            p = Path(path)
            if rec:
                if p.is_dir():
                    for f in p.rglob("*"):
                        if f.is_file() and (not ext or f.suffix.lstrip(".") == ext):
                            if not any(
                                x.startswith(".") and x not in (".", "..")
                                for x in f.parts
                            ):
                                text = f.read_text(encoding="utf-8", errors="replace")
                                msg = "\n[Truncated]" if len(text) > 8192 else ""
                                out.append(f"```{f}\n{text[:8192]}{msg}\n```")
                else:
                    out.append(f"{path} is not a directory")
            else:
                if ext and p.suffix.lstrip(".") != ext:
                    continue
                if p.is_file():
                    text = p.read_text(encoding="utf-8", errors="replace")
                    msg = "\n[Truncated]" if len(text) > 8192 else ""
                    out.append(f"```{p}\n{text[:8192]}{msg}\n```")
                else:
                    out.append(f"{path} not found")

        return "\n\n".join(out) or "No files processed"
