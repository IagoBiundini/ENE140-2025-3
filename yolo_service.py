# services/yolo_service.py
from ultralytics import YOLO
import os

class YoloService:
    def __init__(self):
        self._model = YOLO("yolov8n.pt")

    def detectar_objetos(self, image_path: str) -> list:
        if not os.path.exists(image_path):
            return ["Imagem não encontrada"]

        results = self._model.predict(
            source=image_path,
            save=False
        )

        objetos_detectados = []

        for r in results:
            for cls in r.boxes.cls:
                nome = self._model.names[int(cls)]
                objetos_detectados.append(nome)

        return list(set(objetos_detectados))
