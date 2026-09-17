import socket
import threading

BROADCAST_PORT = 55555

def start_broadcast_listener(server_ip: str, port: int = 8080):
    """
    Слушает UDP broadcast на BROADCAST_PORT.
    Когда кто-то спрашивает 'WHO_IS_SERVER' — отвечает 'I_AM_SERVER:<ip>:<port>'.
    Запускается в daemon-потоке.
    """
    def _listener():
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.bind(("0.0.0.0", BROADCAST_PORT))

        print(f"📡 Broadcast-слушатель запущен на UDP-порту {BROADCAST_PORT}")

        while True:
            try:
                data, addr = sock.recvfrom(1024)
                msg = data.decode("utf-8", errors="ignore").strip()
                if msg == "WHO_IS_SERVER":
                    response = f"I_AM_SERVER:{server_ip}:{port}"
                    sock.sendto(response.encode("utf-8"), addr)
                    print(f"📡 Ответили на broadcast от {addr[0]}: {response}")
            except Exception as e:
                print(f"⚠️ Ошибка broadcast-слушателя: {e}")

    thread = threading.Thread(target=_listener, daemon=True)
    thread.start()
    return thread