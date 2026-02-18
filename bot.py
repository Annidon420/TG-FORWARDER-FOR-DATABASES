import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from config import BOT_TOKEN, ADMIN_ID, ADMIN_KEY
import database as db

logging.basicConfig(level=logging.INFO)

# =========================
# START COMMAND
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.add_user(user.id)

    await update.message.reply_text(
        "👋 Welcome!\n\nSend video code to watch 🎬"
    )


# =========================
# ADMIN COMMAND
# =========================
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not admin.")
        return

    await update.message.reply_text("🔐 Enter Admin Security Key:")

    context.user_data["awaiting_key"] = True


# =========================
# HANDLE TEXT MESSAGES
# =========================
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    # ===== ADMIN KEY CHECK =====
    if context.user_data.get("awaiting_key"):
        if text == ADMIN_KEY:
            context.user_data["awaiting_key"] = False
            context.user_data["admin_logged"] = True

            keyboard = [
                [InlineKeyboardButton("➕ Add Video", callback_data="add_video")],
                [InlineKeyboardButton("📢 Broadcast", callback_data="broadcast")]
            ]

            await update.message.reply_text(
                "✅ Admin Panel",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await update.message.reply_text("❌ Wrong Key")
        return

    # ===== ADD VIDEO CODE STEP =====
    if context.user_data.get("adding_video"):
        context.user_data["video_code"] = text
        context.user_data["adding_video"] = False
        context.user_data["waiting_video_file"] = True

        await update.message.reply_text("🎥 Now send the video file.")
        return

    # ===== BROADCAST STEP =====
    if context.user_data.get("broadcast_mode"):
        users = db.get_all_users()

        for user in users:
            try:
                await context.bot.send_message(user[0], text)
            except:
                pass

        context.user_data["broadcast_mode"] = False
        await update.message.reply_text("✅ Broadcast Sent")
        return

    # ===== NORMAL USER VIDEO ACCESS =====
    video = db.get_video(text)

    if video:
        await context.bot.send_video(chat_id=user_id, video=video[0])
    else:
        await update.message.reply_text("❌ Invalid Code")


# =========================
# HANDLE VIDEO UPLOAD (ADMIN)
# =========================
async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("waiting_video_file"):
        file_id = update.message.video.file_id
        code = context.user_data.get("video_code")

        db.add_video(code, file_id)

        context.user_data["waiting_video_file"] = False

        await update.message.reply_text("✅ Video Added Successfully")


# =========================
# HANDLE BUTTONS
# =========================
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Add Video Button
    if query.data == "add_video":
        context.user_data["adding_video"] = True
        await query.message.reply_text("📝 Send Video Code (example: 101)")

    # Broadcast Button
    elif query.data == "broadcast":
        context.user_data["broadcast_mode"] = True
        await query.message.reply_text("📢 Send message to broadcast to all users")


# =========================
# MAIN
# =========================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))

    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
