from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import cv2
from ultralytics import YOLO
import io
import numpy as np
from dotenv import dotenv_values
import soundfile as sf
import speech_recognition as sr

config = dotenv_values(".env")

class BotTelegram:
    def __init__(self, token, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.__token = token
        self.update = update
        self.context = context
        self.message = update.message

    #Serve para facilitar o envio de mensagens
    async def responder(self, texto):
        self.msg = await self.message.reply_text(texto)
    #Serve para editar a mensagem anteriormente enviada e dar dinâmismo à conversa
    async def editar(self, texto):
        await self.msg.edit_text(texto)

    async def processamento(self):
        pass

class BotImagem(BotTelegram):
    def __init__(self, token, update, context, model):
        super().__init__(token, update, context)
        self.model = model

    async def processamento(self):
        try:
            # baixa a imagem com maior resolução enviada pelo telegram
            photo_file = await self.message.photo[-1].get_file()
            
            await self.responder("Processando imagem...")

            # criar um arquivo na RAM. Ao fim do with, o arquivo será fechado
            with io.BytesIO() as out:
                await photo_file.download_to_memory(out)
                out.seek(0)
                file_bytes = np.frombuffer(out.getvalue(), dtype=np.uint8)
                image_file = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

                if image_file is None:
                    await self.editar("Erro ao carregar a imagem.")
                    return

                # executa o YOLO
                result = self.model(image_file)

                if len(result[0].boxes) == 0:
                    await self.editar("Nenhum objeto detectado.")
                    return

                # nomes das classes
                name_class = result[0].names
                final = "Avaliação da imagem:\n"

                # loop das detecções
                for box in result[0].boxes:
                    class_id = int(box.cls)
                    confidence = float(box.conf) * 100

                    # Bounding box
                    x1, y1, x2, y2 = map(int, box.xyxy[0])

                    # Desenha o retângulo
                    cv2.rectangle(image_file, (x1, y1), (x2, y2), (0, 0, 255), 2)

                    # Desenha o texto
                    cv2.putText(
                        image_file,
                        f"{name_class[class_id]} {confidence:.1f}%",
                        (x1, max(y1 - 10, 20)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 0, 255),
                        2
                    )

                    final += f"- {name_class[class_id]}: {confidence:.1f}%\n"
                
                await self.editar(final)
                await self.responder("...")
                
                sucesso, buffer = cv2.imencode('.jpg', image_file)

                if sucesso:
                    await self.editar("Aqui está a imagem com as classificações:")
                    await self.message.reply_photo(photo=buffer.tobytes())
                else:
                    await self.editar("Não foi possível enviar a imagem classificada.")

        except Exception as e:
            print(f"Erro no processamento de imagem: {e}")
            await self.responder("Ocorreu um erro ao processar a imagem.")


class BotAudio(BotTelegram):
    def __init__(self, token, update, context):
        super().__init__(token, update, context)

    async def processamento(self):
        #Baixa os arquivos do Telegram para o Buffer (para memória RAM)
        audio_buffer = io.BytesIO()

        audio_file = await self.update.message.voice.get_file()
        await audio_file.download_to_memory(audio_buffer)
        audio_buffer.seek(0)  # Volta o ponteiro para o início do buffer

        await self.responder("Processando audio...")
        #faz as operações em memória RAM
        wav_buffer = io.BytesIO()

        try:
            # converte usando soundfile 
            data, samplerate = sf.read(audio_buffer)

            #escreve no buffer WAV, 'PCM_16' é o formato ideal para escrever em buffer
            sf.write(wav_buffer, data, samplerate, format='WAV', subtype='PCM_16')

            #prepara o WAV para leitura
            wav_buffer.seek(0)

            # 3. Reconhecimento de Fala
            recognizer = sr.Recognizer()
            with sr.AudioFile(wav_buffer) as source:
                audio_data = recognizer.record(source)
                # Usando Google (Online)
                texto = recognizer.recognize_google(audio_data, language='pt-BR')

            await self.editar(f"Transcrição:\n\n{texto}")

        except sr.UnknownValueError:
            await self.editar("Não consegui entender o áudio.")
        except Exception as e:
            await self.editar(f"Ocorreu um erro ao tentar processar o áudio.")
            print(f"Erro no processamento: {e}")
        finally:
            #Fecha os buffers
            audio_buffer.close()
            wav_buffer.close()

# comandos
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot iniciado")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Envie uma imagem para análise ou um áudio para transcrição.")

# Roteamento (Factory Pattern)
async def router_imagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = BotImagem(token, update, context, model)
    await bot.processamento()

async def router_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = BotAudio(token, update, context)
    await bot.processamento()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Por favor envie apenas áudios ou imagens.")


if __name__ == "__main__":
    token = config.get('token')

    # ver se o token ta funcionando
    if not token:
        print("Erro: Token não encontrado. Verifique seu arquivo .env")
        exit()

    model = YOLO("yolov8n.pt")

    # configuração do app
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))

    app.add_handler(MessageHandler(filters.PHOTO, router_imagem))
    app.add_handler(MessageHandler(filters.VOICE, router_audio))

    # Ajuste: Filtra texto APENAS se não for comando (ver isso aqui)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot iniciado.")
    app.run_polling()
