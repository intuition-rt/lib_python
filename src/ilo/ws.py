import websocket

# TODO: remove this file iwth protocol abstraction

def _co_send_msg(ws: websocket.WebSocket, message: str) -> str:
    '''
    Send a message over the WebSocket connection
    '''
    if not ws.connected:
        return "..."

    try:
        ws.send(message)
        response = ws.recv()
        print(f"Sent: {message}, Received: {response}")  # Debugging line
        return str(response)
    except Exception as e:
        print(f"Error sending message: {e}")
        return "..."


__all__ = ('_co_send_msg',)
