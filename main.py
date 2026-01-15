from bot_telegram import BotTelegram

"Aqui será rodado o código - Tenha a chave de acesso do bot Telegram em mãos"

#token = input("Digite seu token (Chave de acesso feito no BOTFather)")
#TOKEN = token

TOKEN = '7982411670:AAFIo5hA8evpJy6bDTTrwrwGjb5oy5fy7Bg'
bot_instance = BotTelegram(chave_api=TOKEN)
bot_instance.run()