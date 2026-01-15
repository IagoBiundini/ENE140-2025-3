from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import os
import speech_recognition as sr
from pydub import AudioSegment
from TOKEN import str_token

class BotTelegram:
    def __init__(self, token: str):
        self.application = Application.builder().token(token).build()
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help))
        self.application.add_handler(MessageHandler(filters.UpdateType.MESSAGE, self.main_handler))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /start is issued."""
        user = update.effective_user
        await update.message.reply_html(
            rf"Hello World, Hi {user.mention_html()}!",
            reply_markup=ForceReply(selective=True),
        )

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /help is issued."""
        await update.message.reply_text("""
Seja bem-vindo ao Telegram Bot do Grupo 5 da turma ENE140!
Este é um bot capaz de processar imagens e mensagens de voz.
Ele reconhece automaticamente quando você envia uma imagem e realizar o reconhecimento de objetos nela usando YOLO.
Além disso, quando você enviar um áudio, ele vai transcrever tudo o que você disse!!

Comandos disponíveis:
/start - Inicia a interação com o bot
/help - Exibe esta mensagem de ajuda
                                        """)
    
    async def main_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.message.photo:
            await BotImagem(self).processar_mensagem(update, context)
            
        elif update.message.voice:
            await BotAudio(self).processar_mensagem(update, context)
            
        elif update.message.text:
            await update.message.reply_text("Texto recebido.")
            
        else:
            await update.message.reply_text("Conteúdo não listado.")
            
    def run(self):
        print("BotTelegram iniciado. Esperando mensagens...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES) #ctrl+c

class BotImagem(BotTelegram):
    def __init__(self, parentbot: BotTelegram):
        self.parent = parentbot

    async def processar_mensagem(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Imagem recebida.")

class BotAudio(BotTelegram):
    def __init__(self, parent_bot: BotTelegram):
            self.parent = parent_bot
    
    async def processar_mensagem(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Audio recebido.")
        #corpo principal para conversao de ogg para WAV("sr" funciona apenas com WAV )
        audio = update.message.voice
        arquivo = await context.bot.get_file(audio.file_id)
        arqOGG = f"{audio.file_id}.ogg"
        arqWAV = f"{audio.file_id}.wav"
        await arquivo.download_to_drive(arqOGG)
        try:

         conversao = AudioSegment.from_file(arqOGG , format= "ogg")
         conversao.export(arqWAV , format = "wav")
        except Exception as e:
            await update.message.reply_text(f"Erro ao converter áudio: {e}")
            return

        recognizer = sr.Recognizer()
        #Corpo principal para transcricao do audio
        try:

         with sr.AudioFile(arqWAV) as source:
            audio_data = recognizer.record(source)
            texto = recognizer.recognize_google(audio_data, language="pt-BR")

         await update.message.reply_text(f"Transcrito: {texto}")
         
        except sr.UnknownValueError:
            await update.message.reply_text("Não consegui entender. Repita, por favor.")
            return

        except Exception as e:
            await update.message.reply_text(f"Erro ao transcrever: {e}")
            return
        #Apaga os arquivos de audio que usamos pra transcrever o audio DESSE loop
        finally:
            if os.path.exists(arqOGG):
                os.remove(arqOGG)
            if os.path.exists(arqWAV):
                os.remove(arqWAV)