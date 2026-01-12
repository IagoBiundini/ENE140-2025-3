from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import cv2
from ultralytics import YOLO
import io
import numpy as np
from dotenv import dotenv_values
import soundfile as sf
import speech_recognition as sr
import tensorflow as tf
import tensorflow_hub as hub
import csv

# Configuração de ambiente
config = dotenv_values(".env")

# NOVO: Motor de Classificação de Som (YAMNet)
class ClassificadorSom:
    def __init__(self):
        print("Carregando YAMNet...")
        # Modelo do TF Hub para classificação de eventos sonoros
        self.model = hub.load('https://tfhub.dev/google/yamnet/1')
        class_map_path = self.model.class_map_path().numpy().decode('utf-8')
        self.class_names = self._ler_labels(class_map_path)

    def _ler_labels(self, path):
        classes = []
        with tf.io.gfile.GFile(path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                classes.append(row['display_name'])
        return classes

    def identificar(self, wav_data):
        # YAMNet exige tensores float32
        scores, _, _ = self.model(wav_data)
        media_scores = tf.reduce_mean(scores, axis=0)
        idx_max = tf.argmax(media_scores)
        return self.class_names[idx_max], media_scores[idx_max].numpy()


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

                for box in result[0].boxes:
                    class_id = int(box.cls)
                    confidence = float(box.conf) * 100
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cv2.rectangle(image_file, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    cv2.putText(image_file, f"{name_class[class_id]} {confidence:.1f}%",
                                (x1, max(y1 - 10, 20)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                    final += f"- {name_class[class_id]}: {confidence:.1f}%\n"

                await self.editar(final)
                sucesso, buffer = cv2.imencode('.jpg', image_file)

                if sucesso:
                    await self.message.reply_photo(photo=buffer.tobytes(), caption="Imagem classificada:")

        except Exception as e:
            print(f"Erro imagem: {e}")
            await self.responder("Erro ao processar imagem.")


class BotAudio(BotTelegram):
    # ADAPTAÇÃO: Agora recebe o motor_som
    def __init__(self, token, update, context, motor_som):
        super().__init__(token, update, context)
        self.motor_som = motor_som

    async def processamento(self):
        # Baixa o áudio enviado pelo usuário
        audio_buffer = io.BytesIO()
        audio_file = await self.update.message.voice.get_file()
        await audio_file.download_to_memory(audio_buffer)
        audio_buffer.seek(0)

        await self.responder("Analisando som...")
        wav_buffer = io.BytesIO()

        try:
            # Leitura via soundfile
            data, samplerate = sf.read(audio_buffer)

            # Ajuste para Mono (YAMNet e Google pedem mono)
            if len(data.shape) > 1:
                data = np.mean(data, axis=1)

            # Classificação YAMNet
            classe, confianca = self.motor_som.identificar(data.astype(np.float32))
            res_final = f"Som identificado: {classe} ({confianca:.1%})\n"

            # Escrita no buffer para Transcrição
            sf.write(wav_buffer, data, samplerate, format='WAV', subtype='PCM_16')
            wav_buffer.seek(0)

            # Só transcreve se houver indício de fala humana
            if "Speech" in classe or "Conversation" in classe or confianca > 0.4:
                await self.editar(res_final + "Transcrevendo fala...")
                recognizer = sr.Recognizer()
                with sr.AudioFile(wav_buffer) as source:
                    audio_data = recognizer.record(source)
                    texto = recognizer.recognize_google(audio_data, language='pt-BR')
                    res_final += f"Transcrição: {texto}"

            await self.editar(res_final)

        except Exception as e:
            await self.editar("Erro ao processar áudio.")
            print(f"Erro: {e}")
        finally:
            audio_buffer.close()
            wav_buffer.close()

# comandos
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot iniciado")

async def help_command(update: Update, context: Update):
    await update.message.reply_text("Envie imagem para YOLO ou áudio para classificação/transcrição.")

async def router_imagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = BotImagem(token, update, context, model)
    await bot.processamento()

async def router_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Passando o motor de som instanciado no main
    bot = BotAudio(token, update, context, motor_som)
    await bot.processamento()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Por favor envie apenas áudios ou imagens.")

if __name__ == "__main__":
    token = config.get('token')
    if not token:
        print("Erro: Token não encontrado.")
        exit()

    model = YOLO("yolov8n.pt")
    motor_som = ClassificadorSom() # Inicialização global dos motores

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(MessageHandler(filters.PHOTO, router_imagem))
    app.add_handler(MessageHandler(filters.VOICE, router_audio))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot iniciado.")
    app.run_polling()