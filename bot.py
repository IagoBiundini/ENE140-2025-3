from turtle import update
import cv2
from ultralytics import YOLO
from datetime import datetime
from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from telegram.error import TimedOut
import traceback
import os
import speech_recognition as sr
from pydub import AudioSegment

def log(msg: str):
    with open("log.txt", "a") as f:
        f.write(f"[{datetime.now()}]" + msg + "\n")


class BotTelegram:
    def __init__(self, token: str):
        self.application = Application.builder().token(token).build()
        self.application.add_handler(CommandHandler("test", self.test))
        self.application.add_handler(CommandHandler("help", self.help))
        self.application.add_handler(CommandHandler("log", self.log))
        self.application.add_handler(MessageHandler(filters.UpdateType.MESSAGE, self.main_handler))

    async def test(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /test is issued."""
        log("Comando /test recebido.")
        user = update.effective_user
        await update.message.reply_html(
            rf"Olá, {user.mention_html()}! O bot está rodando normalmente.",
            reply_markup=ForceReply(selective=True),
        )

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /help is issued."""
        log("Comando /help recebido.")
        await update.message.reply_text("""
Seja bem-vindo ao Telegram Bot do Grupo 5 da turma ENE140!
Este é um bot capaz de processar imagens e mensagens de voz.
Ele reconhece automaticamente quando você envia uma imagem e realizar o reconhecimento de objetos nela usando YOLO.
Além disso, quando você enviar um áudio, ele vai transcrever tudo o que você disse!!

Comandos disponíveis:
/test - Verifica se o bot está funcionando
/help - Exibe esta mensagem de ajuda
/log - Exibe o log de atividades do bot desde a última reinicialização
                                        """)
        
    async def log(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send the log file when the command /log is issued."""
        log("Comando /log recebido.")
        if os.path.exists("log.txt"):
            with open("log.txt", "r") as f:
                log_content = f.read()
            if log_content:
                await update.message.reply_text(f"Log de atividades:\n{log_content}")
            else:
                await update.message.reply_text("O log está vazio.")
        else:
            await update.message.reply_text("Nenhum log encontrado.")
    
    async def main_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.message.photo:
            log(f"Imagem recebida.")
            await BotImagem(self).processar_mensagem(update, context)
            
        elif update.message.voice:
            log(f"Mensagem de áudio recebida.")
            await BotAudio(self).processar_mensagem(update, context)
            
        elif update.message.text:
            log(f"Mensagem de texto recebida: {update.message.text}")
            await update.message.reply_text("Texto recebido.")
        else:
            log(f"Conteúdo não listado recebido.")
            await update.message.reply_text("Ops... não trabalhamos com este tipo de mensagem ainda!")
            
    def run(self):
        print("BotTelegram iniciado. Esperando mensagens...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES) #ctrl+c


class BotImagem(BotTelegram):
    def __init__(self, parentbot: BotTelegram):
        self.parent = parentbot
        self.model = YOLO("yolov8n.pt")

    async def processar_mensagem(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message.photo:
            return
        
        try:
            await update.message.reply_text("Imagem recebida.")

            src_img = update.message.photo[-1]
            arquivo = await src_img.get_file()

            path_original = f"{src_img.file_id}.jpg"
            path_resultado = f"{src_img.file_id}_result.jpg"
            await arquivo.download_to_drive(path_original)

            results = self.model(str(path_original))[0]
            img = cv2.imread(path_original)
            detections = []

            for box in results.boxes:
                cls_id = int(box.cls[0])
                label = self.model.names[cls_id]
                conf = float(box.conf[0])

                x1, y1, x2, y2 = map(int, box.xyxy[0])
                detections.append(f"{label} ({conf:.2f})")

                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(
                    img,
                    f"{label} {conf:.2f}",
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0),
                    2,
                )
            cv2.imwrite(str(path_resultado), img)

            await update.message.reply_photo(
                photo=open(path_resultado, "rb"),
                caption="Detecções:")
            
            if detections:
                text = "Objetos detectados:\n" + "\n".join(detections)
                await update.message.reply_text(text)
            else:
                text = "Nenhum objeto detectado."
                await update.message.reply_text(text)

            log(text)

        except TimedOut:
            msg = "A imagem demorou demais para ser enviada. Tente novamente."
            await update.message.reply_text(msg)
            log("TIMEOUT ao enviar imagem para o Telegram.")

        except Exception as e:
            await update.message.reply_text("Erro ao processar a imagem.")
            log(f"ERRO inesperado: {e}")
            log(traceback.format_exc())

        finally:
            if path_original and os.path.exists(path_original):
                os.remove(path_original)
            if path_resultado and os.path.exists(path_resultado):
                os.remove(path_resultado)


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
            text = f"Erro ao converter áudio: {e}"
            await update.message.reply_text(text)
            log(text)
            return

        recognizer = sr.Recognizer()
        #Corpo principal para transcricao do audio
        try:
            with sr.AudioFile(arqWAV) as source:
                audio_data = recognizer.record(source)
                texto = recognizer.recognize_google(audio_data, language="pt-BR")

            await update.message.reply_text(f"Transcrição: {texto}")
            msg = f"Transcrição realizada com sucesso: {texto}"

        except sr.UnknownValueError:
            await update.message.reply_text("Não consegui entender. Repita, por favor.")
            msg = "Erro: áudio não compreendido."

        except Exception as e:
            await update.message.reply_text(f"Erro ao transcrever: {e}")
            msg = f"Erro ao transcrever áudio: {e}"
            return
        #Apaga os arquivos de audio que usamos pra transcrever o audio DESSE loop
        finally:
            if os.path.exists(arqOGG):
                os.remove(arqOGG)
            if os.path.exists(arqWAV):
                os.remove(arqWAV)
        log(msg)