import logging

from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from TOKEN import token

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

class BotTelegram:
    def __init__(self):
        pass

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /start is issued."""
        user = update.effective_user
        await update.message.reply_html(
            rf"Hello World, Hi {user.mention_html()}!",
            reply_markup=ForceReply(selective=True),
        )

def main() -> None:
    application = Application.builder().token(token).build()
    app = BotTelegram()

    application.add_handler(CommandHandler("start", app.start))

    #Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()