import re


class Safety:
    def __init__(self, confirm_mode="auto"):
        self.confirm_mode = confirm_mode
        self._bl_in = set()
        self._bl_out = set()

    def blacklist_input(self, add=None, remove=None):
        if add:
            self._bl_in.update(add)
        if remove:
            self._bl_in.difference_update(remove)

    def blacklist_output(self, add=None, remove=None):
        if add:
            self._bl_out.update(add)
        if remove:
            self._bl_out.difference_update(remove)

    def _check_bl(self, text, bl):
        if not bl or not text:
            return False
        pattern = r"\b(?:" + "|".join(map(re.escape, bl)) + r")\b"
        return bool(re.search(pattern, text, re.IGNORECASE))

    def check_input(self, text):
        return self._check_bl(text, self._bl_in)

    def check_output(self, text):
        return self._check_bl(text, self._bl_out)

    def pending(self, stage):
        return self.confirm_mode in [stage, "all"]
