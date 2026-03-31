import os
import io
import mss
import pexpect
import shlex
from pathlib import Path
from PIL import Image


class ScreenTools:
    @staticmethod
    def get_screen_bytes(args: str = "") -> bytes:
        with mss.mss() as sct:
            monitor = sct.monitors[0]
            sct_img = sct.grab(monitor)

            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            img.thumbnail((1024, 768))

            byte_arr = io.BytesIO()
            img.save(byte_arr, format="PNG")
            return byte_arr.getvalue()


class ShellSession:
    def __init__(self):
        self.sh = pexpect.spawn(
            "/bin/bash --norc --noprofile", encoding="utf-8", echo=False
        )
        init_cmd = (
            "export TERM=dumb; unset PROMPT_COMMAND; "
            'if [ -n "$CONDA_PREFIX" ]; then '
            'export PATH=$(echo $PATH | tr ":" "\\n" | grep -vF "$CONDA_PREFIX/bin" | tr "\\n" ":" | sed "s/:$//"); '
            "fi; "
            "unset CONDA_PREFIX CONDA_DEFAULT_ENV CONDA_SHLVL; "
            'export PS1="[P]\\u@\\h:\\w\\$ "'
        )
        self.sh.sendline(init_cmd)
        self.sh.expect(r"\[P\](.*?[#\$] )")
        self.prompt = self.sh.match.group(1).strip()

    def run_command(self, cmd: str, timeout=100) -> str:
        self.sh.sendline(cmd)
        try:
            self.sh.expect(r"\[P\](.*?[#\$] )", timeout=timeout)
            self.prompt = self.sh.match.group(1).strip()
            return self.sh.before.strip()
        except pexpect.TIMEOUT:
            return "[Timeout]"

    def get_full_form(self, cmd=None) -> str:
        if not cmd:
            return self.prompt
        return f"```bash\n{self.run_command(cmd)}\n{self.prompt}\n```"


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
                                out.append(
                                    f"```{f}\n{f.read_text(encoding='utf-8', errors='replace')}\n```"
                                )
                else:
                    out.append(f"{path} is not a directory")
            else:
                if ext and p.suffix.lstrip(".") != ext:
                    continue
                if p.is_file():
                    if not any(
                        x.startswith(".") and x not in (".", "..") for x in p.parts
                    ):
                        out.append(
                            f"```{p}\n{p.read_text(encoding='utf-8', errors='replace')}\n```"
                        )
                else:
                    out.append(f"{path} not found")

        return "\n\n".join(out) or "No files processed"
