import threading
import time

class IloResponseEvent(threading.Event):
    def __init__(self, code: str, hostname: str, debug: bool):
        super().__init__()
        self.code = code
        self.hostname = hostname
        self._debug = debug

    def set(self):
        if not self.is_set() and self._debug:
            print(f"[EVENT] <{self.code}> resolved for {self.hostname}")
        super().set()

    def clear(self):
        if self._debug:
            print(f"[EVENT] <{self.code}> clear")
        super().clear()

    def wait(self, timeout=None):
        start = time.time()
        if self._debug:
            print(f"Waiting for <{self.code}>")
        result = super().wait(timeout)
        duration = time.time() - start

        if not result:
            if self._debug:
                print(f"[TIMEOUT] <{self.code}> failed after {duration:.2f}s")
            raise TimeoutError

        return result
