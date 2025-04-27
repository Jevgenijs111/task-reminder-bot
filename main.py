import json
import os
import logging
from datetime import datetime, timedelta
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = 'сюда вставь свой токен от бота'

tasks_file = 'tasks.json'

# Логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Загрузка задач
def load_tasks():
    if os.path.exists(tasks_file):
        with open(tasks_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

# Сохранение задач
def save_tasks(tasks):
    with open(tasks_file, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

# Парсинг сообщений
def parse_task(message_text):
    now = datetime.now()
    text = message_text.lower()

    if "завтра" in text:
        date = now + timedelta(days=1)
    elif "сегодня" in text:
        date = now
    elif "послезавтра" in text:
        date = now + timedelta(days=2)
    else:
        date = now

    # Поиск времени
    time_part = None
    for word in text.split():
        if ':' in word:
            try:
                time_part = datetime.strptime(word, "%H:%M").time()
                break
            except ValueError:
                continue

    if not time_part:
        time_part = datetime.strptime("09:00", "%H:%M").time()  # если время не указано, ставим 9 утра

    dt = datetime.combine(date.date(), time_part)
    task_name = message_text

    return {"name": task_name, "datetime": dt.strftime("%Y-%m-%d %H:%M"), "done": False}

# Отправка плана на день
async def send_morning_plan(context: ContextTypes.DEFAULT_TYPE):
    tasks = load_tasks()
    today = datetime.now().strftime("%Y-%m-%d")
    plan = [task for task in tasks if task['datetime'].startswith(today) and not task['done']]

    if plan:
        message = "📋 План на сегодня:\n"
        for task in plan:
            time_part = task['datetime'].split()[1]
            message += f"- {task['name']} в {time_part}\n"
        await context.bot.send_message(chat_id=context.job.chat_id, text=message)

# Спрашивать вечером
async def send_evening_check(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=context.job.chat_id, text="✅ Что ты успел сделать сегодня? Напиши:\n'Выполнил: название задачи' или 'Перенести: название задачи'")

# Проверка напоминаний
async def check_reminders(app):
    while True:
        now = datetime.now()
        tasks = load_tasks()
        for task in tasks:
            task_time = datetime.strptime(task['datetime'], "%Y-%m-%d %H:%M")
            delta = task_time - now
            if timedelta(minutes=19) < delta <= timedelta(minutes=20) and not task.get('reminded', False):
                chat_id = task.get('chat_id')
                if chat_id:
                    await app.bot.send_message(chat_id=chat_id, text=f"🔔 Через 20 минут: {task['name']} в {task_time.strftime('%H:%M')}")
                    task['reminded'] = True
                    save_tasks(tasks)
        await asyncio.sleep(60)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я помогу тебе управлять задачами. Просто напиши новую задачу!")

# Обработка текстов
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text

    if message_text.lower().startswith('выполнил:'):
        task_name = message_text[9:].strip()
        tasks = load_tasks()
        for task in tasks:
            if task_name.lower() in task['name'].lower():
                task['done'] = True
        save_tasks(tasks)
        await update.message.reply_text(f"✅ Задача '{task_name}' отмечена как выполненная!")

    elif message_text.lower().startswith('перенести:'):
        task_name = message_text[10:].strip()
        tasks = load_tasks()
        for task in tasks:
            if task_name.lower() in task['name'].lower():
                old_datetime = datetime.strptime(task['datetime'], "%Y-%m-%d %H:%M")
                new_datetime = old_datetime + timedelta(days=1)
                task['datetime'] = new_datetime.strftime("%Y-%m-%d %H:%M")
                task['done'] = False
                task['reminded'] = False
        save_tasks(tasks)
        await update.message.reply_text(f"🔄 Задача '{task_name}' перенесена на завтра!")

    else:
        task = parse_task(message_text)
        task['chat_id'] = update.message.chat_id
        tasks = load_tasks()
        tasks.append(task)
        save_tasks(tasks)
        await update.message.reply_text(f"📝 Задача добавлена: {task['name']} на {task['datetime']}")

# Запуск
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    scheduler = AsyncIOScheduler(timezone="Europe/Riga")
    scheduler.add_job(send_morning_plan, CronTrigger(hour=8, minute=0), kwargs={'context': app})
    scheduler.add_job(send_evening_check, CronTrigger(hour=17, minute=0), kwargs={'context': app})
    scheduler.start()

    asyncio.create_task(check_reminders(app))

    print("Бот запущен! ✅")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())