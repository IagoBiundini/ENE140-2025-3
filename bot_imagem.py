import cv2
import numpy as np
from ultralytics import YOLO
from telegram.ext import MessageHandler, filters
from bot_base import BotTelegram
from io import BytesIO

class BotImagem(BotTelegram):
    def __init__(self, token):
        super().__init__(token)
        self.model = YOLO("yolov8n.pt")

        self.app.add_handler(
            MessageHandler(filters.PHOTO, self.processar_imagem)
        )

    async def processar_imagem(self, update, context):
        photo = update.message.photo[-1]
        file = await photo.get_file()
        image_bytes = await file.download_as_bytearray()

        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        results = self.model(img)[0]
        textos = []

        if results.boxes:
            for box in results.boxes:
                conf = float(box.conf[0])
                cls = int(box.cls[0])
                label = self.model.names[cls]

                if conf >= 0.5:
                    textos.append(f"{label} ({conf*100:.1f}%)")
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cv2.rectangle(img, (x1, y1), (x2, y2), (0,255,0), 2)
                    cv2.putText(
                        img, label, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2
                    )

        resposta = (
            "🖼️ Objetos detectados:\n" + "\n".join(textos)
            if textos else "Nenhum objeto detectado."
        )

        _, buffer = cv2.imencode(".jpg", img)
        img_io = BytesIO(buffer.tobytes())
        img_io.name = "resultado.jpg"

        await update.message.reply_text(resposta)
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=img_io
        )


