# bot_audio.py

import os
import re
import subprocess
import whisper

from bot_telegram import BotTelegram

from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from telegram.ext import (
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

# ======================================================
# Função para verificar se há fala no áudio
# ======================================================
def audio_tem_fala(caminho_audio, limite_db=-40):
    comando = [
        "ffmpeg",
        "-i", caminho_audio,
        "-af", "volumedetect",
        "-f", "null",
        "-"
    ]

    resultado = subprocess.run(
        comando,
        stderr=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        text=True
    )

    match = re.search(r"mean_volume:\s*(-?\d+(\.\d+)?) dB", resultado.stderr)

    if not match:
        return False

    volume_medio = float(match.group(1))
    return volume_medio > limite_db


# ======================================================
# Classe BotAudio
# ======================================================
class BotAudio(BotTelegram):
    def __init__(self, app):
        super().__init__(app)
        self.modelo = whisper.load_model("base")

    # --------------------------------------------------
    # Registra handlers do bot de áudio
    # --------------------------------------------------
    def registrar(self):

        # =========================
        # RECEBE ÁUDIO
        # =========================
        self.app.add_handler(
            MessageHandler(filters.VOICE, self.receber_audio)
        )

        # =========================
        # BOTÕES: ENVIAR OUTRO ÁUDIO?
        # =========================
        self.app.add_handler(
            CallbackQueryHandler(
                self.tratar_botoes_audio,
                pattern="^audio_(sim|nao)$"
            )
        )

    # --------------------------------------------------
    # Handler de áudio
    # --------------------------------------------------
    async def receber_audio(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        
        chat_id = update.effective_chat.id

        duracao = update.message.voice.duration
        if duracao < 2:
            await update.message.reply_text(
                "⏱️ O áudio é muito curto para transcrição.\n"
                "Fale uma frase completa, por favor."
            )
            return

        await update.message.reply_text("🎧 Processando áudio...")

        await self.processar_audio(update, context)

    # --------------------------------------------------
    # Processamento do áudio
    # --------------------------------------------------
    async def processar_audio(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id

        file = await update.message.voice.get_file()

        os.makedirs("audios", exist_ok=True)
        caminho_audio = f"audios/{file.file_unique_id}.ogg"

        await file.download_to_drive(caminho_audio)

        # =========================
        # FILTRO DE SILÊNCIO
        # =========================
        if not audio_tem_fala(caminho_audio):
            await update.message.reply_text(
                "🔇 Não detectei fala no áudio.\n"
                "Tente falar um pouco mais alto ou falar algo."
            )
            os.remove(caminho_audio)
            return

        # =========================
        # TRANSCRIÇÃO
        # =========================
        resultado = self.modelo.transcribe(
            caminho_audio,
            language="pt",
            fp16=False,
            temperature=0
        )

        texto = resultado["text"].strip()

        if texto:
            await update.message.reply_text(
                f"📝 Transcrição:\n{texto}"
            )
        else:
            await update.message.reply_text(
                "⚠️ Não consegui identificar fala no áudio."
            )

        os.remove(caminho_audio)

        # 🔒 ENCERRA O CICLO DO ÁUDIO
        if chat_id in self.chat_liberado:
            self.chat_liberado.remove(chat_id)

        # =========================
        # PERGUNTA SE QUER ENVIAR OUTRO
        # =========================
        teclado = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🎙️ Enviar outro áudio",
                    callback_data="audio_sim"
                ),
                InlineKeyboardButton(
                    "❌ Encerrar",
                    callback_data="audio_nao"
                )
            ]
        ])

        await update.message.reply_text(
            "Deseja enviar outro áudio?",
            reply_markup=teclado
        )

    # --------------------------------------------------
    # Trata resposta dos botões
    # --------------------------------------------------
    async def tratar_botoes_audio(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        chat_id = query.message.chat_id

        if query.data == "audio_sim":
            # 🔓 LIBERA novo áudio
            self.chat_liberado.add(chat_id)
            await query.message.reply_text(
                "🎧 Pode enviar o próximo áudio."
            )

        elif query.data == "audio_nao":
            await query.message.reply_text(
                "✔️ Tudo certo.\nQuando quiser, digite /start."
            )
