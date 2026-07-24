import os
import logging
import re
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ============================================================
# Configuration
# ============================================================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN environment variable is not set. "
        "Add it in Railway's Variables tab (or a local .env file)."
    )

MAX_CHARS = int(os.environ.get("MAX_CHARS", 3000))

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ============================================================
# Plagiarism check logic (placeholder / pluggable)
# ============================================================
def split_into_sentences(text: str):
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s for s in sentences if len(s.split()) > 4]


async def check_plagiarism(text: str) -> dict:
    sentences = split_into_sentences(text)

    # --- Stub result: replace with real API call later ---
    return {
        "checked_sentences": len(sentences),
        "flagged": [],  # e.g. [(sentence, source_url, similarity_percent), ...]
        "overall_score": 0,
    }


def format_result(result: dict) -> str:
    if not result["flagged"]:
        return (
            f"✅ Checked {result['checked_sentences']} sentence(s).\n"
            "No matches found.\n\n"
            "(Note: plagiarism engine is still a placeholder — connect a "
            "real API in check_plagiarism() for actual results.)"
        )

    lines = [f"⚠️ Checked {result['checked_sentences']} sentence(s):"]
    for sentence, source, score in result["flagged"]:
        snippet = sentence[:60] + ("..." if len(sentence) > 60 else "")
        lines.append(f"• {score}% match — \"{snippet}\" → {source}")
    lines.append(f"\nOverall originality risk: {result['overall_score']}%")
    return "\n".join(lines)


# ============================================================
# Telegram handlers
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hi, I'm DupliScanBot!\n\n"
        "Send me any text and I'll scan it for potential plagiarism.\n\n"
        f"Max length per message: {MAX_CHARS} characters.\n\n"
        "Commands:\n"
        "/start – show this message\n"
        "/help – usage info"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Just paste or type text directly into the chat.\n"
        f"Keep it under {MAX_CHARS} characters per message."
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""

    if not text.strip():
        return

    if len(text) > MAX_CHARS:
        await update.message.reply_text(
            f"That message is {len(text)} characters — please keep it under "
            f"{MAX_CHARS} and try again."
        )
        return

    thinking_msg = await update.message.reply_text("🔍 Scanning your text...")

    try:
        result = await check_plagiarism(text)
        await thinking_msg.edit_text(format_result(result))
    except Exception:
        logger.exception("Plagiarism check failed")
        await thinking_msg.edit_text(
            "Something went wrong while checking that text. Please try again."
        )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Update %s caused error: %s", update, context.error)


# ============================================================
# Entrypoint
# ============================================================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_error_handler(error_handler)

    logger.info("DupliScanBot starting (polling mode)...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
