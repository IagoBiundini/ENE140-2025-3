# grupo6-audio
# Subclasse responsável pela transcrição de áudios

from grp6_bot import BotTelegram  # Classe mãe
from vosk import Model, KaldiRecognizer

import os
import wave
import tempfile
import json
import subprocess

FFMPEG_PATH = r"C:\Users\leca_\Downloads\ffmpeg\ffmpeg-8.0.1-essentials_build\bin\ffmpeg.exe"


class BotAudio(BotTelegram):

    def __init__(self):
        super().__init__()

        # Caminho absoluto do modelo Vosk (robusto para Windows/Colab)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(base_dir, "models", "vosk-model-small-pt-0.3")

        self.model = Model(model_path)

    async def tratar_audio(self, update, context):
        # Segurança básica
        if not update.message:
            return

        # Mensagem inicial
        await update.message.reply_text(
            "Áudio recebido!\nRealizando análise, isso pode demorar um tempo..."
        )

        # Identifica tipo de áudio
        if update.message.voice:  # Áudio do Telegram
            file = await update.message.voice.get_file()
            suffix = ".ogg"

        elif update.message.audio:  # Arquivo externo
            mime = update.message.audio.mime_type
            if not mime or not mime.startswith("audio/"):
                await update.message.reply_text(
                    "Hmm... Parece que o arquivo enviado não é um áudio válido."
                )
                return

            file = await update.message.audio.get_file()
            suffix = os.path.splitext(update.message.audio.file_name)[1]

        else:
            await update.message.reply_text(
                "Envie uma mensagem de voz ou um arquivo de áudio para transcrição."
            )
            return

        # Salva áudio temporário
        temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=suffix).name
        await file.download_to_drive(temp_audio)

        # Converte para WAV padrão Vosk
        wav_path = temp_audio.replace(suffix, ".wav")
        
        subprocess.run(
            [
                FFMPEG_PATH,
                "-i", temp_audio,
                "-ar", "16000",
                "-ac", "1",
                wav_path,
                "-y"
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # Processa o WAV
        wf = wave.open(wav_path, "rb")
        rec = KaldiRecognizer(self.model, wf.getframerate())

        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            rec.AcceptWaveform(data)

        texto = json.loads(rec.FinalResult()).get("text", "")

        # Resposta ao usuário
        if not texto.strip():
            await update.message.reply_text(
                "Poxa, seu áudio está vazio \nTente enviar outro com som mais claro."
            )
        else:
            await update.message.reply_text(
                f"Muito bem! Aqui está o seu áudio transcrito:\n{texto}"
            )
