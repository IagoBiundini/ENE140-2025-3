# bot_base.py

from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

class BotTelegram:
    def __init__(self, app: Application):
        self.app = app
        self.modo_audio = set()
        self.chat_liberado = set()


    def criar_menu(self):
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🎙️ Transcrever Áudio", callback_data="opcao_audio"),
                InlineKeyboardButton("🖼️ Identificar Objeto", callback_data="opcao_imagem")
            ]
        ])

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        self.chat_liberado.add(chat_id)

        await update.message.reply_text(
            "Olá! O que você gostaria de fazer hoje?",
            reply_markup=self.criar_menu()
        )

    async def tratar_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        chat_id = query.message.chat.id

        if query.data == "opcao_audio":
            self.modo_audio.add(chat_id)
            await query.message.reply_text(
                "🎧 Envie um áudio para transcrição."
            )

        elif query.data == "opcao_imagem":
            await query.message.reply_text(
                "🖼️ Ótimo! Envie uma imagem."
            )

    def registrar(self):
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("help", self.start))
        self.app.add_handler(CallbackQueryHandler(self.tratar_callback, pattern="^opcao_"))
