import logging
import random
import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

from keep_alive import keep_alive

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
    return float(f"{left}{right:02d}")

def u_number_to_format(n):
    i = int(n)
    s = str(i)
    if len(s) <= 2:
        return f"0-{s}"
    elif len(s) == 3:
        return f"{s[0]}-{s[1:]}"
    else:
        return f"{s[:2]}-{s[2:]}"

def cut_digits(number, max_digits):
    return str(number)[:max_digits]

def generate_task1():
    distance = random.randint(1, 9999)
    u_str, left, right = generate_random_u_format()
    u_value = parse_u_value(left, right)
    v_prime_raw = (distance * u_value) / 1000
    v = v_prime_raw * 1.05
    v_prime_out = cut_digits(v_prime_raw, 3)
    v_out = cut_digits(v, 3)
    return {
        'text': f'Дальность = {distance}, Угломер = {u_str}\nВопрос: Высота′ = ?, Высота = ?',
        'answer': f'{v_prime_out},{v_out}',
        'solution': f'Угломер = {u_value}\n{distance} * {u_value} / 1000 = {v_prime_raw:.6f} → Высота′={v_prime_out}\n'
                    f'{v_prime_raw:.6f} * 1.05 = {v:.6f} → Высота={v_out}'
    }

def generate_task2():
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

    u_prime_str = f"{left}-{right}"
    u_prime_value = float(f"{left}{right:02d}")
    u_value = u_prime_value * 0.95
    u_str = u_number_to_format(u_value)

    distance = random.randint(1, 9999)
    v = u_prime_value * distance / 1000
    if v < 10 or v > 500:
        return generate_task2()

    return {
        'text': f'Дальность = {distance}, Высота = {int(v)}\nВопрос: Угломер′ = ?, Угломер = ?',
        'answer': f'{u_prime_str},{u_str}',
        'solution': f'{v:.6f} * 1000 / {distance} = {u_prime_value:.15f} → Угломер′={u_prime_str}\n'
                    f'{u_prime_value:.15f} * 0.95 = {u_value:.15f} → Угломер={u_str}'
    }

def generate_task3():
    v = random.randint(10, 500)
    u_str, left, right = generate_random_u_format()
    u_value = parse_u_value(left, right)
    distance_prime = (v * 1000) / u_value
    distance = distance_prime * 0.95
    distance_prime_out = cut_digits(distance_prime, 4)
    distance_out = cut_digits(distance, 4)
    return {
        'text': f'Высота = {v}, Угломер = {u_str}\nВопрос: Дальность′ = ?, Дальность = ?',
        'answer': f'{distance_prime_out},{distance_out}',
        'solution': f'Угломер = {u_value}\n{v} * 1000 / {u_value} = {distance_prime:.6f} → Дальность′={distance_prime_out}\n'
                    f'{distance_prime:.6f} * 0.95 = {distance:.6f} → Дальность={distance_out}'
    }

def generate_task4():
    az_target = random.randint(1, 359)
    az_reference = random.randint(1, 359)
    raw_course = az_target - az_reference
    if raw_course < 0:
        raw_course += 360
    return {
        'text': f'Азимут цели = {az_target}, Азимут ориентира = {az_reference}\nВопрос: Числовой курс цели = ?',
        'answer': f'{raw_course}',
        'solution': f'{az_target} - {az_reference} = {az_target - az_reference} → Числовой курс цели = {raw_course}'
    }

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я бот для расчётных задач.\n\n"
        "Выбирай одну из задач ниже:\n"
        "📌 Формат ответа: Высота′,Высота или Угломер′,Угломер или Дальность′,Дальность или Числовой курс цели\n"
        "📌 Пример: 112,118 или 0–54,0–51 или 3010,2859\n"
        "📌 Ограничения:\n"
        "• Высота и Высота′ — максимум 3 цифры\n"
        "• Дальность и Дальность′ — максимум 4 цифры\n"
        "🛠 Команды:\n"
        "• /skip — показать ответ и решение\n"
        "• /start — начать заново\n",
        reply_markup=menu_keyboard
    )
    return CHOOSING

async def choose_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    task_text = update.message.text

    if task_text == 'Задача 1':
        task = generate_task1()
    elif task_text == 'Задача 2':
        task = generate_task2()
    elif task_text == 'Задача 3':
        task = generate_task3()
    elif task_text == 'Задача 4':
        task = generate_task4()
    else:
        return CHOOSING

    user_state[user_id] = task
    await update.message.reply_text(
        f"📘 Условие:\n{task['text']}\n\n✍️ Введите ответ или /skip",
        reply_markup=menu_keyboard
    )
    return SOLVING

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    task = user_state.get(user_id)

    if not task:
        await update.message.reply_text("⚠️ Нет активной задачи. Введите /start.")
        return CHOOSING

    user_input = update.message.text.replace(" ", "").lower()
    correct = task['answer'].replace(" ", "").lower()

    if user_input == correct:
        await update.message.reply_text("✅ Верно!")
    else:
        await update.message.reply_text(
            f"❌ Неверно.\n✅ Правильный ответ: {task['answer']}\n\n📘 Решение:\n{task['solution']}"
        )

    await update.message.reply_text("🔁 Хотите новую задачу? Выберите ниже:", reply_markup=menu_keyboard)
    return CHOOSING

async def skip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    task = user_state.get(user_id)

    if not task:
        await update.message.reply_text("⚠️ Нет активной задачи. Введите /start.")
        return CHOOSING

    await update.message.reply_text(
        f"✅ Ответ: {task['answer']}\n\n📘 Решение:\n{task['solution']}"
    )
    await update.message.reply_text("🔁 Хотите новую задачу? Выберите ниже:", reply_markup=menu_keyboard)
    return CHOOSING

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.error("❌ Ошибка при обработке обновления:", exc_info=context.error)

def main():
    TOKEN = os.environ.get("BOT_TOKEN")
    if not TOKEN:
        print("❌ Установите переменную окружения BOT_TOKEN в настройках!")
        return

    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING: [
                MessageHandler(filters.Regex("^(Задача 1|Задача 2|Задача 3|Задача 4)$"), choose_task),
            ],
            SOLVING: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer),
                CommandHandler("skip", skip),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(conv_handler)
    app.add_error_handler(error_handler)

    print("✅ Бот запущен...")

    keep_alive()
    app.run_polling()

if __name__ == "__main__":
    main()
