# client_voice.py
import threading
import time
import socket
import requests
import os
import speech_recognition as sr

# --- КОНФИГУРАЦИЯ (должна совпадать с server.py) ---
SERVER_URL = "http://192.168.0.101:8080"  # IP твоего ПК
PHONE_IP = "192.168.0.55"               # IP телефона

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

def run_registration():
    """Фоновая регистрация сервера в самом себе"""
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    SERVER_REGISTRY_URL = f"http://{ip}:8080/register"
    
    while True:
        try:
            data = {"ip": ip, "port": 8080, "name": "MyDevPC"}
            requests.post(SERVER_REGISTRY_URL, json=data, timeout=5)
        except Exception:
            pass
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
        elif cmd == "открыть telegram":
            send_command("open_tg_app")
        elif cmd == "стоп":
            os._exit(0)
        else:
            print(f"Неверная команда: {cmd!r}. Попробуй снова.")

if __name__ == "__main__":
    reg_thread = threading.Thread(target=run_registration, daemon=True)
    reg_thread.start()

    client_thread = threading.Thread(target=voice_client_loop, daemon=True)
    client_thread.start()

    print("💡 Голосовой клиент работает в фоне. Говори команды!")

    # Клиент не запускает uvicorn — он только отправляет команды
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        os._exit(0)
