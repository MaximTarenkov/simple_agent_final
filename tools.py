import subprocess
import time
import fcntl
import os
import io
import mss
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
        home_dir = os.path.expanduser("~")

        self.process = subprocess.Popen(
            ["/bin/bash"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, # Ошибки тоже в stdout
            text=True,
            bufsize=0,
            shell=False,
            cwd=home_dir

        )
        # Non-blocking IO magic
        fd = self.process.stdout.fileno()
        fl = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

    def run_command(self, cmd: str, timeout=100000) -> str:
        sentinel = "___END_MARKER___"
        full_cmd = f"{cmd}; echo '{sentinel}'\n"
        
        try:
            self.process.stdin.write(full_cmd)
            self.process.stdin.flush()
        except BrokenPipeError:
            return "Error: Bash process died. Please restart agent."

        output = []
        start_time = time.time()
        
        while True:
            if time.time() - start_time > timeout:
                output.append("\n[Timeout]")
                break
            try:
                chunk = self.process.stdout.read()
                if chunk:
                    output.append(chunk)
                    if sentinel in "".join(output):
                        break
            except Exception:
                time.sleep(0.05)
                
        result = "".join(output).replace(f"{sentinel}\n", "").replace(sentinel, "").strip()

        return result

    def get_full_form(self, cmd=None):
        user = self.run_command("whoami").strip()
        path = self.run_command("pwd").strip()
        
        prompt = f"{user}@fedora:{path}$"
        
        if cmd is None: 
            return prompt
            
        cmd_output = self.run_command(cmd)
        
        return f"```bash \n{cmd_output}\n{prompt}\n```"