# Bot do Telegram para processamento de áudio e imagens
## ENE140-2025-3/Grupo 5

Este bot transcreve áudios enviados para ele e realiza o reconhecimento de imagens enviadas utilizando o YOLO.

O bot é capaz de:
* Detectar **objetos, animais e pessoas** em imagens usando **YOLOv8**
* Transcrever **mensagens de áudio (voz)** para texto
* Manter um **log de atividades** durante a execução

## Funcionalidades
### Processamento de imagens
* Detecta automaticamente imagens enviadas no chat
* Usa o modelo YOLOv8 (yolov8n.pt) para detecção
* Retorna:
  * Imagem com bounding boxes
  * Lista de objetos detectados
  * Confiança do modelo para cada objeto

### Processamento de áudios
* Converte áudio do Telegram (.ogg) para .wav
* Transcreve o áudio usando Google Speech Recognition
* Idioma: Português (pt-BR)

### Logs
* Todas as ações do bot são registradas em log.txt
* Logs possuem timestamp
* O arquivo é limpo automaticamente ao iniciar o bot
* Acesse aos logs atuais utilizando o comando /log

## Instalação
### Clone o repositório
```bash
git clone -b grupo5 <url-deste-repositorio>
```

### Crie o ambiente virtual (venv)
```powershell
python -m venv .venv
```
    
### Ative o ambiente virtual
```powershell
.venv\Scripts\activate
```

### Instale as dependências
```powershell
pip install -r requirements.txt
```

## Instale o FFmpeg
O FFmpeg é obrigatório para converter áudios .ogg para .wav
* Baixe em: https://ffmpeg.org/download.html
* Use a versão static build para Windows

### Adicione C:\ffmpeg\bin às Variáveis de Ambiente
É recomendado reiniciar o computador após este processo

### TOKEN do Telegram
No arquivo **main.py**, coloque seu TOKEN na sehuinte variável:

```python
token = ""
```
