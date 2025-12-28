from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import cv2
import os
from dotenv import load_dotenv
from ultralytics import YOLO

load_dotenv()

class BotTelegram:
    def __init__(self, token, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.__token = token
        self.update = update
        self.context = context
        self.message = update.message

    async def responder(self, texto):
        await self.message.reply_text(texto)

class BotImagem(BotTelegram):
    def __init__(self, token, update, context, model):
        super().__init__(token, update, context)
        self.model = model

    async def processamento(self):
        try:
            await self.responder("Processando imagem...")
            
            # baixa a imagem com maior resolução enviada pelo telegram
            photo_file = await self.message.photo[-1].get_file()
            
            # criar um arquivo temporário
            image_path = f"temp_{self.message.id}.jpg"
            await photo_file.download_to_drive(image_path)

            # ler a imagem
            image = cv2.imread(image_path)

            if image is None:
                await self.responder("Erro ao carregar a imagem.")
                os.remove(image_path)
                return 

            # executa o YOLO 
            result = self.model(image)

            if len(result[0].boxes) == 0:
                await self.responder("Nenhum objeto detectado.")
                os.remove(image_path)
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
                cv2.rectangle(image, (x1, y1), (x2, y2), (0, 0, 255), 2)

                # Desenha o texto
                cv2.putText(
                    image,
                    f"{name_class[class_id]} {confidence:.1f}%",
                    (x1, max(y1 - 10, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 0, 255),
                    2
                )
                
                final += f"- {name_class[class_id]}: {confidence:.1f}%\n"

            output_imagepath = f"resultado_{self.message.id}.jpg"
            cv2.imwrite(output_imagepath, image)

            await self.responder(final)
            await self.message.reply_photo(photo=open(output_imagepath, 'rb'))

            # Limpar os arquivos
            os.remove(image_path)
            os.remove(output_imagepath)

        except Exception as e:
            print(f"Erro no processamento de imagem: {e}")
            await self.responder("Ocorreu um erro ao processar a imagem.")

class BotAudio(BotTelegram):
    def __init__(self, token, update, context):
        super().__init__(token, update, context)

    async def processamento(self):
        await self.responder("Áudio recebido! (Transcrição em desenvolvimento)")
        # Lógica futura: Pydub + SpeechRecognition

if __name__ == "__main__":
    token = os.getenv('token') 
   
    # ver se o token ta funcionando
    if not token:
        print("Erro: Token não encontrado. Verifique seu arquivo .env")
        exit()

    model = YOLO("yolov8n.pt")

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
    
    # configuração do app
    app = Application.builder().token(token).build()
    
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    
    app.add_handler(MessageHandler(filters.PHOTO, router_imagem))
    app.add_handler(MessageHandler(filters.VOICE, router_audio))
    
    # Ajuste: Filtra texto APENAS se não for comando (ver isso aqui)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("bot iniciado")
    app.run_polling()