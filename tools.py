import os
import io
import mss
import pexpect
from PIL import Image

class ScreenTools:
    @staticmethod
    def get_screen_bytes(max_size=(1024, 768)) -> bytes:
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            sct_img = sct.grab(monitor)
            
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            
            img.thumbnail(max_size)
            
            byte_arr = io.BytesIO()
            img.save(byte_arr, format='PNG')
            return byte_arr.getvalue()

class ShellSession:
    def __init__(self):
        self.sh = pexpect.spawn('/bin/bash --norc --noprofile', cwd=os.path.expanduser('~'), encoding='utf-8', echo=False)
        self.sh.sendline('export TERM=dumb; unset PROMPT_COMMAND; export PS1="[P]\\u@\\h:\\w\\$ "')
        self.sh.expect(r'\[P\](.*?[#\$] )')
        self.prompt = self.sh.match.group(1).strip()

    def run_command(self, cmd: str, timeout=100) -> str:
        self.sh.sendline(cmd)
        try:
            self.sh.expect(r'\[P\](.*?[#\$] )', timeout=timeout)
            self.prompt = self.sh.match.group(1).strip()
            return self.sh.before.strip()
        except pexpect.TIMEOUT:
            return "[Timeout]"

    def get_full_form(self, cmd=None) -> str:
        if not cmd:
            return self.prompt
        return f"```bash\n{self.run_command(cmd)}\n{self.prompt}\n```"