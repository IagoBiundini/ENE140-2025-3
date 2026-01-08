import os
import cv2
import numpy as np
from ultralytics import YOLO # Pip install ultralytics
from telegram import Update
from telegram.ext import (Application, CommandHandler, MessageHandler, ContextTypes, filters)

# --- CLASSE MÃE (BASE) ---
class BotTelegram:
    # Guarda as informações básicas e prepara o bot
    def __init__(self, token, nomedobot):
        self.__token = token # Encapsulamento
        self.nomedobot = nomedobot
        
        # Constrói a aplicação
        self.app = Application.builder().token(self.__token).build()

        # Comandos básicos
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("help", self.help))

        # OBS: Removemos o handler de texto genérico daqui para permitir 
        # que as classes filhas decidam como tratar textos ou outros tipos,
        # ou adicionamos ele por último na execução.

    # Responde ao comando /start
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(f"Olá! Sou o {self.nomedobot}. Envie uma imagem para análise.")

    # Responde ao comando /help
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Encaminhe uma imagem e eu direi o que há nela usando Inteligência Artificial.")

    # Método para iniciar o bot (separado do __init__ para permitir herança correta)
    def iniciar(self):
        print(f"Bot {self.nomedobot} iniciado e aguardando mensagens...")
        self.app.run_polling()

# --- CLASSE FILHA (DERIVADA - Foca em Imagens) ---
class BotImagem(BotTelegram):
    def __init__(self, token, nomedobot, model_path='yolov8n.pt'):
        # 1. Chama o construtor da classe mãe (Herança)
        super().__init__(token, nomedobot)
        
        # 2. Carrega o modelo YOLO (Encapsulamento da lógica de IA)
        print("Carregando modelo YOLO...")
        self.model = YOLO(model_path)

        # 3. Adiciona o handler específico para IMAGENS (Polimorfismo/Especialização)
        # O filtro filters.PHOTO garante que só pegue imagens
        self.app.add_handler(MessageHandler(filters.PHOTO, self.analisar_imagem))
        
        # Adiciona handler de texto caso o usuário mande texto em vez de foto
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Por favor, envie uma IMAGEM para eu analisar.")

    # Função Mágica que processa a imagem
    async def analisar_imagem(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Avisa o usuário que está processando
        msg_processando = await update.message.reply_text("Recebi sua imagem! Processando com YOLO...")

        try:
            # --- PASSO A: BAIXAR A IMAGEM DO TELEGRAM ---
            # Pega a foto de maior resolução (-1)
            photo_file = await update.message.photo[-1].get_file()
            
            # Define um caminho temporário para salvar
            caminho_entrada = "temp_img.jpg"
            await photo_file.download_to_drive(caminho_entrada)

            # --- PASSO B: PROCESSAMENTO COM OPENCV E YOLO ---
            # Ler a imagem com OpenCV
            img = cv2.imread(caminho_entrada)

            # Rodar o modelo YOLO
            results = self.model(img)

            # --- PASSO C: GERAR RESULTADOS ---
            # Extrair nomes dos objetos detectados para texto
            deteccoes = []
            for result in results:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    confianca = float(box.conf[0])
                    nome_objeto = self.model.names[class_id]
                    deteccoes.append(f"{nome_objeto} ({confianca:.2f})")

            # Gerar a imagem com os retângulos desenhados (plot)
            # O YOLO retorna um array numpy (RGB), precisamos converter para BGR pro OpenCV salvar certo
            res_plotted = results[0].plot()
            
            caminho_saida = "resultado.jpg"
            cv2.imwrite(caminho_saida, res_plotted)

            # --- PASSO D: ENVIAR RESPOSTA AO USUÁRIO ---
            
            # 1. Enviar Texto
            if deteccoes:
                texto_final = "Objetos detectados:\n" + "\n".join(deteccoes)
            else:
                texto_final = "Não detectei nenhum objeto conhecido."
            
            # Edita a mensagem de "Processando..." com o resultado
            await context.bot.edit_message_text(chat_id=update.effective_chat.id, 
                                                message_id=msg_processando.message_id, 
                                                text=texto_final)

            # 2. Enviar a Imagem Processada
            await update.message.reply_photo(photo=open(caminho_saida, 'rb'))

            # Limpeza de arquivos temporários (Boa prática)
            if os.path.exists(caminho_entrada): os.remove(caminho_entrada)
            if os.path.exists(caminho_saida): os.remove(caminho_saida)

        except Exception as e:
            print(f"Erro ao processar imagem: {e}")
            await update.message.reply_text("Ocorreu um erro ao processar sua imagem.")


# --- EXECUÇÃO PRINCIPAL ---

# Verificação do Token
token = os.getenv("BOT_TOKEN")
if not token:
    # Se não achar a var de ambiente, pode tentar colocar hardcoded para teste rápido (não recomendado p/ git)
    # token = "SEU_TOKEN_AQUI" 
    raise RuntimeError("BOT_TOKEN não definido.")

# Instancia a classe FILHA (BotImagem) em vez da BotTelegram genérica
bot = BotImagem(token, "@EngEletricaBot")

# Inicia o loop de execução
bot.iniciar()
