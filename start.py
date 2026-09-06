import threading
import time
import socket
import requests
import sys,os
import speech_recognition as sr
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict

# --- КОНФИГУРАЦИЯ (Вынеси сюда все настройки) ---
SERVER_URL = "http://192.168.0.101:8080"  # IP твоего ПК
PHONE_IP = "192.168.0.55"               # IP телефона
HOST = "0.0.0.0"
PORT = 8080

app = FastAPI()

# Хранилища в памяти
devices: List[Dict] = []
commands: List[Dict] = []

# --- Модели данных ---
class CommandRequest(BaseModel):
    cmd: str
    target_ip: str

class RegisterRequest(BaseModel):
    ip: str
    port: int
    name: str

# --- Эндпоинты сервера ---

@app.post("/command")
def add_command(req: CommandRequest):
    if not req.cmd or not req.target_ip:
        raise HTTPException(status_code=400, detail="Поля cmd и target_ip обязательны")

    for c in commands:
        if c["target_ip"] == req.target_ip and not c["done"] and c["cmd"] == req.cmd:
            print(f"⚠️ Дубликат команды игнорирован: {req.cmd}")
            return {"ok": True, "id": c["id"], "msg": "duplicate"}

    cmd_id = len(commands)
    commands.append({
        "id": cmd_id,
        "cmd": req.cmd,
        "target_ip": req.target_ip,
        "timestamp": time.time(),
        "done": False
    })
    print(f"✅ Команда добавлена: {req.cmd} для {req.target_ip} (id={cmd_id})")
    return {"ok": True, "id": cmd_id}

@app.get("/commands")
def get_commands(ip: str):
    return [c for c in commands if c["target_ip"] == ip and not c["done"]]

class DoneRequest(BaseModel):
    cmd_id: int

@app.post("/done")
def mark_done(req: DoneRequest):
    print(f"📩 Получен запрос /done для id={req.cmd_id}")
    for c in commands:
        if c["id"] == req.cmd_id:
            c["done"] = True
            print(f"🏁 Команда {req.cmd_id} ВЫПОЛНЕНА")
            return {"ok": True}
    raise HTTPException(status_code=404, detail="Команда не найдена")

@app.post("/register")
def register_device(req: RegisterRequest):
    now = time.time()
    for d in devices:
        if d["ip"] == req.ip:
            d["port"] = req.port
            d["name"] = req.name
            d["last_seen"] = now
            print(f"🔄 Устройство обновлено: {req.ip} ({req.name})")
            return {"ok": True, "msg": "updated"}
    
    devices.append({
        "ip": req.ip,
        "port": req.port,
        "name": req.name,
        "last_seen": now
    })
    print(f"➕ Устройство зарегистрировано: {req.ip} ({req.name})")
    return {"ok": True}

@app.get("/devices")
async def get_devices():
    return devices

# --- Логика клиента (Голосовой ввод) ---

def run_registration():
    """Фоновая регистрация сервера в самом себе"""
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    SERVER_REGISTRY_URL = f"http://{ip}:8080/register"
    
    while True:
        try:
            data = {"ip": ip, "port": PORT, "name": "MyDevPC"}
            requests.post(SERVER_REGISTRY_URL, json=data, timeout=5)
        except Exception as e:
            pass # Игнорируем ошибки регистрации для чистоты логов
        time.sleep(30)

def voice_client_loop():
    """Бесконечный цикл прослушивания микрофона"""
    r = sr.Recognizer()
    
    while True:
        print("\n--- Ожидание команды (5 сек) ---")
        try:
            with sr.Microphone() as src:
                r.adjust_for_ambient_noise(src, duration=0.5)
                audio = r.listen(src, timeout=5, phrase_time_limit=5)
                cmd = r.recognize_google(audio, language='ru-RU').strip().lower()
                print(f"Вы сказали: {cmd}")
        except sr.WaitTimeoutError:
            continue
        except sr.UnknownValueError:
            print("Не удалось распознать речь.")
            continue
        except sr.RequestError as e:
            print(f"Ошибка сервиса Google: {e}")
            continue
        except Exception as e:
            print(f"Неожиданная ошибка микрофона: {e}")
            continue

        if cmd == "показать уведомление":
            text = input("Текст для toast: ")
            send_command(f"show_toast:{text}") 
        elif cmd == "открыть Telegram":
            send_command("open_tg_app")
        elif cmd == "стоп":
            os._exit(0)
        else:
            print(f"Неверная команда: {cmd!r}. Попробуй снова.")

def send_command(action: str, payload: str | None = None):
    print(f"Отправляем: {action} для {PHONE_IP}")
    data = {"cmd": action, "target_ip": PHONE_IP}
    if payload is not None:
        data["payload"] = payload

    try:
        resp = requests.post(
            f"{SERVER_URL}/command",
            json=data,
            timeout=5
        )
        print("Статус:", resp.status_code)
    except requests.exceptions.ConnectionError:
        print("❌ Не удалось подключиться. Проверь IP и фаервол.")
    except Exception as e:
        print("Ошибка:", e)


if __name__ == "__main__":
    reg_thread = threading.Thread(target=run_registration, daemon=True)
    reg_thread.start()

    client_thread = threading.Thread(target=voice_client_loop, daemon=True)
    client_thread.start()

    print(f"🚀 Запуск FastAPI сервера на http://{HOST}:{PORT}")
    print("💡 Голосовой клиент работает в фоне. Говори команды!")

    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
