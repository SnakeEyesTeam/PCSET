# server.py
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict

# --- КОНФИГУРАЦИЯ ---
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

class DoneRequest(BaseModel):
    cmd_id: int

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

if __name__ == "__main__":
    import uvicorn
    print(f"🚀 Запуск FastAPI сервера на http://{HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)
