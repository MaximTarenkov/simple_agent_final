import io
import mss
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
