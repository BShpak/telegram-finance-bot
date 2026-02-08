from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from datetime import datetime, timedelta

BOT_TOKEN = "8479393093:AAFvm_uJUE6wiECkWnaMjD2DU7iFP5xFGlk"
DATA_FILE = "finance.txt"

# ===== КАТЕГОРИИ И ПОДКАТЕГОРИИ =====
CATEGORIES = {
    "🍔 Еда": ["Еда в кафе/ресторанах", "Еда в столовой", "Продукты в супермаркетах", "Доставка"],
    "🚕 Транспорт": ["Такси", "Общественный транспорт"],
    "🏠 Жильё": ["Аренда"],
    "🎉 Развлечения": [],
    "📚 Саморазвитие": ["Книги", "Спорт", "Образование", "Прочее"],
    "✈️ Путешествия": ["Перелет", "Поезд", "Отель", "Прочее"],
    "💳 Ежемесячные подписки": [],
    "🎁 Подарки": ["Маше", "Кому-то"],
    "🗂 Прочее": []
}

# ===== КЛАВИАТУРЫ =====
def main_menu():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("➕ Добавить расход")],
            [KeyboardButton("💰 Добавить доход")],
            [KeyboardButton("📊 Составить отчёт")],
            [KeyboardButton("🗑 Очистить записи")],
        ],
        resize_keyboard=True
    )

def category_menu():
    keyboard = [[KeyboardButton(cat)] for cat in CATEGORIES.keys()]
    keyboard.append([KeyboardButton("⬅️ Назад")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def subcategory_menu(category):
    subs = CATEGORIES.get(category, [])
    if not subs:
        return None
    keyboard = [[KeyboardButton(sub)] for sub in subs]
    keyboard.append([KeyboardButton("⬅️ Назад")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def report_period_menu():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("📅 День"), KeyboardButton("🗓 Неделя")],
            [KeyboardButton("🗓 Месяц"), KeyboardButton("✏️ Свой период")],
            [KeyboardButton("⬅️ Назад")],
        ],
        resize_keyboard=True
    )

def clear_period_menu():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("📅 Сегодня"), KeyboardButton("🗓 Неделя")],
            [KeyboardButton("✏️ Свой период"), KeyboardButton("🗑 Все записи")],
            [KeyboardButton("⬅️ Назад")],
        ],
        resize_keyboard=True
    )

def confirm_menu():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("✅ Да"), KeyboardButton("❌ Нет")],
        ],
        resize_keyboard=True
    )

# ===== /start =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "Привет! 👋\nВыбери действие:",
        reply_markup=main_menu()
    )

# ===== ФУНКЦИЯ ОТЧЁТА =====
async def send_report(update, start_date, end_date):
    expenses_total = 0
    incomes_total = 0
    expenses_report = {}
    incomes_report = {}

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            for line in f:
                date_str, mode, category, amount = line.strip().split(";")
                date_val = datetime.strptime(date_str, "%Y-%m-%d").date()
                amount = float(amount)
                if start_date <= date_val <= end_date:
                    if mode == "expense":
                        expenses_total += amount
                        expenses_report[category] = expenses_report.get(category, 0) + amount
                    elif mode == "income":
                        incomes_total += amount
                        incomes_report[category] = incomes_report.get(category, 0) + amount
    except FileNotFoundError:
        await update.message.reply_text("Нет данных")
        return

    if expenses_total == 0 and incomes_total == 0:
        await update.message.reply_text("За выбранный период данных нет")
        return

    text = f"📊 Отчёт с {start_date} по {end_date}:\n\n"

    if expenses_report:
        text += "Расходы:\n"
        for cat, amt in expenses_report.items():
            text += f"  {cat}: {amt} ₽\n"
        text += f"Итого расходов: {expenses_total} ₽\n\n"
    else:
        text += "Расходов нет\n\n"

    if incomes_report:
        text += "Доходы:\n"
        for cat, amt in incomes_report.items():
            text += f"  {cat}: {amt} ₽\n"
        text += f"Итого доходов: {incomes_total} ₽\n\n"
    else:
        text += "Доходов нет\n\n"

    saldo = incomes_total - expenses_total
    text += f"💰 Сальдо (доходы − расходы): {saldo} ₽"

    await update.message.reply_text(text, reply_markup=main_menu())

# ===== ФУНКЦИЯ ОЧИСТКИ =====
def delete_records(from_date=None, to_date=None):
    try:
        if from_date is None and to_date is None:
            open(DATA_FILE, "w", encoding="utf-8").close()
            return

        lines_to_keep = []
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            for line in f:
                date_str = line.split(";")[0]
                date_val = datetime.strptime(date_str, "%Y-%m-%d").date()
                if not (from_date <= date_val <= to_date):
                    lines_to_keep.append(line)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            f.writelines(lines_to_keep)
    except FileNotFoundError:
        pass

