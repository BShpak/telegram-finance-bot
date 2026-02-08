import os
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# Берём токен из переменной окружения Render
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Файл для хранения расходов и доходов
DATA_FILE = "expenses.txt"

# Категории и подкатегории
CATEGORIES = {
    "Еда": ["Еда в кафе/ресторанах", "Еда в столовой", "Продукты в супермаркетах", "Доставка"],
    "Транспорт": ["Такси", "Общественный транспорт"],
    "Жилье": ["Аренда"],
    "Развлечения": [],
    "Саморазвитие": ["Книги", "Спорт", "Образование", "Прочее"],
    "Путешествия": ["Перелет", "Поезд", "Отель", "Прочее"],
    "Ежемесячные подписки": [],
    "Подарки": ["Маше", "Кому-то"],
    "Прочее": []
}

# ---------- Старт и главное меню ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Добавить расход", callback_data="add_expense")],
        [InlineKeyboardButton("Добавить доход", callback_data="add_income")],
        [InlineKeyboardButton("Составить отчет", callback_data="report")],
        [InlineKeyboardButton("Очистить записи", callback_data="clear")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Главное меню:", reply_markup=reply_markup)

# ---------- Обработка callback кнопок ----------
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "add_expense":
        keyboard = [
            [InlineKeyboardButton(cat, callback_data=f"cat_exp:{cat}")] for cat in CATEGORIES
        ]
        await query.edit_message_text("Выбери категорию расхода:", reply_markup=InlineKeyboardMarkup(keyboard))
        
    elif query.data == "add_income":
        await query.edit_message_text("Отправь доход в формате:\nсумма категория\nНапример:\n5000 зарплата")
        
    elif query.data == "report":
        keyboard = [
            [InlineKeyboardButton("День", callback_data="report_day")],
            [InlineKeyboardButton("Неделя", callback_data="report_week")],
            [InlineKeyboardButton("Месяц", callback_data="report_month")]
        ]
        await query.edit_message_text("Выбери период для отчета:", reply_markup=InlineKeyboardMarkup(keyboard))
        
    elif query.data == "clear":
        keyboard = [
            [InlineKeyboardButton("Все записи", callback_data="clear_all")],
            [InlineKeyboardButton("Назад", callback_data="back")],
        ]
        await query.edit_message_text("Выбери, что очистить:", reply_markup=InlineKeyboardMarkup(keyboard))
        
    elif query.data == "back":
        await start(update, context)

# ---------- Добавление расхода / дохода ----------
async def handle_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        parts = text.split()
        if len(parts) == 2:
            category, amount = parts
            amount = float(amount)
        else:
            await update.message.reply_text("Неверный формат. Например: еда 1200")
            return
    except ValueError:
        await update.message.reply_text("Неверный формат. Например: еда 1200")
        return
    
    date = datetime.now().strftime("%Y-%m-%d")
    with open(DATA_FILE, "a", encoding="utf-8") as f:
        f.write(f"{date};expense;{category};{amount}\n")
    
    await update.message.reply_text(f"✅ Записан расход: {category} — {amount} ₽")

async def handle_income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        parts = text.split()
        if len(parts) == 2:
            amount, category = parts
            amount = float(amount)
        else:
            await update.message.reply_text("Неверный формат. Например: 5000 зарплата")
            return
    except ValueError:
        await update.message.reply_text("Неверный формат. Например: 5000 зарплата")
        return
    
    date = datetime.now().strftime("%Y-%m-%d")
    with open(DATA_FILE, "a", encoding="utf-8") as f:
        f.write(f"{date};income;{category};{amount}\n")
    
    await update.message.reply_text(f"✅ Записан доход: {category} — {amount} ₽")

# ---------- Отчеты ----------
def filter_records(start_date, end_date):
    expenses = []
    incomes = []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            for line in f:
                date_str, typ, category, amount = line.strip().split(";")
                date = datetime.strptime(date_str, "%Y-%m-%d")
                amount = float(amount)
                if start_date <= date <= end_date:
                    if typ == "expense":
                        expenses.append((category, amount))
                    else:
                        incomes.append((category, amount))
    except FileNotFoundError:
        pass
    return expenses, incomes

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE, period="day"):
    today = datetime.now().date()
    if period == "day":
        start_date = end_date = today
    elif period == "week":
        start_date = today - timedelta(days=7)
        end_date = today
    elif period == "month":
        start_date = today.replace(day=1)
        end_date = today
    
    expenses, incomes = filter_records(start_date, end_date)
    
    total_exp = sum(amount for _, amount in expenses)
    total_inc = sum(amount for _, amount in incomes)
    saldo = total_inc - total_exp
    
    text = f"📊 Отчет с {start_date} по {end_date}:\n\n"
    text += f"💰 Доходы: {total_inc} ₽\n"
    text += f"🛒 Расходы: {total_exp} ₽\n"
    text += f"⚖️ Сальдо: {saldo} ₽"
    
    await update.callback_query.edit_message_text(text)

# ---------- Очистка записей ----------
async def clear_records(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "clear_all":
        open(DATA_FILE, "w").close()
        await query.edit_message_text("✅ Все записи очищены")
    elif query.data == "back":
        await start(update, context)

# ---------- Основной блок ----------
app = ApplicationBuilder().token(BOT_TOKEN).build()

# Handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_expense))
app.add_handler(MessageHandler(filters.Regex(r'^\d+(\.\d+)? .+$'), handle_income))
app.add_handler(CallbackQueryHandler(menu_handler))

print("Бот запущен...")
app.run_polling()
