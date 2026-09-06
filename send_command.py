import requests
import os, sys
import speech_recognition as sr

SERVER_URL = "http://192.168.0.101:8080"
PHONE_IP = "192.168.0.55"

r = sr.Recognizer()

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
        try:
            print("Ответ:", resp.json())
        except ValueError:
            print("Ответ (не JSON):", resp.text)
    except requests.exceptions.ConnectionError as e:
        print("❌ Не удалось подключиться. Проверь: фаервол, AP Isolation, IP ПК.")
        print(e)
    except Exception as e:
        print("Ошибка:", e)

if __name__ == "__main__":
    print("Доступные команды:")
    print("1 - show_toast:текст (показать уведомление)")
    print("2 - open_tg:username (открыть Telegram)")
    print("3 - open_tg:username (открыть Telegram)")

    with sr.Microphone() as src:
        r.adjust_for_ambient_noise(src, duration=0.5)

        try:
            audio = r.listen(src, timeout=5, phrase_time_limit=5)
            cmd = r.recognize_google(audio, language='ru-RU')
            print(f"Вы сказали: {cmd}")
        except sr.WaitTimeoutError:
            print("Не услышал ничего за отведённое время.")
            sys.exit(1)
        except sr.UnknownValueError:
            print("Не удалось распознать речь.")
            sys.exit(1)
        except sr.RequestError as e:
            print("Ошибка сервиса распознавания:", e)
            sys.exit(1)

    if cmd.strip() == "показать уведомление":
        text = input("Текст для toast: ")
        send_command(f"show_toast:{text}") 
    elif cmd.strip() == "открыть Telegram":
        send_command("open_tg_app")
    else:
        print(f"Неверная команда: {cmd!r}")
