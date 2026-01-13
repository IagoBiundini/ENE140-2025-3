# Bot Telegram de processamento de áudios e imagens

Este bot analisa imagens (detectando objetos com YOLO) e processa áudios (classificação com YAMNet e Speech Recognition).

## 🚀 Funcionalidades

* **Detecção de Objetos (YOLOv8):** Envie uma foto e o bot retornará a classificação dos objetos presentes na imagem, a imagem desenhada com as caixas (bounding boxes) e a confiança de cada objeto detectado.
* **Classificação de Som (YAMNet):** Identifica o tipo de som (ex: fala humana, animais, música).
* **Transcrição (SpeechRecognition):** Se o som for identificado como fala, o bot transcreve o áudio para texto.

## 📦 Instalação

### 1. Dependências
Certifique-se de ter o Python instalado. Crie um arquivo `requirements.txt` na raiz do projeto com o seguinte conteúdo:

```txt
numpy==1.26.4
opencv-python==4.9.0.80
tensorflow
tensorflow-hub
ultralytics
python-telegram-bot
python-dotenv
soundfile
SpeechRecognition
scipy