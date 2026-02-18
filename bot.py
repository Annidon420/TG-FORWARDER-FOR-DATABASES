import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from config import BOT_TOKEN, ADMIN_ID, ADMIN_KEY, FORCE_CHANNELS
import database as db

logging.basicConfig(level=logging.INFO)

admin_logged = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.add_user(user.id)

    await update.message.reply_text(
        "Send video code to watch 🎬"
    )

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Enter Admin Security Key 🔐")

    admin_logged[update.effective_user.id] = False

async def check_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id == ADMIN_ID and update.message.text == ADMIN_KEY:
        admin_logged[user_id] = True

        keyboard = [
            [InlineKeyboardButton("Add Video", callback_data="add")],
            [InlineKeyboardButton("Broadcast", callback_data="broadcast")]
        ]

        await update.message.reply_text(
            "Admin Panel",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await handle_user_message(update, context)

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "add":
        await query.message.reply_text("Send video with code like:\nCODE 123")

        context.user_data["adding"] = True

    elif query.data == "broadcast":
        await query.message.reply_text("Send message to broadcast")

        context.user_data["broadcast"] = True

async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if context.user_data.get("adding"):
        code = text.split()[1]
        context.user_data["code"] = code
        await update.message.reply_text("Now send the video file 🎥")
        return

    if context.user_data.get("broadcast"):
        users = db.get_all_users()
        for user in users:
            try:
                await context.bot.send_message(user[0], text)
            except:
                pass

        context.user_data["broadcast"] = False
        await update.message.reply_text("Broadcast Sent ✅")
        return

    video = db.get_video(text)

    if video:
        await context.bot.send_video(chat_id=user_id, video=video[0])
    else:
        await update.message.reply_text("Invalid Code ❌")

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("adding"):
        code = context.user_data["code"]
        file_id = update.message.video.file_id

        db.add_video(code, file_id)

        context.user_data["adding"] = False
        await update.message.reply_text("Video Added ✅")

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CallbackQueryHandler(handle_buttons))
app.add_handler(MessageHandler(filters.VIDEO, handle_video))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_key))

app.run_polling()
