### Telegram Bot - Grupo 8

### ⚠️ Importante
Para que o reconhecimento de áudio funcione corretamente, **é obrigatório baixar manualmente a pasta de modelos de idiomas** antes de executar o bot.

---

## 📥 Download dos modelos

Faça o download da pasta completa contendo todos os idiomas no link abaixo:

🔗 **[Link para download dos modelos de idioma](https://drive.google.com/drive/folders/1Mj0GWLwxiX2pL9ztVYac4tP52PGdjOkf?usp=drive_link)** 

A pasta 'idiomas' deverá ser colocada no mesmo diretório que os demais arquivos deste repositório e extraída, a fim de que ```bot_audio.py``` seja capaz de encontrar o caminho da pasta.

❗❗❗ **A PASTA A SER BAIXADA É A 'idiomas', E NÃO A PASTA COM O NOME DO IDIOMA, POR EXMEPLO 'portugues', 'ingles' ou 'espanhol'** ❗❗❗

Assim deve ser a organização de seu diretório:

```
idiomas/
├── portugues/
│   ├── am/
│   ├── conf/
│   ├── graph/
│   ├── ivector/
│   └── model.conf
├── ingles/
├── espanhol/
├── frances/
├── alemao/
├── russo/
├── arabe/
├── chines/
└── hindi/
main.py
bot_telegram.py
bot_imagem.py
bot_audio.py
yamnet_classes_map.csv
yolo_service.py
yolov8n.pt
...
```

**Caso o download não seja feito, o Bot não será capaz de reconhecer os aúdios enviados.**
