import threading
import websocket
from typing import Callable

from ..ws import _co_send_msg


WS_PORT = 4583


class WiFiTransport:
    on_received: Callable[[str], None] | None = None

    def __init__(self, address: str):
        self.on_received: Callable[[str], None] | None = None
        self.address = address

        self._recv_thread = None
        self._recv_thread_running = False

        self._ws = None

    def connect(self) -> bool:
        self._ws = websocket.create_connection(f"ws://{self.address}:{WS_PORT}")

        # Vérifie si un ancien thread de réception est actif et l'arrête avant d'en démarrer un nouveau
        if self._recv_thread and self._recv_thread.is_alive():
            # print("Stopping the previous reception thread...")
            self._stop_reception()

        # Start the WebSocket de reception in a separate thread
        self._recv_thread_running = True
        self._recv_thread = threading.Thread(target=self._web_socket_receive)

        self._recv_thread.start()
        return True

    def disconnect(self) -> None:
        if self._ws is not None:
            _co_send_msg(self._ws, "<>")
            self._ws.close()
        self._stop_reception()

    def send(self, message: str) -> None:
        if self._ws is None:
            return

        self._ws.send(message)

    def poll(self) -> None:
        pass

    def _stop_reception(self):
        """
        Stop the WebSocket reception thread and close the connection.
        """
        if not self._recv_thread_running:
            return  # Si le thread est déjà arrêté, ne rien faire

        print("Stopping reception thread...")
        self._recv_thread_running = False  # Arrêter la boucle dans le thread de réception

        if self._ws:
            try:
                if self._ws is not None and self._ws.connected:
                    self._ws.close()
                self._connect = False  # Mettre à jour l'état de connexion après la fermeture de WebSocket
                print("WebSocket successfully closed")
            except Exception as e:
                print(f"Erreur lors de la fermeture de la WebSocket: {e}")

        # if self._recv_thread and self._recv_thread.is_alive():
        if self._recv_thread:
            print("Waiting for the reception thread to stop...")
            self._recv_thread.join(timeout=2)

    def _web_socket_receive(self):
        """
        Thread function to continuously receive data from the WebSocket.
        Stops when recv_thread_running is set to False.
        """
        if self._ws is None:
            return
        while self._recv_thread_running:
            try:
                self._ws.settimeout(1) # Ajout d'un timeout pour que recv() ne bloque pas indéfiniment
                data = self._ws.recv() # Timeout de 1 seconde pour éviter un blocage sur recv()
                if data:
                    if '/' in data:
                        sub_trames = data.split('/')[1:-1]
                        for sub_trame in sub_trames:
                            self.on_received(f"<{sub_trame}>")
                    else:
                        if self.on_received:
                            self.on_received(data)
            except websocket.WebSocketTimeoutException:
                # Timeout atteint, continue à boucler pour vérifier recv_thread_running
                continue
            except websocket.WebSocketException as e:
                # Gestion des erreurs de WebSocket, afficher l'erreur pour le débogage
                print(f"WebSocket error: {e}")
                break

        print("Thread de réception terminé.")

    def send_binary(self, data: bytes) -> None:
        if self._ws is None:
            return
        self._ws.send(data, opcode=websocket.ABNF.OPCODE_BINARY)


    @property
    def preferred_chunk_size(self) -> int:
        return 1024
