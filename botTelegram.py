"""
Dependências e configuração do sistema.
Este trecho centraliza as bibliotecas utilizadas pelo bot do Telegram,
abrangendo:
- Integração com a API do Telegram
- Processamento de imagens e anotações visuais
- Execução de inferência com YOLO
- Manipulação de dados em memória
- Carregamento de configurações sensíveis via arquivo .env

As dependências relacionadas a áudio estão incluídas para
extensão multimodal futura do sistema.
"""
import tensorflow as tf
import tensorflow_hub as hub
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import cv2
from ultralytics import YOLO
import io
import numpy as np
from dotenv import dotenv_values
import soundfile as sf
import speech_recognition as sr
import csv
from scipy import signal

#proteção do token utilizando um arquivo .env que será ocultado no github
config = dotenv_values(".env")

class BotTelegram:
    def __init__(self, token, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Inicializa os componentes básicos do bot.

        :param token: Chave de API do bot fornecida pelo BotFather.
        :param update: Objeto que contém todas as informações da interação atual.
        :param context: Gerenciador de contexto do framework python-telegram-bot.
        """
        self.__token = token            # Atributo privado para segurança do token
        self.update = update            # Armazena os dados da atualização recebida
        self.context = context          # Armazena o contexto da execução
        self.message = update.message   # Atalho para acessar a mensagem do usuário

    async def responder(self, texto):
        """
        Envia uma nova mensagem de resposta ao usuário e armazena a
        instância da mensagem enviada para futuras edições.

        :param texto: Conteúdo da mensagem a ser enviada.
        """
        self.msg = await self.message.reply_text(texto)
        
    async def editar(self, texto):
        """
        Modifica o conteúdo de uma mensagem enviada anteriormente pelo bot.
        Utilizado para criar uma interface dinâmica e limpa, evitando excesso de mensagens por cada interação.

        :param texto: Novo conteúdo que substituirá o texto anterior.
        """
        await self.msg.edit_text(texto)

    async def processamento(self):
        """
        Método abstrato planejado para ser sobrescrito em classes filhas.
        Garante que o código sempre chame o método processamento, não importa se for para o áudio ou para o texto.
        """
        pass

class BotImagem(BotTelegram):
    """
    Classe responsável pelo processamento de imagens enviadas ao bot do Telegram.

    Esta classe herda de BotTelegram e adiciona funcionalidades de:
    - Download de imagens enviadas pelo usuário
    - Processamento usando um modelo YOLO
    - Desenho de bounding boxes e labels
    - Retorno da imagem processada ao usuário
    """

    def __init__(self, token, update, context, model):
        """
        Inicializa o bot de processamento de imagens.

        Parâmetros:
        token : str
            Token de autenticação do bot do Telegram.
        update : telegram.Update
            Objeto de atualização recebido do Telegram.
        context : telegram.ext.ContextTypes.DEFAULT_TYPE
            Contexto da aplicação do Telegram.
        model : object
            Modelo YOLO previamente carregado para detecção de objetos.
        """
        super().__init__(token, update, context)
        self.model = model

    async def processamento_imagem(self):
        """
        Processa a imagem enviada pelo usuário no Telegram.

        Etapas do processamento:
        Download da imagem em maior resolução
        Conversão da imagem para formato OpenCV
        Execução do modelo YOLO
        Desenho das bounding boxes e labels
        Envio da imagem processada ao usuário
        """
        try:
            # Baixa a imagem com maior resolução enviada pelo Telegram
            photo_file = await self.message.photo[-1].get_file()

            await self.responder("Processando imagem...")

            # Cria um arquivo temporário em memória (RAM)
            # Ao final do bloco 'with', o buffer é automaticamente fechado
            with io.BytesIO() as out:
                await photo_file.download_to_memory(out)
                out.seek(0)

                # Converte os bytes da imagem para um array NumPy
                file_bytes = np.frombuffer(out.getvalue(), dtype=np.uint8)

                # Decodifica a imagem usando OpenCV
                image_file = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

                # Verifica se a imagem foi carregada corretamente
                if image_file is None:
                    await self.editar("Erro ao carregar a imagem.")
                    return

                # Executa o modelo YOLO na imagem
                result = self.model(image_file)

                # Verifica se algum objeto foi detectado
                if len(result[0].boxes) == 0:
                    await self.editar("Nenhum objeto detectado.")
                    return

                # Dicionário contendo os nomes das classes do modelo
                name_class = result[0].names

                # Texto final que será enviado ao usuário
                final = "Avaliação da imagem:\n"

                # Loop sobre todas as detecções
                for box in result[0].boxes:
                    # ID da classe detectada
                    class_id = int(box.cls)

                    # Confiança da detecção (em porcentagem)
                    confidence = float(box.conf) * 100

                    # Coordenadas da bounding box
                    x1, y1, x2, y2 = map(int, box.xyxy[0])

                    # Desenha o retângulo da bounding box
                    cv2.rectangle(
                        image_file,
                        (x1, y1),
                        (x2, y2),
                        (0, 0, 255),
                        2
                    )

                    # Desenha o texto com nome da classe e confiança
                    cv2.putText(
                        image_file,
                        f"{name_class[class_id]} {confidence:.1f}%",
                        (x1, max(y1 - 10, 20)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 0, 255),
                        2
                    )

                    # Acrescenta o resultado ao texto final
                    final += f"- {name_class[class_id]}: {confidence:.1f}%\n"

                # Atualiza a mensagem com o resumo das detecções
                await self.editar(final)
                await self.responder("...")

                # Codifica a imagem processada para envio
                sucesso, buffer = cv2.imencode('.jpg', image_file)

                if sucesso:
                    await self.editar("Aqui está a imagem com as classificações:")
                    await self.message.reply_photo(photo=buffer.tobytes())
                else:
                    await self.editar("Não foi possível enviar a imagem classificada.")

        except Exception as e:
            # Log de erro para depuração
            print(f"Erro no processamento de imagem: {e}")
            await self.responder("Ocorreu um erro ao processar a imagem.")

class ClassificadorSom:
    """
    Classe responsável por gerenciar o modelo YAMNet para classificação de sons.
    Realiza o carregamento do modelo YAMNet, lê os dados do modelo e realiza o pré-processamento de sinais e inferência.
    """
    
    def __init__(self):
        """
        Inicializa a classe, carrega o modelo YAMNet do TensorFlow Hub e
        mapeia os nomes das classes (labels).
        """
        
        print("Carregando YAMNet...")
        # Carrega o modelo pré-treinado do Google via TF Hub
        self.model = hub.load('https://tfhub.dev/google/yamnet/1')

        # Extrai o caminho do arquivo de classes (.csv) embutido no modelo
        class_map_path = self.model.class_map_path().numpy().decode('utf-8')
        self.class_names = self._ler_labels(class_map_path)

    def _ler_labels(self, path):
        """
        Lê o arquivo CSV que mapeia os IDs do modelo para nomes legíveis.

        :param path: Caminho do arquivo CSV de mapeamento.
        :return: Lista com os nomes das classes ordenadas por índice.
        """
        
        classes = []
        with tf.io.gfile.GFile(path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                classes.append(row['display_name'])
        return classes

    def preparar_audio(self, data, sample_rate_original):
        """
        Normaliza e adapta o áudio de entrada para os requisitos do YAMNet:
        (Mono, 16kHz, Float32).

        :param data: Array de áudio bruto (NumPy).
        :param sample_rate_original: Taxa de amostragem original (ex: 44100Hz).
        :return: Áudio processado pronto para inferência.
        """
        
        # 1. Conversão para Mono: Se o áudio for estéreo (2 canais), calcula a média
        if len(data.shape) > 1:
            data = np.mean(data, axis=1)
            
        # 2. Resampling: O YAMNet exige exatamente 16.000 amostras por segundo
        target_sr = 16000
        if sample_rate_original != target_sr:
            number_of_samples = round(len(data) * float(target_sr) / sample_rate_original)
            data = signal.resample(data, number_of_samples)
            
        # 3. Tipagem: Converte para float32 para compatibilidade com o TensorFlow
        return data.astype(np.float32)

    def identificar(self, wav_data):
        """
        Executa a inferência no áudio e retorna a classe mais provável.

        :param wav_data: Áudio já processado pelo método preparar_audio.
        :return: Tupla contendo (Nome da Classe, Porcentagem de Confiança).
        """
        # Execução do modelo: retorna scores, embeddings e espectrograma
        scores, embeddings, spectrogram = self.model(wav_data)
        
        # Agrega os resultados: O modelo analisa pequenos frames. Aqui calculamos a média de probabilidade do áudio inteiro.
        media_scores = tf.reduce_mean(scores, axis=0)
        
        # Identifica o índice do maior valor de probabilidade
        idx_max = tf.argmax(media_scores)
        confidence = media_scores[idx_max].numpy() * 100
        
        return self.class_names[idx_max], confidence

class BotAudio(BotTelegram):
    """
    Classe responsável por mediar a interação entre o bot do Telegram e as IA's (Classificação de Som e Transcrição).
    Herda as funcionalidades básicas de comunicação da classe BotTelegram.
    """
    
    def __init__(self, token, update, context, classificador_som):
        """
        Inicializa o gerenciador de áudio do bot.

        :param token: Token de autenticação do bot.
        :param update: Objeto que contém os dados da mensagem recebida.
        :param context: Contexto da execução do bot.
        :param classificador_som: Instância carregada da classe ClassificadorSom (YAMNet).
        """
        
        super().__init__(token, update, context)
        self.classificador_som = classificador_som

    async def processamento(self):
        """
        Método principal que coordena o fluxo de processamento:
        1. Download do áudio; 2. Classificação; 3. Transcrição (se necessário).
        """

        # Buffer em memória para evitar escrita em disco, aumentando a velocidade
        audio_buffer = io.BytesIO()

        # Baixa o arquivo de voz enviado pelo usuário diretamente para a memória RAM
        audio_file = await self.update.message.voice.get_file()
        await audio_file.download_to_memory(audio_buffer)
        audio_buffer.seek(0)  # Reseta o ponteiro para o início do arquivo

        await self.responder("Processando audio...")
        
        wav_buffer = io.BytesIO()

        try:
            # Leitura dos dados brutos do buffer usando soundfile
            data, samplerate = sf.read(audio_buffer)

            # Fase 1: Classificação de Som (YAMNet)
            audio_preparado = self.classificador_som.preparar_audio(data, samplerate)
            classe, confianca = self.classificador_som.identificar(audio_preparado)
            res_final = f"Som identificado: {classe} ({confianca:.1f}%)\n"

            # Conversão para formato WAV (PCM_16) em memória para o Reconhecedor de Fala
            sf.write(wav_buffer, data, samplerate, format='WAV', subtype='PCM_16')
            wav_buffer.seek(0)

            # Fase 2: Reconhecimento de Fala (Google Speech Recognition)
            # A transcrição só ocorre se a classe identificada for voz humana.
            if "Speech" in classe or "Conversation" in classe:
                await self.editar(res_final + "\nTranscrevendo fala...")
                
                recognizer = sr.Recognizer()
                with sr.AudioFile(wav_buffer) as source:
                    # Captura os dados de áudio do buffer WAV
                    audio_data = recognizer.record(source)
                    # Envia para a API do Google via SpeechRecognition
                    texto = recognizer.recognize_google(audio_data, language='pt-BR')
                    res_final += f"\nTranscrição: {texto}"
            else:
                res_final += "\nO som enviado não possui fala clara para transcrição."

            # Retorno final para o usuário no Telegram
            await self.editar(res_final)

        except sr.UnknownValueError:
            await self.responder("Não consegui entender o áudio.")
        except Exception as e:
            await self.responder(f"Ocorreu um erro ao tentar processar o áudio.")
            print(f"Erro no processamento: {e}")
        finally:
            # Liberação manual de memória
            audio_buffer.close()
            wav_buffer.close()

# comandos
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot iniciado.\n\nEnvie uma imagem para análise ou um áudio para transcrição.\n\nDigite /help caso haja dúvidas sobre o funcionamento do bot")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Este é um bot de classificação de áudios e imagens.\n\nCaso uma imagem seja enviada, o bot irá avaliar e classificar os objetos presentes na imagem e retornar a imagem com as classificações indicando cada objeto.\n\nCaso um áudio seja enviado, o bot irá o classificar o áudio, que pode ser sons emitidos por animais, se é uma fala humana ou até mesmo se não há nenhum som detectável. Caso o usuário fale algo no áudio, o bot irá transcrever a mensagem enviada em áudio para texto.")

# Roteamento (Factory Pattern)
async def router_imagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = BotImagem(token, update, context, model)
    await bot.processamento()

async def router_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = BotAudio(token, update, context, classificador_som)
    await bot.processamento()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Por favor envie apenas áudios ou imagens.")


if __name__ == "__main__":
    token = config.get('token')

    # ver se o token ta funcionando
    if not token:
        print("Erro: Token não encontrado. Verifique seu arquivo .env")
        exit()

    model = YOLO("yolov8n.pt")

    classificador_som = ClassificadorSom()
    # configuração do app
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))

    app.add_handler(MessageHandler(filters.PHOTO, router_imagem))
    app.add_handler(MessageHandler(filters.VOICE, router_audio))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot iniciado.")
    app.run_polling()
