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

def u_number_to_format(n):
    i = int(n)
    s = str(i)
    if len(s) <= 2:
        return f"0-{s.zfill(2)}"
    elif len(s) == 3:
        return f"{s[0]}-{s[1:]}"
    else:
        return f"{s[:2]}-{s[2:]}"

def cut_digits(number, max_digits):
    s = str(number)
    if '.' in s:
        s = s.split('.')[0]  # берём только целую часть без округления и точки
    return s[:max_digits]

def float_to_u_format(value: float) -> str:
    """Преобразует число в формат 'xx-xx', отсекая дробную часть без округления."""
    int_value = int(value)  # отбрасываем дробь
    s = str(int_value)
    if len(s) <= 2:
        # 0-xx
        return f"0-{s.zfill(2)}"
    elif len(s) == 3:
        # x-xx
        return f"{s[0]}-{s[1:]}"
    else:
        # xx-xx
        return f"{s[:2]}-{s[2:]}"

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
        'solution': (f'Угломер = {Угломер_value}\n'
                     f'{Дальность} * {Угломер_value} / 1000 = {Высота_raw:.6f} → Высота′={Высота_out}\n'
                     f'{Высота_raw:.6f} * 1.05 = {Высота:.6f} → Высота={Высота_final_out}')
    }

def generate_task2():
    # Генерируем Угломер′ в формате
    Угломер_prime_str, left, right = generate_random_u_format()
    Угломер_prime_value = parse_u_value(left, right)

    Высота = random.randint(10, 500)  # строго 10..500

    # Рассчитываем Дальность под формулу
    Дальность = Высота * 1000 / Угломер_prime_value

    # Угломер с коэффициентом 0.95, без округления
    Угломер_value = Угломер_prime_value * 0.95

    # Форматируем угломеры без округления
    Угломер_prime_str_correct = Угломер_prime_str
    Угломер_str = float_to_u_format(Угломер_value)

    return {
        'text': f'Дальность = {int(Дальность)}, Высота = {Высота}\nВопрос: Угломер′ = ?, Угломер = ?',
        'answer': f'{Угломер_prime_str_correct},{Угломер_str}',
        'solution': (f'{Высота} * 1000 / {int(Дальность)} = {Угломер_prime_value:.9f} → Угломер′={Угломер_prime_str_correct}\n'
                     f'{Угломер_prime_value:.9f} * 0.95 = {Угломер_value:.9f} → Угломер={Угломер_str}')
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
        'solution': (f'Угломер = {Угломер_value}\n'
                     f'{Высота} * 1000 / {Угломер_value} = {Дальность_prime:.6f} → Дальность′={Дальность_prime_out}\n'
                     f'{Дальность_prime:.6f} * 0.95 = {Дальность:.6f} → Дальность={Дальность_out}')
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
        'solution': f'Числовой курс цели = {азимут_цели} - {азимут_ориентира} = {числовой_курс}'
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
        "• Высота в задачах от 10 до 500\n"
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
        await update.message.reply_text("Пожалуйста, выберите задачу из меню.")
        return CHOOSING

    user_state[user_id] = task
    await update.message.reply_text(task['text'])
    return SOLVING

async def answer_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_answer = update.message.text.strip()

    if user_id not in user_state:
        await update.message.reply_text("Сначала выберите задачу командой /start")
        return CHOOSING

    task = user_state[user_id]
    correct_answer = task['answer']

    if user_answer == correct_answer:
        await update.message.reply_text("✅ Правильно! Поздравляю.\nДля выбора другой задачи нажми /start", reply_markup=menu_keyboard)
    else:
        await update.message.reply_text(f"❌ Неверно.\nПравильный ответ:\n{correct_answer}\n\nРешение:\n{task['solution']}", reply_markup=menu_keyboard)

    del user_state[user_id]
    return CHOOSING

async def skip_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_state:
        await update.message.reply_text("Сначала выберите задачу командой /start")
        return CHOOSING
    task = user_state[user_id]
    await update.message.reply_text(f"Ответ: {task['answer']}\n\nРешение:\n{task['solution']}", reply_markup=menu_keyboard)
    del user_state[user_id]
    return CHOOSING

def main():
    token = os.getenv("TOKEN")
    if not token:
        print("Ошибка: токен бота не установлен в переменной окружения TOKEN")
        return

    application = ApplicationBuilder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [
                MessageHandler(filters.Regex('^(Задача 1|Задача 2|Задача 3|Задача 4)$'), choose_task),
                CommandHandler('skip', skip_handler),
            ],
            SOLVING: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, answer_handler),
                CommandHandler('skip', skip_handler),
            ],
        },
        fallbacks=[CommandHandler('start', start)],
    )

    application.add_handler(conv_handler)

    # keep_alive()  # Если используешь keep_alive для хостинга - раскомментируй

    application.run_polling()

if __name__ == '__main__':
    main()