# ===== ОБРАБОТЧИК СООБЩЕНИЙ =====
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    # ---- Назад ----
    if text == "⬅️ Назад":
        context.user_data.clear()
        await start(update, context)
        return

    # ---- Добавить расход ----
    if text == "➕ Добавить расход":
        context.user_data["mode"] = "expense"
        await update.message.reply_text("Выбери категорию:", reply_markup=category_menu())
        return

    # ---- Добавить доход ----
    if text == "💰 Добавить доход":
        context.user_data["mode"] = "income"
        await update.message.reply_text("Введи сумму дохода:")
        return

    # ---- Составить отчёт ----
    if text == "📊 Составить отчёт":
        context.user_data["mode"] = "report"
        await update.message.reply_text(
            "Выбери период:",
            reply_markup=report_period_menu()
        )
        return

    # ---- Очистить записи ----
    if text == "🗑 Очистить записи":
        context.user_data["mode"] = "clear"
        await update.message.reply_text(
            "Выбери период для очистки:",
            reply_markup=clear_period_menu()
        )
        return

    # ---- Выбор категории ----
    if context.user_data.get("mode") == "expense" and text in CATEGORIES:
        context.user_data["category"] = text
        subs_menu = subcategory_menu(text)
        if subs_menu:
            await update.message.reply_text("Выбери подкатегорию:", reply_markup=subs_menu)
        else:
            await update.message.reply_text("Введи сумму:")
        return

    # ---- Выбор подкатегории ----
    if context.user_data.get("mode") == "expense" and "category" in context.user_data:
        all_subs = sum(CATEGORIES.values(), [])
        if text in all_subs:
            context.user_data["category"] += f" — {text}"
            await update.message.reply_text("Введи сумму:")
            return

    # ---- Фиксированные периоды отчёта ----
    if context.user_data.get("mode") == "report":
        today = datetime.now().date()
        if text == "📅 День":
            await send_report(update, today, today)
            context.user_data.clear()
            return
        elif text == "🗓 Неделя":
            start_week = today - timedelta(days=6)
            await send_report(update, start_week, today)
            context.user_data.clear()
            return
        elif text == "🗓 Месяц":
            start_month = today.replace(day=1)
            await send_report(update, start_month, today)
            context.user_data.clear()
            return
        elif text == "✏️ Свой период":
            context.user_data["calendar_step"] = "from"
            await update.message.reply_text("Введи дату начала (дд.мм.гггг):")
            return

    # ---- Ввод дат для отчёта ----
    if context.user_data.get("calendar_step") == "from":
        try:
            context.user_data["from_date"] = datetime.strptime(text, "%d.%m.%Y").date()
            context.user_data["calendar_step"] = "to"
            await update.message.reply_text("Введи дату конца (дд.мм.гггг):")
        except ValueError:
            await update.message.reply_text("Неверный формат даты, попробуй ещё раз (дд.мм.гггг)")
        return

    if context.user_data.get("calendar_step") == "to":
        try:
            from_date = context.user_data.get("from_date")
            to_date = datetime.strptime(text, "%d.%m.%Y").date()
            if from_date > to_date:
                await update.message.reply_text("Дата конца не может быть раньше начала. Начни заново.")
                context.user_data.clear()
                return
            await send_report(update, from_date, to_date)
            context.user_data.clear()
        except ValueError:
            await update.message.reply_text("Неверный формат даты, попробуй ещё раз (дд.мм.гггг)")
        return

    # ---- Ввод суммы ----
    if context.user_data.get("mode") in ["expense", "income"]:
        try:
            amount = float(text)
        except ValueError:
            await update.message.reply_text("❌ Введи число")
            return
        date_str = datetime.now().strftime("%Y-%m-%d")
        mode = context.user_data["mode"]
        category = context.user_data.get("category", "Доход")
        with open(DATA_FILE, "a", encoding="utf-8") as f:
            f.write(f"{date_str};{mode};{category};{amount}\n")
        await update.message.reply_text(f"✅ Записал:\n{category} — {amount} ₽", reply_markup=main_menu())
        context.user_data.clear()
        return

    # ---- ОЧИСТКА ЗАПИСЕЙ ----
    if context.user_data.get("mode") == "clear":
        today = datetime.now().date()

        # Фиксированные периоды
        if text == "📅 Сегодня":
            context.user_data["clear_from"] = today
            context.user_data["clear_to"] = today
            await update.message.reply_text("Вы точно хотите очистить записи за сегодня?", reply_markup=confirm_menu())
            return
        elif text == "🗓 Неделя":
            context.user_data["clear_from"] = today - timedelta(days=6)
            context.user_data["clear_to"] = today
            await update.message.reply_text("Вы точно хотите очистить записи за неделю?", reply_markup=confirm_menu())
            return
        elif text == "✏️ Свой период":
            context.user_data["calendar_step"] = "clear_from"
            await update.message.reply_text("Введи дату начала периода (дд.мм.гггг):")
            return
        elif text == "🗑 Все записи":
            context.user_data["clear_from"] = None
            context.user_data["clear_to"] = None
            await update.message.reply_text("Вы точно хотите очистить все записи?", reply_markup=confirm_menu())
            return

    # Ввод дат для собственного периода очистки
    if context.user_data.get("calendar_step") == "clear_from":
        try:
            context.user_data["clear_from"] = datetime.strptime(text, "%d.%m.%Y").date()
            context.user_data["calendar_step"] = "clear_to"
            await update.message.reply_text("Введи дату конца периода (дд.мм.гггг):")
        except ValueError:
            await update.message.reply_text("Неверный формат даты, попробуй ещё раз (дд.мм.гггг)")
        return

    if context.user_data.get("calendar_step") == "clear_to":
        try:
            context.user_data["clear_to"] = datetime.strptime(text, "%d.%m.%Y").date()
            context.user_data["calendar_step"] = None
            await update.message.reply_text("Вы точно хотите очистить выбранный период?", reply_markup=confirm_menu())
        except ValueError:
            await update.message.reply_text("Неверный формат даты, попробуй ещё раз (дд.мм.гггг)")
        return

    # Подтверждение очистки
    if text == "✅ Да" and context.user_data.get("mode") == "clear":
        delete_records(context.user_data.get("clear_from"), context.user_data.get("clear_to"))
        await update.message.reply_text("✅ Записи очищены", reply_markup=main_menu())
        context.user_data.clear()
        return

    if text == "❌ Нет" and context.user_data.get("mode") == "clear":
        await update.message.reply_text("Отмена очистки", reply_markup=main_menu())
        context.user_data.clear()
        return

# ===== ЗАПУСК БОТА =====
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("Бот запущен...")
app.run_polling()
