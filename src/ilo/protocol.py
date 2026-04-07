class IloProtocolBuffer:
    def __init__(self):
        self._buffer = ""

    def feed(self, chunk: str) -> list[str]:
        self._buffer += chunk
        trames = []

        while ">" in self._buffer:
            end_pos = self._buffer.find(">")
            start_pos = self._buffer.rfind("<", 0, end_pos)

            if start_pos != -1:
                trame = self._buffer[start_pos : end_pos + 1]

                if " " not in trame and ":" not in trame:
                    trames.append(trame)

                self._buffer = self._buffer[end_pos + 1:]
            else:
                self._buffer = self._buffer[end_pos + 1:]

        return trames
