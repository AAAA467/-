import os
import random
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes
)
from dotenv import load_dotenv

# Загрузка токена из .env
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# Логирование
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

CHOOSING, SOLVING = range(2)
user_state = {}

menu_keyboard = ReplyKeyboardMarkup(
    [['Задача 1', 'Задача 2', 'Задача 3', 'Задача 4'], ['/skip', '/start']],
    resize_keyboard=True
)

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

def generate_random_u_format():
    format_type = random.choice(['0-x', '0-xx', 'x-xx', 'xx-xx'])
    if format_type == '0-x':
        left = 0
        right = random.randint(1, 9)
    elif format_type == '0-xx':
        left = 0
        right = random.randint(10, 99)
    elif format_type == 'x-xx':
        left = random.randint(1, 9)
        right = random.randint(10, 99)
    else:
        left = random.randint(10, 99)
        right = random.randint(10, 99)
    return f"{left}-{right}", left, right

def parse_u_value(left, right):
    if left == 0:
        return right
    return int(f"{left}{right:02d}")

def float_to_u_format(value: float) -> str:
    int_value = int(round(value))
    s = str(int_value)
    if len(s) <= 2:
        return f"0-{s.zfill(2)}"
    elif len(s) == 3:
        return f"{s[0]}-{s[1:]}"
    else:
        return f"{s[:2]}-{s[2:]}"

def cut_digits(number, max_digits):
    return str(int(number))[:max_digits]

# --- ЗАДАЧИ ---

def generate_task1():
    Дальность = random.randint(1, 9999)
    Угломер_str, left, right = generate_random_u_format()
    Угломер_value = parse_u_value(left, right)
    Высота_raw = (Дальность * Угломер_value) / 1000
    Высота = Высота_raw * 1.05
    Высота_out = cut_digits(Высота_raw, 3)
    Высота_final_out = cut_digits(Высота, 3)
    return {
        'text': f'Дальность = {Дальность}, Угломер = {Угломер_str}\nВопрос: Высота′ = ?, Высота = ?',
        'answer': f'{Высота_out},{Высота_final_out}',
        'solution': (
            f'{Дальность} * {Угломер_value} / 1000 = {Высота_raw:.6f} → Высота′={Высота_out}\n'
            f'{Высота_raw:.6f} * 1.05 = {Высота:.6f} → Высота={Высота_final_out}'
        )
    }

def generate_task2():
    Высота = random.randint(10, 500)
    while True:
        Угломер_prime_value = (Высота * 1000) / random.randint(1, 9999)
        if 10 <= Угломер_prime_value <= 9999:
            break
    Угломер_value = round(Угломер_prime_value * 0.95)
    Угломер_prime_str = float_to_u_format(Угломер_prime_value)
    Угломер_str = float_to_u_format(Угломер_value)
    return {
        'text': f'Высота = {Высота}, Угломер′ = ?\nВопрос: Угломер′ = ?, Угломер = ?',
        'answer': f'{Угломер_prime_str},{Угломер_str}',
        'solution': (
            f'{Высота} * 1000 / ? = {Угломер_prime_value:.15f} → Угломер′={Угломер_prime_str}\n'
            f'{Угломер_prime_value:.15f} * 0.95 = {Угломер_value} → Угломер={Угломер_str}'
        )
    }

def generate_task3():
    Высота = random.randint(10, 500)
    Угломер_str, left, right = generate_random_u_format()
    Угломер_value = parse_u_value(left, right)
    Дальность_prime = (Высота * 1000) / Угломер_value
    Дальность = Дальность_prime * 0.95
    Дальность_prime_out = cut_digits(Дальность_prime, 4)
    Дальность_out = cut_digits(Дальность, 4)
    return {
        'text': f'Высота = {Высота}, Угломер = {Угломер_str}\nВопрос: Дальность′ = ?, Дальность = ?',
        'answer': f'{Дальность_prime_out},{Дальность_out}',
        'solution': (
            f'{Высота} * 1000 / {Угломер_value} = {Дальность_prime:.6f} → Дальность′={Дальность_prime_out}\n'
            f'{Дальность_prime:.6f} * 0.95 = {Дальность:.6f} → Дальность={Дальность_out}'
        )
    }

def generate_task4():
    азимут_цели = random.randint(1, 359)
    азимут_ориентира = random.randint(1, 359)
    числовой_курс = (азимут_цели - азимут_ориентира + 360) % 360
    return {
        'text': f'Азимут цели = {азимут_цели}, Азимут ориентира = {азимут_ориентира}\nВопрос: Числовой курс цели = ?',
        'answer': str(числовой_курс),
        'solution': f'({азимут_цели} - {азимут_ориентира} + 360) % 360 = {числовой_курс}'
    }

# --- ХЕНДЛЕРЫ ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Выбери задачу ниже:", reply_markup=menu_keyboard
    )
    return CHOOSING

async def choose_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    task_text = update.message.text
    task = None
    if task_text == 'Задача 1':
        task = generate_task1()
    elif task_text == 'Задача 2':
        task = generate_task2()
    elif task_text == 'Задача 3':
        task = generate_task3()
    elif task_text == 'Задача 4':
        task = generate_task4()

    if task:
        user_state[user_id] = task
        await update.message.reply_text(task['text'])
        return SOLVING
    else:
        await update.message.reply_text("Выберите задачу из меню.")
        return CHOOSING

async def answer_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_state:
        await update.message.reply_text("Сначала выберите задачу с /start")
        return CHOOSING

    task = user_state[user_id]
    user_answer = update.message.text.strip()
    correct_answer = task['answer']
    if user_answer == correct_answer:
        await update.message.reply_text("✅ Правильно! /start — новая задача", reply_markup=menu_keyboard)
    else:
        await update.message.reply_text(f"❌ Неверно. Ответ: {correct_answer}\n\nРешение:\n{task['solution']}", reply_markup=menu_keyboard)
    del user_state[user_id]
    return CHOOSING

async def skip_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_state:
        task = user_state[user_id]
        await update.message.reply_text(f"Ответ: {task['answer']}\n\nРешение:\n{task['solution']}", reply_markup=menu_keyboard)
        del user_state[user_id]
    else:
        await update.message.reply_text("Нет активной задачи. Используйте /start.")
    return CHOOSING

# --- ЗАПУСК БОТА ---

def main():
    if not TOKEN:
        print("❌ BOT_TOKEN не найден в переменных окружения.")
        return

    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING: [
                MessageHandler(filters.Regex("^Задача [1-4]$"), choose_task),
                CommandHandler("skip", skip_handler)
            ],
            SOLVING: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, answer_handler),
                CommandHandler("skip", skip_handler)
            ]
        },
        fallbacks=[CommandHandler("start", start)]
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
