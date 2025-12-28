from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import cv2
import os
from dotenv import load_dotenv
from ultralytics import YOLO
from telegram import Update

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

    # Função para executar a parte do yolo, sendo "image_path" a imagem que quer-se ler
    async def processamento(self):

        #baixa a imagem com maior resuluão enviada pelo telegram
        photo_file = await self.message.photo[-1].get_file()
        #criar um arquivo temporário para extrair o caminho da imagem com o id da mensagem
        image_path = f"temp_{self.message.id}.jpg"
        #baixa a imagem no computador
        await photo_file.download_to_drive(image_path)

        # Está lendo a iamgem que é enviada ao yolo
        image = cv2.imread(image_path)

        if image is None:
            await self.responder("Erro ao carregar a imagem.")
            return 

        # Está executando o yolo
        result = self.model(image)

        if len(result[0].boxes) == 0:
            await self.responder("Nenhum objeto detectado.")
            return  # Fundamental compreender que  o yolo pré treinado possui limitações

        # Nomes das classes já presentes no yolo
        name_class = result[0].names

        final = "Avaliação da imagem:\n"

        # Esse loop passa por cada parte do yolo já treinasdo e mostra o resultado da análise
        for box in result[0].boxes:
            class_id = int(box.cls)
            confidence = float(box.conf) * 100


            # Desenvolvendo o comportamento da bounding box
            x1, y1, x2, y2 = map(int, box.xyxy[0])   # bounding box

            # desenha a bounding box (vermelha)
            cv2.rectangle(
            image,
                (x1, y1),
                (x2, y2),
                (0, 0, 255), # vermelho (BGR)
                2
            )

            # Desenha o texto na imagem
            cv2.putText(
            image,
                f"{name_class[class_id]} {confidence:.1f}%",
                (x1, max(y1 - 10, 20)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 0, 255),
                2
            )

        output_imagepath = f"resultado_{self.message.id}.jpg"
        cv2.imwrite(output_imagepath, image)

        await self.responder(final)
        await self.message.reply_photo(photo = open(output_imagepath, 'rb'))

        #limpar o arquivo
        os.remove(image_path)
        os.remove(output_imagepath)

class BotAudio(BotTelegram):
    def __init__(self, token, update, context):
        super().__init__(token, update, context)

    async def processamento(self):
        await self.responder("Áudio recebido! (Transcrição em desenvolvimento)")
    #interpretar a mensagem como um audio

if __name__ == "__main__":
    token = os.getenv('token')
    model = YOLO("yolov8n.pt")

    #comandos /start e /help
    async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("bot iniciado")

    async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("envie uma imagem para que o bot descreva os objetos contidos nela ou um áudio para que o bot o transcreva em forma de texto")
    
    #identificar se a mensagem é um áudio ou imagem e instancia a mensagem para cada respectiva classe através de polimorfismo
    async def router_imagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
        bot = BotImagem(token, update, context, model)
        await bot.processamento()

    async def router_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
        bot = BotAudio(token, update, context)
        await bot.processamento()

    #se o usuário enviar uma mensagem
    async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("mensagens de texto não são compreendidas pelo bot. por favor envie apenas audios ou imagens")
    
    #em caso de erro
    #async def error(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        #print(f'Update {update} caused error {context.error}')

    app = Application.builder().token(token).build()
    
    #comandos
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    #mensagens
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
        
    #quando houver algum erro
    #app.add_error_handler(error)

    #imagem e audio
    app.add_handler(MessageHandler(filters.PHOTO, router_imagem))
    app.add_handler(MessageHandler(filters.VOICE, router_audio))

    #iniciar o bot
    app.run_polling()
