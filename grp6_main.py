# -*- coding: utf-8 -*-
# main.py

import os
import sys
import logging
import json
import wave
import tempfile
import subprocess
import numpy as np
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()
TOKEN = os.getenv("TOKEN_TELEGRAM")
if not TOKEN:
    raise ValueError("TOKEN_TELEGRAM não encontrado no arquivo .env")

# Importações do Telegram
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters
)

# Importações do Vosk (áudio)
from vosk import Model, KaldiRecognizer

# Importações do YOLO (imagem)
from ultralytics import YOLO

# Adiciona o diretório atual aos módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importa classes do projeto
from grp6_bot import BotTelegram
from grp6_audio import BotAudio
from grp6_imagem import BotImagem


class BotFinal(BotImagem, BotAudio):
    def __init__(self, modelo):
        super().__init__()
        self._modelo = modelo

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Inicializa modelo YOLO
    modelo_path = "yolov8n.pt"  # ou "best.pt" se você tiver o modelo treinado
    modelo = YOLO(modelo_path)

    # Cria instância do bot final
    bot = BotFinal(modelo)

    # Roda o bot
    bot.run()
