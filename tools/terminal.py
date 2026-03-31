import os
import re
import pexpect


class ShellSession:
    def __init__(self, cwd="~"):
        self.sh = pexpect.spawn(
            "/bin/bash --norc --noprofile",
            cwd=os.path.expanduser(cwd),
            encoding="utf-8",
            echo=False,
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
            out = self.sh.before.strip()
        except pexpect.TIMEOUT:
            out = f"{self.sh.before.strip()}\n[Timeout]"

        out = out.replace("\r\n", "\n")
        out = "\n".join(line.split("\r")[-1] for line in out.split("\n"))
        return re.sub(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])", "", out)

    def get_full_form(self, cmd=None) -> str:
        if not cmd:
            return self.prompt
        return f"```bash\n{self.run_command(cmd)}\n{self.prompt}\n```"
