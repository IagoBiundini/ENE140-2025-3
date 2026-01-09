import os
import speech_recognition as sr
from pydub import AudioSegment
from telegram.ext import MessageHandler, filters
from bot_base import BotTelegram

class BotAudio(BotTelegram):
    def __init__(self, token):
        super().__init__(token)
        self.recognizer = sr.Recognizer()

        self.app.add_handler(
            MessageHandler(filters.VOICE, self.processar_audio)
        )

    async def processar_audio(self, update, context):
        voice = update.message.voice
        file = await voice.get_file()

        ogg_path = "temp_audio.ogg"
        wav_path = "temp_audio.wav"

        await file.download_to_drive(ogg_path)

        audio_ogg = AudioSegment.from_ogg(ogg_path)
        audio_ogg.export(wav_path, format="wav")

        with sr.AudioFile(wav_path) as source:
            audio = self.recognizer.record(source)

        try:
            texto = self.recognizer.recognize_google(
                audio, language="pt-BR"
            )
            await update.message.reply_text(
                f"🎧 Texto reconhecido:\n{texto}"
            )
        except:
            await update.message.reply_text(
                "❌ Não foi possível reconhecer o áudio."
            )

        os.remove(ogg_path)
        os.remove(wav_path)


