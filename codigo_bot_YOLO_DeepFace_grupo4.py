import deepface
import os
import cv2
import numpy as np
from ultralytics import YOLO 
from deepface import DeepFace 
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters)

# --- CLASSE MÃE (BASE) ---
class BotTelegram:
    def __init__(self, token, nomedobot):
        self.__token = token
        self.nomedobot = nomedobot
        self.app = Application.builder().token(self.__token).build()
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("help", self.help))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(f"Olá! Sou o {self.nomedobot}. Envie uma foto de rosto para começar.")

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Envie uma imagem e escolha: YOLO (objetos), Inverter (edição) ou Idade (facial).")

    def iniciar(self):
        print(f"Bot {self.nomedobot} iniciado...")
        self.app.run_polling()

# --- CLASSE FILHA (DERIVADA) ---
class BotImagem(BotTelegram):
    def __init__(self, token, nomedobot, model_path='yolov8n.pt'):
        super().__init__(token, nomedobot)
        print("Carregando modelo YOLO...")
        self.model = YOLO(model_path)

        self.app.add_handler(MessageHandler(filters.PHOTO, self.receber_imagem))
        self.app.add_handler(CallbackQueryHandler(self.botao_pressionado))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Por favor, envie uma IMAGEM primeiro.")

    # --- PASSO 1: Recebe a imagem e mostra 3 botões ---
    async def receber_imagem(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        caminho_arquivo = f"temp_{user_id}.jpg"
        
        photo_file = await update.message.photo[-1].get_file()
        await photo_file.download_to_drive(caminho_arquivo)
        
        context.user_data['caminho_imagem'] = caminho_arquivo

        # Configuração dos Botões
        teclado = [
            [InlineKeyboardButton("🔍 Analisar Objetos (YOLO)", callback_data='analisar')],
            [InlineKeyboardButton("🎂 Estimar Idade (DeepFace)", callback_data='idade')], # <--- NOVO BOTÃO
            [InlineKeyboardButton("🔄 Inverter Imagem", callback_data='inverter')]
        ]
        reply_markup = InlineKeyboardMarkup(teclado)

        await update.message.reply_text(
            "O que você gostaria de fazer com esta imagem?", 
            reply_markup=reply_markup
        )

    # --- PASSO 2: Trata o clique ---
    async def botao_pressionado(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        opcao = query.data
        caminho = context.user_data.get('caminho_imagem')

        if not caminho or not os.path.exists(caminho):
            await query.edit_message_text("Erro: Imagem expirou. Envie novamente.")
            return

        await query.edit_message_text(f"Opção: {opcao.upper()}. Processando... (isso pode levar alguns segundos)")

        try:
            if opcao == 'analisar':
                await self.executar_analise_yolo(update, context, caminho)
            elif opcao == 'inverter':
                await self.executar_inversao_opencv(update, context, caminho)
            elif opcao == 'idade':
                await self.executar_estimativa_idade(update, context, caminho) # <--- NOVA CHAMADA

        except Exception as e:
            print(f"Erro: {e}")
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Erro interno: {e}")
        finally:
            # Só deleta se já tiver terminado tudo. 
            # Dica: Em apps reais, deletamos com um timer, mas aqui deletamos direto
            if os.path.exists(caminho): os.remove(caminho)

    # --- LÓGICA 1: YOLO ---
    async def executar_analise_yolo(self, update, context, caminho):
        img = cv2.imread(caminho)
        results = self.model(img)
        res_plotted = results[0].plot()
        
        caminho_saida = "resultado_yolo.jpg"
        cv2.imwrite(caminho_saida, res_plotted)
        
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(caminho_saida, 'rb'))
        if os.path.exists(caminho_saida): os.remove(caminho_saida)

    # --- LÓGICA 2: INVERSÃO ---
    async def executar_inversao_opencv(self, update, context, caminho):
        img = cv2.imread(caminho)
        img_inv = cv2.flip(img, 1)
        caminho_saida = "resultado_invertido.jpg"
        cv2.imwrite(caminho_saida, img_inv)
        
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(caminho_saida, 'rb'))
        if os.path.exists(caminho_saida): os.remove(caminho_saida)

    # --- LÓGICA 3: DEEPFACE (IDADE) ---
    async def executar_estimativa_idade(self, update, context, caminho_imagem):
        try:
            # DeepFace faz a mágica. actions=['age'] foca na idade.
            # enforce_detection=False evita crash se não achar rosto (mas o resultado pode ser ruim)
            print("Rodando DeepFace...")
            analise = DeepFace.analyze(img_path=caminho_imagem, actions=['age', 'gender'], enforce_detection=False)
            
            # O resultado é uma lista (pode ter vários rostos)
            # Vamos pegar o primeiro rosto encontrado
            dados_rosto = analise[0]
            idade = dados_rosto['age']
            genero = dados_rosto['dominant_gender']
            
            # Desenhar na imagem usando OpenCV
            img = cv2.imread(caminho_imagem)
            
            # Pega a região do rosto para desenhar o quadrado
            region = dados_rosto['region']
            x, y, w, h = region['x'], region['y'], region['w'], region['h']
            
            # Desenha retângulo verde
            cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
            # Escreve a idade
            texto = f"{genero}, ~{idade} anos"
            cv2.putText(img, texto, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            
            caminho_saida = "resultado_idade.jpg"
            cv2.imwrite(caminho_saida, img)
            
            msg = f"Detectei um rosto! Estimativa: {texto}"
            await context.bot.send_message(chat_id=update.effective_chat.id, text=msg)
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(caminho_saida, 'rb'))
            
            if os.path.exists(caminho_saida): os.remove(caminho_saida)

        except Exception as e:
            print(f"Erro DeepFace: {e}")
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Não consegui detectar um rosto humano claro nesta imagem.")

# --- EXECUÇÃO ---
token = os.getenv("BOT_TOKEN")
if not token: raise RuntimeError("BOT_TOKEN não definido. Defina a variável de ambiente BOT_TOKEN antes de executar o script.")
bot = BotImagem(token, "@trabalho_telegram_bot")
bot.iniciar()
