from services.yolo_service import YoloService
from bot_telegram import BotTelegram

class BotImagem(BotTelegram):
    def __init__(self, token):
        super().__init__(token)
        self._yolo = YoloService()

    async def processar_mensagem(self, update, context):
        foto = update.message.photo[-1]
        arquivo = await foto.get_file()
        caminho = f"img_{foto.file_unique_id}.jpg"

        await arquivo.download_to_drive(caminho)

        objetos = self._yolo.detectar_objetos(caminho)

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Objetos detectados: {', '.join(objetos)}"
        )
