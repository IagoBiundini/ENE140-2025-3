# Bot Telegram de processamento de áudios e imagens

Este bot analisa imagens (detectando objetos com YOLO) e processa áudios (classificação com YAMNet e Speech Recognition).

## Funcionalidades

* **Detecção de Objetos (YOLOv8):** Envie uma foto e o bot retornará a classificação dos objetos presentes na imagem, a imagem desenhada com as caixas (bounding boxes) e a confiança de cada objeto detectado.
* **Classificação de Som (YAMNet):** Identifica o tipo de som (ex: fala humana, animais, música).
* **Transcrição (SpeechRecognition):** Se o som for identificado como fala, o bot transcreve o áudio para texto.

## Instalação

Para executar o programa, você precisará do Python 3 e das bibliotecas listadas no arquivo `requirements.txt`. O processo recomendado é:

1.  **Clone o repositório:**

    ```bash
    git clone <url-deste-repositorio>
    cd process_timeseries
    ```

2.  **Crie um ambiente virtual (recomendado):**

    ```bash
    python -m venv venv
    source venv/bin/activate  # No Windows: venv\Scripts\activate
    ```

3.  **Instale as dependências:**

    ```bash
    pip install -r requirements.txt
    ```

4. **Configuração de token**

    ```bash
    token=seutoken
    ```
