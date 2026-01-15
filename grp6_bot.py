# -*- coding: utf-8 -*-

import os
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

class BotTelegram:
    def __init__(self):
        self._token = os.getenv("TOKEN_TELEGRAM")
        if not self._token:
            raise ValueError("Defina a variável de ambiente TOKEN_TELEGRAM")

        self._application = ApplicationBuilder().token(self._token).build()
        self._handlers()

    def _handlers(self):
        self._application.add_handler(CommandHandler("start", self.start))
        self._application.add_handler(
            MessageHandler(filters.ALL, self.tratar_mensagem)
        )

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message:
            await update.message.reply_text(
                "Olá! Por favor, envie um áudio ou uma imagem, para que eu realize sua transcrição ou reconhecimento."
            )

    async def tratar_mensagem(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message:
            return

        if update.message.text:
            await self.tratar_texto(update, context)
        elif update.message.photo:
            await self.tratar_imagem(update, context)
        elif update.message.voice or update.message.audio:
            await self.tratar_audio(update, context)
        else:
            await update.message.reply_text(
                "Desculpe, a mensagem que você enviou não é de um tipo suportado. Envie apenas imagens ou áudios!"
            )

    async def tratar_texto(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "Texto recebido com sucesso! No entanto, processar textos está fora do meu escopo.\nPor favor, envie somente áudios ou imagens ;)"
        )

    async def tratar_imagem(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "Imagem recebida com sucesso! Seu processamento está em andamento..."
        )

    async def tratar_audio(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "Áudio recebido com sucesso! Seu processamento está em andamento..."
        )

    def run(self):
        self._application.run_polling()
