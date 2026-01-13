import cv2
import numpy as np
import torch
import logging
from ultralytics import YOLO
from telegram.ext import MessageHandler, filters
from bot_base import BotTelegram
from io import BytesIO
from dataclasses import dataclass

#CONFIGURAÇÃO DE LOG 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#DTO DE DETECÇÃO
@dataclass
class Deteccao:
    label: str
    confianca: float
    bbox: tuple  # (x1, y1, x2, y2)

# BOT DE IMAGEM 
class BotImagem(BotTelegram):

    def __init__(self, token):
        super().__init__(token)

        # Modelo YOLO
        self.model = YOLO("yolov8n.pt")

        # Configurações
        self.conf_min = 0.5
        self.imgsz = 640
        self.max_img_size = 1280
        self.cor_box = (0, 255, 0)
        self.espessura_box = 2

        # Handler de imagens
        self.app.add_handler(
            MessageHandler(filters.PHOTO, self.processar_imagem)
        )

    #PIPELINE PRINCIPAL
    async def processar_imagem(self, update, context):
        try:
            img = await self._baixar_imagem(update)

            if img is None:
                await update.message.reply_text("Imagem inválida.")
                return

            img = self._redimensionar_imagem(img)

            deteccoes = self._detectar_objetos(img)

            self._desenhar_deteccoes(img, deteccoes)

            resposta = self._montar_resposta(deteccoes)

            await update.message.reply_text(resposta)
            await self._enviar_imagem(update, context, img)

        except Exception as e:
            logger.error("Erro ao processar imagem", exc_info=True)
            await update.message.reply_text(
                "Ocorreu um erro ao processar a imagem."
            )

    #FUNÇÕES AUXILIARES 
    async def _baixar_imagem(self, update):
        photo = update.message.photo[-1]
        file = await photo.get_file()
        image_bytes = await file.download_as_bytearray()

        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        return img

    def _redimensionar_imagem(self, img):
        h, w = img.shape[:2]
        maior_dim = max(h, w)

        if maior_dim > self.max_img_size:
            escala = self.max_img_size / maior_dim
            img = cv2.resize(img, None, fx=escala, fy=escala)

        return img

    def _detectar_objetos(self, img):
        deteccoes = []

        with torch.no_grad():
            results = self.model(
                img,
                imgsz=self.imgsz,
                conf=self.conf_min,
                stream=False
            )[0]

        if results.boxes is None or len(results.boxes) == 0:
            return deteccoes

        for box in results.boxes:
            conf = float(box.conf[0])
            cls = int(box.cls[0])
            label = self.model.names[cls]
            x1, y1, x2, y2 = map(int, box.xyxy[0])

            deteccoes.append(
                Deteccao(
                    label=label,
                    confianca=conf,
                    bbox=(x1, y1, x2, y2)
                )
            )

        return deteccoes

    def _desenhar_deteccoes(self, img, deteccoes):
        for det in deteccoes:
            x1, y1, x2, y2 = det.bbox
            texto = f"{det.label} {det.confianca*100:.1f}%"

            cv2.rectangle(
                img,
                (x1, y1),
                (x2, y2),
                self.cor_box,
                self.espessura_box
            )

            cv2.putText(
                img,
                texto,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                self.cor_box,
                2
            )

    def _montar_resposta(self, deteccoes):
        if not deteccoes:
            return "Nenhum objeto detectado."

        linhas = ["Objetos detectados:"]
        for det in deteccoes:
            linhas.append(
                f"- {det.label} ({det.confianca*100:.1f}%)"
            )

        return "\n".join(linhas)

    async def _enviar_imagem(self, update, context, img):
        _, buffer = cv2.imencode(".jpg", img)
        img_io = BytesIO(buffer.tobytes())
        img_io.name = "resultado.jpg"

        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=img_io
        )

