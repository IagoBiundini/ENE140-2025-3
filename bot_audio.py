# bot_audio.py
import os
import whisper
import telebot
from bot_telegram import BotTelegram
import subprocess
import re

# Função para verificar se há fala no áudio
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

class BotAudio(BotTelegram):
    def __init__(self, token):
        super().__init__(token)
        self.modelo = whisper.load_model("base")

    def configurar_handlers(self):
        super().configurar_handlers()

        @self.bot.message_handler(content_types=['voice'])
        def receber_audio(message):
            chat_id = message.chat.id

            # =========================
            # FILTRO DE DURAÇÃO
            # =========================
            duracao = message.voice.duration  # segundos

            if duracao < 2:
                self.bot.send_message(
                    chat_id,
                    "⏱️ O áudio é muito curto para transcrição.\n"
                    "Fale uma frase completa, por favor."
                )
                return

            self.bot.send_message(chat_id, "🎧 Processando áudio...")

            self.processar_audio(message)

    def processar_audio(self, message):
        chat_id = message.chat.id

        file_info = self.bot.get_file(message.voice.file_id)
        downloaded_file = self.bot.download_file(file_info.file_path)

        os.makedirs("audios", exist_ok=True)
        caminho_audio = f"audios/{message.voice.file_id}.ogg"

        with open(caminho_audio, "wb") as f:
            f.write(downloaded_file)
        
        # =========================
        # FILTRO DE SILÊNCIO
        # =========================
        
        if not audio_tem_fala(caminho_audio):
            self.bot.send_message(
                chat_id,
                "🔇 Não detectei fala no áudio.\n"
                "Tente falar um pouco mais alto ou falar algo."
            )
            os.remove(caminho_audio)
            return

        # ============
        # Transcrição
        # ============
        
        resultado = self.modelo.transcribe(
            caminho_audio,
            language="pt",
            fp16=False, ## muda para False se não tiver GPU
            temperature=0 ## para reduzir alucinações do whisper
        )
        
        texto = resultado["text"].strip()

        if texto == "":
            self.bot.send_message(
                chat_id,
                "⚠️ Não consegui identificar fala no áudio."
            )
        else:
            self.bot.send_message(
                chat_id,
                f"📝 Transcrição:\n{texto}"
            )

        os.remove(caminho_audio)
