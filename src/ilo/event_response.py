import threading
import time

class IloResponseEvent(threading.Event):
    def __init__(self, code: str, hostname: str, debug: bool):
        super().__init__()
        self.code = code
        self.hostname = hostname
        self._debug = debug

        self._start = 0

    def set(self):
        if not self.is_set() and self._debug:
            duration = time.time() - self._start
            print(f"[EVENT] <{self.code}> resolved for {self.hostname} after {duration:.2f}s")
        super().set()

    def clear(self):
        if self._debug:
            print(f"[EVENT] <{self.code}> clear")
        self._start = time.time()
        super().clear()

    def wait(self, timeout=None):
        self._start = time.time()

        if self._debug:
            print(f"[EVENT] Waiting for <{self.code}>")

        result = super().wait(timeout)

        if not result:
            if self._debug:
                duration = time.time() -  self._start
                print(f"[EVENT] <{self.code}> timeout after {duration:.2f}s")
            raise TimeoutError

        return result
