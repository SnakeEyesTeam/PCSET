import threading
import uvicorn
from server import app, HOST, PORT
from voice_client import voice_client_loop, run_registration

if __name__ == "__main__":
    reg_thread = threading.Thread(target=run_registration, daemon=True)
    reg_thread.start()

    voice_thread = threading.Thread(target=voice_client_loop, daemon=True)
    voice_thread.start()

    print(f"🚀 Сервер + голосовой клиент запущены на http://{HOST}:{PORT}")
    print("💡 Говори команды!")

    uvicorn.run(app, host=HOST, port=PORT)
