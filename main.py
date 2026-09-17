import threading
import uvicorn
from server import app, HOST, PORT, LOCAL_IP
from voice_client import voice_client_loop, run_registration
from broadcast import start_broadcast_listener

if __name__ == "__main__":
    reg_thread = threading.Thread(target=run_registration, daemon=True)
    reg_thread.start()
    voice_thread = threading.Thread(target=voice_client_loop, daemon=True)
    voice_thread.start()
    start_broadcast_listener(LOCAL_IP, PORT)
    print(f"🚀 Сервер + голосовой клиент запущены на http://{LOCAL_IP}:{PORT}")
    print("📡 Broadcast-обнаружение включено")
    print("💡 Говори команды!")
    uvicorn.run(app, host=HOST, port=PORT)
