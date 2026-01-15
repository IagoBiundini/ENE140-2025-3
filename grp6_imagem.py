# -*- coding: utf-8 -*-
# grp6_imagem.py

import os
import tempfile
import numpy as np
from telegram import Update
from telegram.ext import ContextTypes
from ultralytics import YOLO

from grp6_bot import BotTelegram


# Traduções de todas as classes detectáveis
TRADUCOES = {
    "person": "pessoa",
    "bicycle": "bicicleta",
    "car": "carro",
    "motorcycle": "moto",
    "airplane": "avião",
    "bus": "ônibus",
    "train": "trem",
    "truck": "caminhão",
    "boat": "barco",
    "traffic light": "semáforo",
    "fire hydrant": "hidrante",
    "stop sign": "placa de pare",
    "parking meter": "parquímetro",
    "bench": "banco",
    "bird": "pássaro",
    "cat": "gato",
    "dog": "cachorro",
    "horse": "cavalo",
    "sheep": "ovelha",
    "cow": "vaca",
    "elephant": "elefante",
    "bear": "urso",
    "zebra": "zebra",
    "giraffe": "girafa",
    "backpack": "mochila",
    "umbrella": "guarda-chuva",
    "handbag": "bolsa",
    "tie": "gravata",
    "suitcase": "mala",
    "frisbee": "frisbee",
    "skis": "esquis",
    "snowboard": "snowboard",
    "sports ball": "bola esportiva",
    "kite": "pipa",
    "baseball bat": "taco de beisebol",
    "baseball glove": "luva de beisebol",
    "skateboard": "skate",
    "surfboard": "prancha de surfe",
    "tennis racket": "raquete de tênis",
    "bottle": "garrafa",
    "wine glass": "taça de vinho",
    "cup": "copo",
    "fork": "garfo",
    "knife": "faca",
    "spoon": "colher",
    "bowl": "tigela",
    "banana": "banana",
    "apple": "maçã",
    "sandwich": "sanduíche",
    "orange": "laranja",
    "broccoli": "brócolis",
    "carrot": "cenoura",
    "hot dog": "cachorro-quente",
    "pizza": "pizza",
    "donut": "rosquinha",
    "cake": "bolo",
    "chair": "cadeira",
    "couch": "sofá",
    "potted plant": "planta em vaso",
    "bed": "cama",
    "dining table": "mesa de jantar",
    "toilet": "vaso sanitário",
    "tv": "televisão",
    "laptop": "notebook",
    "mouse": "mouse",
    "remote": "controle remoto",
    "keyboard": "teclado",
    "cell phone": "celular",
    "microwave": "micro-ondas",
    "oven": "forno",
    "toaster": "torradeira",
    "sink": "pia",
    "refrigerator": "geladeira",
    "book": "livro",
    "clock": "relógio",
    "vase": "vaso",
    "scissors": "tesoura",
    "teddy bear": "urso de pelúcia",
    "hair drier": "secador de cabelo",
    "toothbrush": "escova de dentes",
}


def analise_estatistica_yolo(deteccoes):
    """
    Agrupa detecções por classe e retorna mediana de confiança e quantidade de amostras.
    """
    agrupado = {}
    for d in deteccoes:
        agrupado.setdefault(d["classe"], []).append(d["conf"])

    resultado = []
    for classe, confs in agrupado.items():
        confs = np.array(confs)
        q1 = np.percentile(confs, 25)
        q3 = np.percentile(confs, 75)
        iqr = q3 - q1
        confs_validas = confs[(confs >= q1 - 1.5 * iqr) & (confs <= q3 + 1.5 * iqr)]
        resultado.append({
            "classe": classe,
            "confianca": float(np.median(confs_validas)),
            "amostras": len(confs_validas)
        })

    return resultado


class BotImagem(BotTelegram):
    def __init__(self):
        super().__init__()
        # O modelo YOLO deve ser passado externamente para o bot
        # self._modelo = YOLO("yolov8n.pt") # Exemplo, mas não ativar aqui

    async def tratar_imagem(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message or not update.message.photo:
            return

        status = await update.message.reply_text(
            "Imagem recebida!\nIniciando análise..."
        )

        # Pega a maior resolução da imagem enviada
        foto = await update.message.photo[-1].get_file()

        # Salva temporariamente local
        temp_img = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg").name
        await foto.download_to_drive(temp_img)


        # Executa o YOLO
        resultados = self._modelo.predict(
            source=temp_img,
            conf=0.15,
            verbose=False
        )

        # Remove arquivo temporário
        os.remove(temp_img)

        # Coleta detecções
        deteccoes = []
        for r in resultados:
            for box in r.boxes:
                classe_en = r.names[int(box.cls)]
                classe_pt = TRADUCOES.get(classe_en, classe_en)
                deteccoes.append({
                    "classe": classe_pt,
                    "conf": float(box.conf)
                })

        if not deteccoes:
            await status.edit_text(
                "Poxa, não consegui entender o que está na sua imagem :(\n"
                "Que tal me mandar de outro ângulo?"
            )
            return

        # Análise estatística
        resultado_final = analise_estatistica_yolo(deteccoes)

        # Resposta final
        resposta = "Show! O que eu vejo na sua imagem se chama...\n\n"
        for d in resultado_final:
            resposta += (
                f"{d['classe'].capitalize()}! Digo isso com "
                f"{d['confianca']:.1%} de confiança!\n"
            )

        await status.edit_text(resposta)
