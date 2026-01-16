# ENE140-2025-3
Repositório da turma de ENE140 - Programação para Engenharia - 2025/3


# Bot Telegram com YOLO e Vosk

## Descrição do Projeto

Este projeto consiste no desenvolvimento de um **bot para Telegram**, implementado em Python, que integra **visão computacional** e **reconhecimento de fala**. O bot utiliza o modelo **YOLO** para detecção de objetos em imagens/vídeos e a biblioteca **Vosk** para transcrição de áudio, permitindo uma interação multimodal com o usuário.

O sistema foi desenvolvido com foco em modularidade e organização do código, utilizando conceitos de **Programação Orientada a Objetos**, como abstração, herança e polimorfismo, além da integração entre diferentes bibliotecas externas.

---

## Funcionalidades

* Integração com a API do Telegram
* Detecção de objetos em imagens e vídeos utilizando YOLO
* Reconhecimento de fala em áudios usando Vosk
* Processamento assíncrono de mensagens
* Estrutura de código modular e reutilizável

---

## Tecnologias Utilizadas

* **Python 3.10.05**
* **python-telegram-bot** – comunicação com o Telegram
* **Ultralytics (YOLO)** – visão computacional
* **Vosk** – reconhecimento de fala offline
* **NumPy** – operações numéricas
* **nest_asyncio** – suporte a execução assíncrona
* **Google Colab**
---

## Dependências

As dependências do projeto foram listadas manualmente com base nas bibliotecas efetivamente utilizadas no código.

Arquivo `requirements.txt`:

```txt
python-telegram-bot
ultralytics
vosk
nest_asyncio
numpy

```

Para instalar todas as dependências:

```bash
pip install -r requirements.txt
```

---

## Como Executar o Projeto

O projeto pode ser executado **de duas formas**: utilizando o **Google Colab** ou localmente por meio de arquivos `.py`.

---

### Opção 1: Execução no Google Colab

Essa opção é indicada para testes rápidos, sem necessidade de configuração do ambiente local.

1. Abra o Google Colab e crie um novo notebook.
2. Instale as dependências necessárias executando:

```python
!pip install python-telegram-bot ultralytics vosk nest_asyncio numpy 
!apt-get install ffmpeg -y
```

3. Importe e execute o código do projeto no notebook.
4. Configure o token do bot do Telegram diretamente no código ou como variável de ambiente dentro do Colab.

Observação: no Colab, o ambiente é temporário, portanto os modelos e dependências precisam ser reinstalados a cada nova sessão.

---

### Opção 2: Execução Local (arquivos .py)

Essa opção é recomendada para desenvolvimento contínuo.

1. Clone este repositório:

```bash
git clone <url-do-repositorio>
```

2. Acesse a pasta do projeto:

```bash
cd bot_telegram_GRP6
```

3. Instale as dependências:

```bash
pip install -r requirements.txt
```

4. Defina o token do bot do Telegram como variável de ambiente:

```bash
set TOKEN_TELEGRAM=SEU_TOKEN_AQUI
```

5. Execute o programa principal:

```bash
python GRP6_main.py
```

---

## Pontos de Atenção

* Alguns trechos do código utilizam **caminhos de arquivos e pastas locais** (por exemplo, para o modelo do Vosk ou arquivos temporários).
* Esses caminhos podem variar de acordo com o sistema operacional, estrutura de pastas ou ambiente de execução (Colab x execução local).
* Antes de executar o projeto, é necessário **verificar e ajustar manualmente** os caminhos definidos no código para que correspondam ao ambiente do usuário.

---

## Observações

* O modelo de reconhecimento de fala Vosk deve estar corretamente baixado e com o caminho configurado no código.
* O projeto foi desenvolvido em ambiente Windows, mas pode ser adaptado para outros sistemas operacionais.
