import os
import random
import logging
from threading import Thread

# ── Telegram ────────────────────────────────────────────────────────────────────
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

# ── Flask ───────────────────────────────────────────────────────────────────────
from flask import Flask

# ── Логирование ────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# ── Состояния для ConversationHandler ──────────────────────────────────────────
CHOOSING, SOLVING = range(2)
user_state: dict[int, dict] = {}

# ── Клавиатура ─────────────────────────────────────────────────────────────────
menu_keyboard = ReplyKeyboardMarkup(
    [["Задача 1", "Задача 2", "Задача 3", "Задача 4"], ["/skip", "/start"]],
    resize_keyboard=True,
)

# ── Вспомогательные функции ────────────────────────────────────────────────────
def generate_random_u_format():
    format_type = random.choice(["0-x", "0-xx", "x-xx", "xx-xx"])
    if format_type == "0-x":
        left, right = 0, random.randint(1, 9)
    elif format_type == "0-xx":
        left, right = 0, random.randint(10, 99)
    elif format_type == "x-xx":
        left, right = random.randint(1, 9), random.randint(10, 99)
    else:
        left, right = random.randint(10, 99), random.randint(10, 99)
    return f"{left}-{right}", left, right


def parse_u_value(left: int, right: int) -> int:
    return right if left == 0 else int(f"{left}{right:02d}")


def cut_digits(number: float, max_digits: int) -> str:
    return str(int(number))[:max_digits]


def float_to_u_format(value: float) -> str:
    s = str(int(value))
    if len(s) <= 2:
        return f"0-{s.zfill(2)}"
    if len(s) == 3:
        return f"{s[0]}-{s[1:]}"
    return f"{s[:2]}-{s[2:]}"


# ── Генерация задач ────────────────────────────────────────────────────────────
def generate_task1():
    Дальность = random.randint(1, 9999)
    Угломер_str, left, right = generate_random_u_format()
    Угломер_value = parse_u_value(left, right)
    Высота_prime = (Дальность * Угломер_value) / 1000
    Высота = Высота_prime * 1.05
    return {
        "text": f"Дальность = {Дальность}, Угломер = {Угломер_str}\n"
                f"Вопрос: Высота′ = ?, Высота = ?",
        "answer": f"{cut_digits(Высота_prime, 3)},{cut_digits(Высота, 3)}",
        "solution": (
            f"Угломер = {Угломер_value}\n"
            f"{Дальность} * {Угломер_value} / 1000 = {Высота_prime}"
            f" → Высота′={cut_digits(Высота_prime, 3)}\n"
            f"{Высота_prime} * 1.05 = {Высота}"
            f" → Высота={cut_digits(Высота, 3)}"
        ),
    }


def generate_task2():
    Высота = random.randint(10, 500)
    Дальность = random.randint(10, 500)
    Угломер_prime_value = Высота * 1000 / Дальность
    Угломер_value = Угломер_prime_value * 0.95
    return {
        "text": f"Дальность = {Дальность}, Высота = {Высота}\n"
                f"Вопрос: Угломер′ = ?, Угломер = ?",
        "answer": f"{float_to_u_format(Угломер_prime_value)},"
                  f"{float_to_u_format(Угломер_value)}",
        "solution": (
            f"{Высота} * 1000 / {Дальность} = {Угломер_prime_value}"
            f" → Угломер′={float_to_u_format(Угломер_prime_value)}\n"
            f"{Угломер_prime_value} * 0.95 = {Угломер_value}"
            f" → Угломер={float_to_u_format(Угломер_value)}"
        ),
    }


def generate_task3():
    Высота = random.randint(10, 500)
    Угломер_str, left, right = generate_random_u_format()
    Угломер_value = parse_u_value(left, right)
    Дальность_prime = (Высота * 1000) / Угломер_value
    Дальность = Дальность_prime * 0.95
    return {
        "text": f"Высота = {Высота}, Угломер = {Угломер_str}\n"
                f"Вопрос: Дальность′ = ?, Дальность = ?",
        "answer": f"{cut_digits(Дальность_prime, 4)},{cut_digits(Дальность, 4)}",
        "solution": (
            f"Угломер = {Угломер_value}\n"
            f"{Высота} * 1000 / {Угломер_value} = {Дальность_prime}"
            f" → Дальность′={cut_digits(Дальность_prime, 4)}\n"
            f"{Дальность_prime} * 0.95 = {Дальность}"
            f" → Дальность={cut_digits(Дальность, 4)}"
        ),
    }


def generate_task4():
    азимут_цели = random.randint(1, 359)
    азимут_ориентира = random.randint(1, 359)
    числовой_курс = (азимут_цели - азимут_ориентира) % 360
    return {
        "text": f"Азимут цели = {азимут_цели}, "
                f"Азимут ориентира = {азимут_ориентира}\n"
                f"Вопрос: Числовой курс цели = ?",
        "answer": str(числовой_курс),
        "solution": (
            f"Числовой курс цели = {азимут_цели} - {азимут_ориентира}"
            f" = {числовой_курс}"
        ),
    }


# ── Хендлеры Telegram ──────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я бот для расчётных задач.\n\n"
        "Выбирай одну из задач ниже:\n"
        "📌 Формат ответа: Высота′,Высота или Угломер′,Угломер или "
        "Дальность′,Дальность или Числовой курс (для задачи 4)\n"
        "📌 Пример: 112,118 или 0–54,0–51 или 3010,2859 или 8\n"
        "🛠 Команды:\n"
        "• /skip — показать ответ и решение\n"
        "• /start — начать заново\n",
        reply_markup=menu_keyboard,
    )
    return CHOOSING


async def choose_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    tasks = {
        "Задача 1": generate_task1,
        "Задача 2": generate_task2,
        "Задача 3": generate_task3,
        "Задача 4": generate_task4,
    }
    if text not in tasks:
        await update.message.reply_text("Пожалуйста, выберите задачу из меню.")
        return CHOOSING

    task = tasks[text]()
    user_state[user_id] = task
    await update.message.reply_text(task["text"])
    return SOLVING


async def answer_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    answer = update.message.text.strip()

    if user_id not in user_state:
        await update.message.reply_text("Сначала выберите задачу командой /start")
        return CHOOSING

    task = user_state[user_id]
    correct = task["answer"]

    if answer == correct:
        await update.message.reply_text(
            "✅ Правильно! Молодец!\n/start для новой задачи", reply_markup=menu_keyboard
        )
    else:
        await update.message.reply_text(
            f"❌ Неверно.\nПравильный ответ:\n{correct}\n\nРешение:\n{task['solution']}",
            reply_markup=menu_keyboard,
        )

    del user_state[user_id]
    return CHOOSING


async def skip_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_state:
        await update.message.reply_text("Сначала выберите задачу /start")
        return CHOOSING

    task = user_state[user_id]
    await update.message.reply_text(
        f"Ответ: {task['answer']}\n\nРешение:\n{task['solution']}",
        reply_markup=menu_keyboard,
    )
    del user_state[user_id]
    return CHOOSING


# ── Flask keep‑alive сервер ────────────────────────────────────────────────────
def run_flask():
    app = Flask(__name__)

    @app.route("/")
    def home():
        return "I'm alive", 200

    @app.route("/health")
    def health():
        return "OK", 200

    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)


# ── Точка входа ────────────────────────────────────────────────────────────────
def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        logging.error("❌ BOT_TOKEN не найден!")
        return

    # Запускаем Flask в отдельном потоке
    Thread(target=run_flask, daemon=True).start()

    telegram_app = ApplicationBuilder().token(token).build()

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

    telegram_app.add_handler(conv_handler)
    telegram_app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
