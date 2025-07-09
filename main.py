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
    return int(f"{left}{right:02d}")

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
    return str(int(number))[:max_digits]

def generate_task1():
    while True:
        D = random.randint(1, 9999)
        U_str, left, right = generate_random_u_format()
        U_value = parse_u_value(left, right)
        V_prime_raw = (D * U_value) / 1000
        V = V_prime_raw * 1.05
        if 10 <= V_prime_raw <= 500 and 10 <= V <= 500:
            break
    V_prime_out = cut_digits(V_prime_raw, 3)
    V_out = cut_digits(V, 3)
    return {
        'text': f'Д = {D}, У = {U_str}\nВопрос: В′ = ?, В = ?',
        'answer': f'{V_prime_out},{V_out}',
        'solution': f'У = {U_value}\n{D} * {U_value} / 1000 = {V_prime_raw:.6f} → В′={V_prime_out}\n'
                    f'{V_prime_raw:.6f} * 1.05 = {V:.6f} → В={V_out}'
    }

def generate_task2():
    while True:
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

        U_prime_str = f"{left}-{right}"
        U_prime_value = parse_u_value(left, right)
        U_value = U_prime_value * 0.95
        U_str = u_number_to_format(U_value)

        D = random.randint(1, 9999)
        V = (U_prime_value * D) / 1000

        if 10 <= V <= 500:
            break

    return {
        'text': f'Д = {D}, В = {int(V)}\nВопрос: У′ = ?, У = ?',
        'answer': f'{U_prime_str},{U_str}',
        'solution': f'{int(V)} * 1000 / {D} = {U_prime_value:.12f} → У′={U_prime_str}\n'
                    f'{U_prime_value:.12f} * 0.95 = {U_value:.12f} → У={U_str}'
    }

def generate_task3():
    while True:
        V = random.randint(10, 500)
        U_str, left, right = generate_random_u_format()
        U_value = parse_u_value(left, right)
        D_prime = (V * 1000) / U_value
        D = D_prime * 0.95
        if 10 <= D_prime <= 9999 and 10 <= D <= 9999:
            break
    D_prime_out = cut_digits(D_prime, 4)
    D_out = cut_digits(D, 4)
    return {
        'text': f'В = {V}, У = {U_str}\nВопрос: Д′ = ?, Д = ?',
        'answer': f'{D_prime_out},{D_out}',
        'solution': f'У = {U_value}\n{V} * 1000 / {U_value} = {D_prime:.6f} → Д′={D_prime_out}\n'
                    f'{D_prime:.6f} * 0.95 = {D:.6f} → Д={D_out}'
    }

def generate_task4():
    azimuth_target = random.randint(1, 359)
    azimuth_reference = random.randint(1, 359)
    raw_course = azimuth_target - azimuth_reference
    if raw_course < 0:
        raw_course += 360
    return {
        'text': f'Азимут цели = {azimuth_target}, Азимут ориентира = {azimuth_reference}\nВопрос: Числовой курс цели = ?',
        'answer': f'{raw_course}',
        'solution': f'{azimuth_target} - {azimuth_reference} = {azimuth_target - azimuth_reference} → '
                    f'Числовой курс цели = {raw_course}'
    }

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я бот для расчётных задач.\n\n"
        "Выбирай одну из задач ниже:\n"
        "📌 Формат ответа: В′,В или У′,У или Д′,Д или Число\n"
        "📌 Пример: 112,118 или 0–54,0–51 или 3010,2859 или 8\n"
        "📌 Ограничения:\n"
        "• В и В′ — от 10 до 500\n"
        "• Д и Д′ — максимум 4 цифры\n"
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
        print("❌ Установите переменную окружения BOT_TOKEN!")
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
