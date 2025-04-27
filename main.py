python
import requests
import time
from datetime import datetime, timedelta
import threading

TOKEN = '8031084278:AAGghXtj3zuBHPsfVRqbTR9804holImXHiQ'
URL = f"https://api.telegram.org/bot{TOKEN}/"

tasks = [
    {'name': 'Урок китайского', 'date': '2024-04-27', 'time': '13:30'},
    {'name': 'Купить освещение', 'date': '2024-04-28', 'time': '15:00'}
]

chat_id = None

def send_message(chat_id, text):
    url = URL + "sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)

def get_updates(offset=None):
    url = URL + "getUpdates"
    if offset:
        url += f"?offset={offset}"
    response = requests.get(url, timeout=100)
    return response.json()

def morning_tasks():
    while True:
        now = datetime.now()
        if now.hour == 8 and now.minute == 0:
            today = now.strftime('%Y-%m-%d')
message = "📋 Задачи на сегодня:\n"
            for task in tasks:
                if task['date'] == today:
                    message += f"- {task['name']} в {task['time']}\n"
            if chat_id and message != "📋 Задачи на сегодня:\n":
                send_message(chat_id, message)
        time.sleep(60)

def reminder_tasks():
    while True:
        now = datetime.now()
        today = now.strftime('%Y-%m-%d')
        for task in tasks:
            task_time = datetime.strptime(f"{task['date']} {task['time']}", "%Y-%m-%d %H:%M")
            if timedelta(minutes=19) < (task_time - now) <= timedelta(minutes=20):
                if chat_id:
                    send_message(chat_id, f"🔔 Через 20 минут начнется задача: {task['name']} в {task['time']}!")
        time.sleep(60)

def main():
    global chat_id
    last_update_id = None
    print("Бот запущен! ✅")
    while True:
        updates = get_updates(last_update_id)
        if updates.get("result"):
            for item in updates["result"]:
                last_update_id = item["update_id"] + 1
                chat_id = item["message"]["chat"]["id"]
                message_text = item["message"]["text"]
                if message_text.lower() in ["/start", "привет", "hello"]:
send_message(chat_id, "Бот на связи! 🚀")
                else:
                    send_message(chat_id, f"Ты написал: {message_text}")
        time.sleep(2)

if name == 'main':
    threading.Thread(target=morning_tasks).start()
    threading.Thread(target=reminder_tasks).start()
    main()
