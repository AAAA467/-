import os
import random
import logging
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes
)

# Загрузка переменных из .env
load_dotenv()

# Логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

CHOOSING, SOLVING = range(2)
user_state = {}

menu_keyboard = ReplyKeyboardMarkup(
    [['Задача 1', 'Задача 2', 'Задача 3', 'Задача 4'], ['/skip', '/start']],
    resize_keyboard=True
)

# --- УТИЛИТЫ ---

def generate_random_u_format():
    """Генерация угломера в формате x-xx, 0-xx и т.д."""
    format_type = random.choice(['0-xx', 'x-xx', 'xx-xx'])
    if format_type == '0-xx':
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
    """Преобразует угломер в целое число"""
    return int(f"{left}{right:02d}") if left > 0 else right

def float_to_u_format(value: float) -> str:
    """Преобразует число в формат x-xx, 0-xx, xx-xx без округления"""
    int_value = int(value)
    s = str(int_value)
    if len(s) <= 2:
        return f"0-{s.zfill(2)}"
    elif len(s) == 3:
        return f"{s[0]}-{s[1:]}"
    else:
        return f"{s[:2]}-{s[2:]}"

def cut_digits(number, max_digits):
    """Обрезает число до целой части и ограниченного количества цифр"""
    return str(int(number))[:max_digits]

# --- ЗАДАЧИ ---

def generate_task1():
    Дальность = random.randint(1, 9999)
    Угломер_str, left, right = generate_random_u_format()
    Угломер_value = parse_u_value(left, right)
    Высота_prime = (Дальность * Угломер_value) / 1000
    Высота = Высота_prime * 1.05
    return {
        'text': f'Дальность = {Дальность}, Угломер = {Угломер_str}\nВопрос: Высота′ = ?, Высота = ?',
        'answer': f'{cut_digits(Высота_prime, 3)},{cut_digits(Высота, 3)}',
        'solution': (f'Угломер = {Угломер_value}\n'
                     f'{Дальность} * {Угломер_value} / 1000 = {Высота_prime:.6f} → Высота′={cut_digits(Высота_prime, 3)}\n'
                     f'{Высота_prime:.6f} * 1.05 = {Высота:.6f} → Высота={cut_digits(Высота, 3)}')
    }

def generate_task2():
    Угломер_prime_str, left, right = generate_random_u_format()
    Угломер_prime_value = parse_u_value(left, right)
    Высота = random.randint(10, 500)
    Дальность = Высота * 1000 / Угломер_prime_value
    Угломер_value = Угломер_prime_value * 0.95
    return {
        'text': f'Дальность = {int(Дальность)}, Высота = {Высота}\nВопрос: Угломер′ = ?, Угломер = ?',
        'answer': f'{Угломер_prime_str},{float_to_u_format(Угломер_value)}',
        'solution': (f'{Высота} * 1000 / {int(Дальность)} = {Угломер_prime_value:.9f} → Угломер′={Угломер_prime_str}\n'
                     f'{Угломер_prime_value:.9f} * 0.95 = {Угломер_value:.9f} → Угломер={float_to_u_format(Угломер_value)}')
    }

def generate_task3():
    Высота = random.randint(10, 500)
    Угломер_str, left, right = generate_random_u_format()
    Угломер_value = parse_u_value(left, right)
    Дальность_prime = (Высота * 1000) / Угломер_value
    Дальность = Дальность_prime * 0.95
    return {
        'text': f'Высота = {Высота}, Угломер = {Угломер_str}\nВопрос: Дальность′ = ?, Дальность = ?',
        'answer': f'{cut_digits(Дальность_prime, 4)},{cut_digits(Дальность, 4)}',
        'solution': (f'Угломер = {Угломер_value}\n'
                     f'{Высота} * 1000 / {Угломер_value} = {Дальность_prime:.6f} → Дальность′={cut_digits(Дальность_prime, 4)}\n'
                     f'{Дальность_prime:.6f} * 0.95 = {Дальность:.6f} → Дальность={cut_digits(Дальность, 4)}')
    }

def generate_task4():
    азимут_цели = random.randint(1, 359)
    азимут_ориентира = random.randint(1, 359)
    числовой_курс = азимут_цели - азимут_ориентира
    if числовой_курс < 0:
        числовой_курс += 360
    return {
        'text': f'Азимут цели = {азимут_цели}, Азимут ориентира = {азимут_ориентира}\nВопрос: Числовой курс цели = ?',
        'answer': str(числовой_курс),
        'solution': f'{азимут_цели} - {азимут_ориентира} = {числовой_курс}'
    }

# --- ХЕНДЛЕРЫ ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я бот для расчётных задач.\n\n"
        "Выбирай одну из задач ниже:\n"
        "📌 Пример ответа: 112,118 или 0–54,0–51 или 3010,2859 или 8\n"
        "📌 Команды:\n"
        "• /skip — показать ответ и решение\n"
        "• /start — начать заново",
        reply_markup=menu_keyboard
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
    else:
        await update.message.reply_text("Пожалуйста, выбери задачу.")
        return CHOOSING

    user_state[user_id] = task
    await update.message.reply_text(task['text'])
    return SOLVING

async def answer_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_answer = update.message.text.strip()
    if user_id not in user_state:
        await update.message.reply_text("Сначала выбери задачу: /start")
        return CHOOSING

    task = user_state[user_id]
    correct = task['answer']
    if user_answer == correct:
        await update.message.reply_text("✅ Правильно! /start — выбрать новую задачу", reply_markup=menu_keyboard)
    else:
        await update.message.reply_text(f"❌ Неверно!\nПравильный ответ: {correct}\n\nРешение:\n{task['solution']}", reply_markup=menu_keyboard)

    del user_state[user_id]
    return CHOOSING

async def skip_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_state:
        await update.message.reply_text("Сначала выбери задачу: /start")
        return CHOOSING
    task = user_state[user_id]
    await update.message.reply_text(f"Ответ: {task['answer']}\n\nРешение:\n{task['solution']}", reply_markup=menu_keyboard)
    del user_state[user_id]
    return CHOOSING

# --- MAIN ---

def main():
    token = os.getenv("TOKEN")
    if not token:
        print("❌ Ошибка: токен не найден в .env")
        return

    app = ApplicationBuilder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING: [
                MessageHandler(filters.Regex("^Задача [1-4]$"), choose_task),
                CommandHandler("skip", skip_handler),
            ],
            SOLVING: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, answer_handler),
                CommandHandler("skip", skip_handler),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
