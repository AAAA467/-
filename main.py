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

# Импортируем keep_alive
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

# --- Вспомогательные функции ---

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
    s = str(number)
    if '.' in s:
        s = s.split('.')[0]  # берём только целую часть без округления и точки
    return s[:max_digits]

# --- Генерация задач ---

def generate_task1():
    Дальность = random.randint(1, 9999)
    Угломер_str, left, right = generate_random_u_format()
    Угломер_value = parse_u_value(left, right)
    Высота_prime_raw = (Дальность * Угломер_value) / 1000
    Высота = Высота_prime_raw * 1.05
    Высота_prime_out = cut_digits(Высота_prime_raw, 3)
    Высота_out = cut_digits(Высота, 3)
    return {
        'text': f'Дальность = {Дальность}, Угломер = {Угломер_str}\nВопрос: Высота′ = ?, Высота = ?',
        'answer': f'{Высота_prime_out},{Высота_out}',
        'solution': f'Угломер = {Угломер_value}\n{Дальность} * {Угломер_value} / 1000 = {Высота_prime_raw:.6f} → Высота′={Высота_prime_out}\n'
                    f'{Высота_prime_raw:.6f} * 1.05 = {Высота:.6f} → Высота={Высота_out}'
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

    Угломер_prime_str = f"{left}-{right}"
    Угломер_prime_value = parse_u_value(left, right)
    Угломер_value = Угломер_prime_value * 0.95  # оставляем float без округления
    Угломер_str = u_number_to_format(int(Угломер_value))

    Дальность = random.randint(1, 9999)
    Высота = random.randint(10, 500)  # Высота в диапазоне 10..500

    # Восстановим Высота для корректного соотношения с Угломер_prime_value и Дальность
    # Пересчитаем Высота исходя из формулы, чтобы высчитать Угломер_prime_value корректно:
    Высота = Угломер_prime_value * Дальность / 1000

    return {
        'text': f'Дальность = {Дальность}, Высота = {int(Высота)}\nВопрос: Угломер′ = ?, Угломер = ?',
        'answer': f'{Угломер_prime_str},{Угломер_str}',
        'solution': f'{int(Высота)} * 1000 / {Дальность} = {Угломер_prime_value:.6f} → Угломер′={Угломер_prime_str}\n'
                    f'{Угломер_prime_value:.6f} * 0.95 = {Угломер_value:.6f} → Угломер={Угломер_str}'
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
        'solution': f'Угломер = {Угломер_value}\n{Высота} * 1000 / {Угломер_value} = {Дальность_prime:.6f} → Дальность′={Дальность_prime_out}\n'
                    f'{Дальность_prime:.6f} * 0.95 = {Дальность:.6f} → Дальность={Дальность_out}'
    }

def generate_task4():
    азимут_цели = random.randint(1, 359)
    азимут_ориентира = random.randint(1, 359)
    числовой_курс = азимут_цели - азимут_ориентира
    if числовой_курс < 0:
        числовой_курс += 360
    return {
        'text': f'Азимут цели = {азимут_цели}, Азимут ориентира = {азимут_ориентира}\nВопрос: Числовой курс цели = ?',
        'answer': f'{числовой_курс}',
        'solution': f'{азимут_цели} - {азимут_ориентира} = {числовой_курс}'
    }

# --- ХЕНДЛЕРЫ ТЕЛЕГРАМ ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я бот для расчётных задач.\n\n"
        "Выбирай одну из задач ниже:\n"
        "📌 Формат ответа: Высота′,Высота или Угломер′,Угломер или Дальность′,Дальность или Числовой курс цели\n"
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
        await update.message.reply_text("⚠️ Нет активной задачи. Введите /start")
        return CHOOSING

    answer = update.message.text.strip()

    if answer == '/skip':
        await update.message.reply_text(
            f"✅ Правильный ответ: {task['answer']}\n\n📖 Решение:\n{task['solution']}",
            reply_markup=menu_keyboard
        )
        return CHOOSING

    if answer == task['answer']:
        await update.message.reply_text(
            "🎉 Верно! Можете выбрать другую задачу или /start для начала.",
            reply_markup=menu_keyboard
        )
        return CHOOSING
    else:
        await update.message.reply_text(
            "❌ Неверно. Попробуйте ещё раз или /skip для подсказки.",
            reply_markup=menu_keyboard
        )
        return SOLVING

async def skip_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    task = user_state.get(user_id)
    if task:
        await update.message.reply_text(
            f"✅ Правильный ответ: {task['answer']}\n\n📖 Решение:\n{task['solution']}",
            reply_markup=menu_keyboard
        )
    else:
        await update.message.reply_text("⚠️ Нет активной задачи.")
    return CHOOSING

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚪 Выход. До встречи!")
    return ConversationHandler.END

def main():
    token = os.environ.get("BOT_TOKEN")
    if not token:
        print("Ошибка: переменная окружения BOT_TOKEN не установлена")
        return

    application = ApplicationBuilder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_task)],
            SOLVING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer)]
        },
        fallbacks=[CommandHandler('skip', skip_task), CommandHandler('cancel', cancel)]
    )

    application.add_handler(conv_handler)

    print("Бот запущен...")
    application.run_polling()

if __name__ == '__main__':
    keep_alive()
    main()
