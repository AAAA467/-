import os
import random
import logging
from flask import Flask, request, abort
from telegram import Bot, Update, ReplyKeyboardMarkup
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, ConversationHandler, filters, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN not set in environment variables!")

bot = Bot(token=BOT_TOKEN)

# Dispatcher для обработки апдейтов
dispatcher = Dispatcher(bot, None, workers=0, use_context=True)

CHOOSING, SOLVING = range(2)
user_state = {}

menu_keyboard = ReplyKeyboardMarkup(
    [['Задача 1', 'Задача 2', 'Задача 3', 'Задача 4'], ['/skip', '/start']],
    resize_keyboard=True
)

# --- Твои функции генерации задач и хендлеры (как в твоем коде) ---
# ... (сюда вставь все функции generate_task1, start, choose_task, answer_handler, skip_handler и т.д.) ...
# Для сокращения здесь — вставь твой код из предыдущего сообщения с функциями и хендлерами

# ВАЖНО: перепиши хендлеры, чтобы они были async, как у тебя, но Flask будет их запускать в sync режиме через dispatcher

async def start(update, context):
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

# Аналогично остальные хендлеры...

# Добавляем хендлеры в диспетчер
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, filters

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

dispatcher.add_handler(conv_handler)

# --- Flask route для webhook ---

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
        return "ok", 200
    else:
        abort(405)

if __name__ == "__main__":
    # Запускаем Flask на нужном порту (обычно Render использует порт из env PORT)
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
