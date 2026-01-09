from telegram.ext import ApplicationBuilder, CommandHandler

class BotTelegram:
    
    def __init__(self, token: str):
        self.__token = token
        self.app = ApplicationBuilder().token(self.__token).build()

        self.app.add_handler(CommandHandler("start", self.start))

    async def start(self, update, context):
        await update.message.reply_text(
            "🤖 Olá!\n"
            "Envie uma imagem ou um áudio para análise."
        )

    def run(self):

        self.app.run_polling()
