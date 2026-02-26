from functools import wraps
import pyperclip


@wraps(pyperclip.copy)
def copy_to_clipboard(text: str) -> None:
    if not pyperclip.is_available:
        return

    copy, _ = pyperclip.determine_clipboard()

    if copy:
        pyperclip.copy(text)
