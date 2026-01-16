# bot_imagem.py

import os
import cv2
from collections import Counter
from ultralytics import YOLO

from bot_telegram import BotTelegram

from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from telegram.ext import (
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters
)


class BotImagem(BotTelegram):
    """
    Bot especializado em detecção de objetos com YOLO
    """

    def __init__(self, app, modelo: str):
        super().__init__(app)
        self._modelo = YOLO(modelo)
        self._cache = {}

    # --------------------------------------------------
    # Registra handlers do bot de imagem
    # --------------------------------------------------
    def registrar(self):

        # Recebe imagens
        self.app.add_handler(
            MessageHandler(filters.PHOTO, self.processar_mensagem)
        )

        # Botões da análise (objetos, contagem, imagem)
        self.app.add_handler(
            CallbackQueryHandler(
                self.tratar_botoes_analise,
                pattern="^(lista|contagem|imagem)_\\d+$"
            )
        )

        # Botões: enviar outra imagem?
        self.app.add_handler(
            CallbackQueryHandler(
                self.tratar_botoes_nova_imagem,
                pattern="^imagem_(sim|nao)$"
            )
        )

    # --------------------------------------------------
    # Processa imagem
    # --------------------------------------------------
    async def processar_mensagem(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id

        foto = update.message.photo[-1]
        arquivo = await foto.get_file()

        msg_id = update.message.message_id
        caminho_img = f"img_{msg_id}.jpg"
        await arquivo.download_to_drive(caminho_img)

        resultados = self._modelo(caminho_img, conf=0.4)

        objetos = []
        for r in resultados:
            for cls in r.boxes.cls:
                objetos.append(self._modelo.names[int(cls)])

        self._cache[msg_id] = {
            "objetos": objetos,
            "resultados": resultados,
            "arquivo": caminho_img
        }

        teclado = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📦 Objetos", callback_data=f"lista_{msg_id}"),
                InlineKeyboardButton("🔢 Quantidade", callback_data=f"contagem_{msg_id}")
            ],
            [
                InlineKeyboardButton("🖼️ Imagem anotada", callback_data=f"imagem_{msg_id}")
            ]
        ])

        await update.message.reply_text(
            "✅ Detecção concluída! Escolha uma opção:",
            reply_markup=teclado
        )

        # 🔒 ENCERRA O CICLO DA IMAGEM
        if chat_id in self.chat_liberado:
            self.chat_liberado.remove(chat_id)

    # --------------------------------------------------
    # Trata botões da análise
    # --------------------------------------------------
    async def tratar_botoes_analise(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        acao, msg_id = query.data.split("_")
        msg_id = int(msg_id)

        dados = self._cache.get(msg_id)
        if not dados:
            await query.edit_message_text("❌ Dados não encontrados.")
            return

        if acao == "lista":
            objetos = set(dados["objetos"])
            texto = "📦 Objetos detectados:\n" + "\n".join(objetos)
            await query.edit_message_text(texto)

        elif acao == "contagem":
            contagem = Counter(dados["objetos"])
            texto = "🔢 Quantidade por classe:\n"
            for obj, qtd in contagem.items():
                texto += f"{obj}: {qtd}\n"
            await query.edit_message_text(texto)

        elif acao == "imagem":
            img_anotada = dados["resultados"][0].plot()
            caminho_saida = f"annot_{msg_id}.jpg"

            cv2.imwrite(caminho_saida, img_anotada)

            await query.message.reply_photo(
                photo=open(caminho_saida, "rb"),
                caption="🖼️ Imagem com detecções YOLO"
            )

            os.remove(caminho_saida)

        # 👇 Após qualquer ação, pergunta se quer outra imagem
        teclado = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "📷 Enviar outra imagem",
                    callback_data="imagem_sim"
                ),
                InlineKeyboardButton(
                    "❌ Encerrar",
                    callback_data="imagem_nao"
                )
            ]
        ])

        await query.message.reply_text(
            "Deseja enviar outra imagem?",
            reply_markup=teclado
        )

    # --------------------------------------------------
    # Trata resposta: enviar outra imagem?
    # --------------------------------------------------
    async def tratar_botoes_nova_imagem(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        chat_id = query.message.chat_id

        if query.data == "imagem_sim":
            # 🔓 LIBERA nova imagem
            self.chat_liberado.add(chat_id)
            await query.message.reply_text(
                "📷 Pode enviar a próxima imagem."
            )

        elif query.data == "imagem_nao":
            await query.message.reply_text(
                "✔️ Tudo certo.\nQuando quiser, digite /start."
            )
