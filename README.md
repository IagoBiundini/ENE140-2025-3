# Bot Telegram de processamento de áudios e imagens

Este bot analisa imagens (detectando objetos com YOLO) e processa áudios (classificação com YAMNet e Speech Recognition).

## Funcionalidades

* **Detecção de Objetos (YOLOv8):** Envie uma foto e o bot retornará a classificação dos objetos presentes na imagem, a imagem desenhada com as caixas (bounding boxes) e a confiança de cada objeto detectado.
* **Classificação de Som (YAMNet):** Identifica o tipo de som (ex: fala humana, animais, música).
* **Transcrição (SpeechRecognition):** Se o som for identificado como fala, o bot transcreve o áudio para texto.

## Instalação

### 1.  Clone este repositório:

    ```bash
    git clone <url-deste-repositorio>
    cd ENE-2025-3
    

### 2.  (Recomendado) Crie e ative um ambiente virtual:

    ```bash
    python -m venv venv
    source venv/bin/activate  # No Windows: venv\Scripts\activate
    

### 3. Dependências
Certifique-se de ter o Python instalado. Utilize o arquivo `requirements.txt` na raiz do projeto com o seguinte conteúdo:

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


### 4. Instale as dependências

    ```bash
    pip install -r requirements.txt
    ```
