# bot_telegram.py
from telegram.ext import ApplicationBuilder, ContextTypes

class BotTelegram:
    def __init__(self, token: str):
        self._token = token  # encapsulamento
        self._app = ApplicationBuilder().token(self._token).build()

    def get_app(self):
        return self._app

    async def processar_mensagem(self, update, context: ContextTypes.DEFAULT_TYPE):
        raise NotImplementedError("Este método deve ser sobrescrito")
