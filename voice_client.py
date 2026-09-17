# voice_client.py
import os
import time
import socket
import requests
import speech_recognition as sr

PORT = 8080
PHONE_NAME = "MyPhone"

def get_local_ip() -> str:
    """
    Возвращает локальный IP, предпочитая 192.168.x.x.
    """
    try:
        hostname = socket.gethostname()
        infos = socket.getaddrinfo(hostname, None, socket.AF_INET)
        for info in infos:
            ip = info[4][0]
            if ip.startswith("192.168."):
                return ip
    except Exception:
        pass

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            if ip.startswith("192.168."):
                return ip
        except OSError:
            pass

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
        except OSError:
            return "127.0.0.1"

LOCAL_IP = get_local_ip()
SERVER_URL = f"http://{LOCAL_IP}:{PORT}"

def get_phone_ip() -> str | None:
    """Получает актуальный IP телефона из /devices на сервере."""
    try:
        resp = requests.get(f"{SERVER_URL}/devices", timeout=5)
        devices_list = resp.json()
        for d in devices_list:
            if d.get("name") == PHONE_NAME:
                return d.get("ip")
    except Exception:
        pass
    return None

def send_command(action: str, payload: str | None = None):
    phone_ip = get_phone_ip()
    if not phone_ip:
        print("⚠️ Телефон не зарегистрирован. Жду регистрации...")
        return

    print(f"Отправляем: {action} для {phone_ip}")
    data = {"cmd": action, "target_ip": phone_ip}
    if payload is not None:
        data["payload"] = payload

    try:
        resp = requests.post(f"{SERVER_URL}/command", json=data, timeout=5)
        print("Статус:", resp.status_code)
    except requests.exceptions.ConnectionError:
        print("❌ Не удалось подключиться. Проверь, запущен ли сервер.")
    except Exception as e:
        print("Ошибка:", e)

def run_registration():
    """Фоновая регистрация ПК на сервере."""
    while True:
        try:
            data = {
                "ip": get_local_ip(),
                "port": PORT,
                "name": "MyDevPC"
            }
            requests.post(f"{SERVER_URL}/register", json=data, timeout=5)
        except Exception:
            pass
        time.sleep(30)

def voice_client_loop():
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
        elif cmd == "открыть telegram":
            send_command("open_tg_app")
        elif cmd == "стоп":
            os._exit(0)
        else:
            print(f"Неверная команда: {cmd!r}. Попробуй снова.")
