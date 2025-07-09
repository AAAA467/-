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

# --- ФУНКЦИИ ОБРАБОТКИ ЗАДАЧ ---

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
    # Возвращаем float без округления
    if left == 0:
        return float(right)
    return float(f"{left}{right:02d}")

def u_number_to_format(n):
    # n - float или int
    # Преобразуем в строку целой части без округления
    int_str = str(int(n))
    if len(int_str) <= 2:
        return f"0-{int_str}"
    elif len(int_str) == 3:
        return f"{int_str[0]}-{int_str[1:]}"
    else:
        return f"{int_str[:2]}-{int_str[2:]}"

def cut_digits(number, max_digits):
    # Возвращает строку с не более max_digits цифр (без округления)
    s = str(number).replace('.', '').replace(',', '')
    return s[:max_digits]

def generate_task1():
    D = random.randint(1, 9999)
    U_str, left, right = generate_random_u_format()
    U_value = parse_u_value(left, right)
    V_prime_raw = (D * U_value) / 1000
    V = V_prime_raw * 1.05
    V_prime_out = cut_digits(V_prime_raw, 3)
    V_out = cut_digits(V, 3)
    return {
        'text': f'Дальность = {D}, Угломер = {U_str}\nВопрос: Высота′ = ?, Высота = ?',
        'answer': f'{V_prime_out},{V_out}',
        'solution': f'Угломер = {U_value}\n{D} * {U_value} / 1000 = {V_prime_raw:.9f} → Высота′={V_prime_out}\n'
                    f'{V_prime_raw:.9f} * 1.05 = {V:.9f} → Высота={V_out}'
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

    U_prime_str = f"{left}-{right}"
    U_prime_value = parse_u_value(left, right)

    # D от 1 до 9999
    D = random.randint(1, 9999)

    # Высота в диапазоне от 10 до 500 (исправлено)
    V = (U_prime_value * D) / 1000
    if V < 10:
        V = 10
    elif V > 500:
        V = 500

    # Высота теперь float, не int
    # Вычисляем Угломер′ и Угломер без округления
    U_prime_value_exact = V * 1000 / D  # точное значение Угломера'
    U_value_exact = U_prime_value_exact * 0.95  # точное значение Угломера

    U_prime_str = u_number_to_format(U_prime_value_exact)
    U_str = u_number_to_format(U_value_exact)

    return {
        'text': f'Дальность = {D}, Высота = {V:.6f}\nВопрос: Угломер′ = ?, Угломер = ?',
        'answer': f'{U_prime_str},{U_str}',
        'solution': f'{V:.6f} * 1000 / {D} = {U_prime_value_exact:.9f} → Угломер′={U_prime_str}\n'
                    f'{U_prime_value_exact:.9f} * 0.95 = {U_value_exact:.9f} → Угломер={U_str}'
    }

def generate_task3():
    V = random.uniform(10, 500)  # Высота от 10 до 500, float для точности
    U_str, left, right = generate_random_u_format()
    U_value = parse_u_value(left, right)
    D_prime = (V * 1000) / U_value
    D = D_prime * 0.95
    D_prime_out = cut_digits(D_prime, 4)
    D_out = cut_digits(D, 4)
    return {
        'text': f'Высота = {V:.6f}, Угломер = {U_str}\nВопрос: Дальность′ = ?, Дальность = ?',
        'answer': f'{D_prime_out},{D_out}',
        'solution': f'Угломер = {U_value}\n{V:.6f} * 1000 / {U_value} = {D_prime:.9f} → Дальность′={D_prime_out}\n'
                    f'{D_prime:.9f} * 0.95 = {D:.9f} → Дальность={D_out}'
    }

def generate_task4():
    azimuth_target = random.randint(1, 359)
    azimuth_reference = random.randint(1, 359)
    numeric_course = azimuth_target - azimuth_reference
    if numeric_course < 0:
        numeric_course += 360
    return {
        'text': f'Азимут цели = {azimuth_target}, Азимут ориентира = {azimuth_reference}\nВопрос: Числовой курс цели = ?',
        'answer': f'{numeric_course}',
        'solution': f'{azimuth_target} - {azimuth_reference} = {numeric_course}'
    }

# --- ХЕНДЛЕРЫ ТЕЛЕГРАМ ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я бот для расчётных задач.\n\n"
        "Выбирай одну из задач ниже:\n"
        "📌 Формат ответа: Высота′,Высота или Угломер′,Угломер или Дальность′,Дальность или Числовой курс (для задачи 4)\n"
        "📌 Пример: 112,118 или 0–54,0–51 или 3010,2859 или 8\n"
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
    if task:
        await update.message.reply_text(f"✅ Правильный ответ: {task['answer']}\n\n📘 Решение:\n{task['solution']}")
    else:
        await update.message.reply_text("⚠️ Нет активной задачи. Введите /start.")
    await update.message.reply_text("🔁 Хотите новую задачу? Выберите ниже:", reply_markup=menu_keyboard)
    return CHOOSING

def main():
    TOKEN = os.getenv('TOKEN')
    application = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_task)],
            SOLVING: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer),
                CommandHandler('skip', skip)
            ],
        },
        fallbacks=[CommandHandler('start', start)]
    )
    application.add_handler(conv_handler)

    application.run_polling()

if __name__ == '__main__':
    main()
