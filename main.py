# main.py
from telegram import Update
from telegram.ext import (ContextTypes, MessageHandler, CommandHandler, CallbackQueryHandler, filters)
import os
from dotenv import load_dotenv

from bot_imagem import BotImagem
from bot_audio import BotAudio
from bot_telegram import BotTelegram

load_dotenv()
TOKEN = os.getenv('TOKEN')

bot_base = BotTelegram(TOKEN)
bot_imagem = BotImagem(TOKEN)
bot_audio = BotAudio(TOKEN)

# -------- COMANDOS -------- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (
        "👋 Bem-vindo!\n\n"
        "Escolha o que você deseja fazer:\n"
        "📸 /imagem → Analisar uma imagem com YOLO\n"
        "🎤 /audio → Converter áudio em texto\n"
        "📝 /texto → Enviar apenas texto\n"
    )
    await update.message.reply_text(texto)

async def modo_imagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["modo"] = "imagem"
    await update.message.reply_text(
        "📸 Modo imagem ativado!\nEnvie uma foto."
    )

async def modo_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["modo"] = "audio"
    await bot_audio.start(update, context)

async def modo_texto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["modo"] = "texto"
    await update.message.reply_text(
        "📝 Modo texto ativado!\nEnvie uma mensagem de texto."
    )

# -------- ROTEADOR -------- #

async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    modo = context.user_data.get("modo")

    # ----- MODO IMAGEM -----
    if modo == "imagem":
        if update.message.photo:
            await bot_imagem.processar_mensagem(update, context)
        else:
            await update.message.reply_text(
                "⚠️ Você está no modo imagem. Envie uma FOTO."
            )

    # ----- MODO ÁUDIO -----
    elif modo == "audio":
        if update.message.voice or update.message.audio:
            await bot_audio.handle_audio(update, context)
        else:
            await update.message.reply_text(
                "⚠️ Você está no modo áudio. Utilize os botões interativos para navegar por essa área."
            )

    # ----- MODO TEXTO -----
    elif modo == "texto":
        if update.message.text:
            await update.message.reply_text(
                f"📝 Texto recebido:\n{update.message.text}"
            )
        else:
            await update.message.reply_text(
                "⚠️ Envie apenas TEXTO."
            )

    # ----- SEM MODO -----
    else:
        await start(update, context)

# -------- APP -------- #

app = bot_base.get_app()

app.add_handler(CallbackQueryHandler(bot_audio.button_handler))
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("imagem", modo_imagem))
app.add_handler(CommandHandler("audio", modo_audio))
app.add_handler(CommandHandler("texto", modo_texto))
app.add_handler(MessageHandler(filters.ALL, router))

print("Bot is working...")
app.run_polling()