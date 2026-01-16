# main.py

import os
from telegram.ext import Application

from bot_telegram import BotTelegram
from bot_audio import BotAudio
from bot_imagem import BotImagem


def main():
    # ==================================================
    # LÊ TOKEN DO AMBIENTE
    # ==================================================
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

    if not TOKEN:
        raise RuntimeError(
            "❌ TOKEN não encontrado.\n"
            "Defina a variável de ambiente TELEGRAM_BOT_TOKEN."
        )

    # ==================================================
    # CRIA A APLICAÇÃO
    # ==================================================
    app = Application.builder().token(TOKEN).build()

    # ==================================================
    # REGISTRA OS BOTS
    # ==================================================
    bot_base = BotTelegram(app)
    bot_audio = BotAudio(app)
    bot_imagem = BotImagem(app, "yolov8n.pt")

    bot_base.registrar()
    bot_audio.registrar()
    bot_imagem.registrar()

    # ==================================================
    # INICIA O BOT
    # ==================================================
    app.run_polling()


if __name__ == "__main__":
    main()
