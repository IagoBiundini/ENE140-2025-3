import speech_recognition as sr
from pydub import AudioSegment
import os
from time import sleep
from threading import Thread, Event
from shazamio import Shazam
import asyncio
from yt_dlp import YoutubeDL
import webbrowser
import wikipedia as wk
import difflib, time, hmac, hashlib, base64, requests


class Speech_audio_recognition():
    """
        Class principal de reconhecimento de áudio e transcrição de texto     
    """
    

    def __init__(self, audio: str):
        """
        Classe `Speech_audio_recognition` responsável por preparar e transcrever áudio usando o módulo de
        reconhecimento de fala. Suporta entradas como caminho para arquivo (wav, mp3, etc.)
        ou `pydub.AudioSegment`.

        :param audio: Caminho para o arquivo de áudio (ex.: 'mensagem.wav'). Deve ser uma string.
            O construtor apenas armazena o caminho; **não realiza a transcrição automaticamente**.
            Use o método `transcrever_audio()` para obter o texto transcrito a partir do arquivo de áudio ou implemente validações
            em `load_audio()`/`transcribe()` conforme necessário.
        :type audio: str
        """
        self._audio = audio
        self._frase = None
        self._rec = sr.Recognizer()
        #Eventos das threads
        self._stop_method = Event()
        self._update_thread = None
        # Caminho temporário padrão para arquivos WAV (usado para conversão/tempo de vida curto).
        self.caminho_temp = "audio_temp.wav"
        self.tempo = 0
        self.acesso = True


    def __converter_wav(self):
        """
            Método privado que converte o áudio de qualquer formato 
            suportado pelo ``pydub`` para WAV.
        """
        try:
            print(f"Carregando e convertendo o arquivo: {self._audio}")
            #Carregamento do arquivo .algumacoisa usando pydub
            #O pydub reconhecerá o formato pela extensão do caminho do arquivo automaticamente
            audio_comprimido = AudioSegment.from_file(self._audio)
            #Conferir a duração do áudio
            duracao_audio = audio_comprimido.duration_seconds
            print(f"O áudio original tem {duracao_audio:.2f} segundos.\n")
            #Conversão para .WAV
            audio_comprimido.export(self.caminho_temp, format = "wav")
            return (duracao_audio)
        except OSError as erro:
            print(f"Erro ao processar o arquivo de áudio: {erro}")
            return (0)        
    
    def Limpeza_dados(self):
        """
            Método responsável em limpar as variáveis        
        """
        if os.path.exists(self.caminho_temp):
            os.remove(self.caminho_temp)
            self._frase = None
            self.tempo = 0
            self.caminho_temp = "audio_temp.wav"
            print("Arquivo temporário WAV removido.")

    def transcrever_audio(self):
        """
            Transcreve o arquivo de áudio.

            O método realiza as seguintes etapas:
                1. Carrega o arquivo de áudio (qualquer formato suportado pelo pydub/ffmpeg).
                2. Converte o áudio para um WAV temporário pelo método privado.
                3. Usa o Google Web Speech API via `speech_recognition` para transcrever o áudio
                (idioma: português do Brasil - `pt-BR`).
                4. Remove o arquivo temporário ao final, mesmo em caso de erro.

            Retorno
            -------
            str | None
                Texto transcrito (string) se a transcrição for bem-sucedida, ou `None` em caso de falha.

            Exceções tratadas
            -----------------
            FileNotFoundError
                Quando o arquivo especificado em `self._audio` (variável passada) não é encontrado ou o FFmpeg
                não está disponível no PATH.
            sr.UnknownValueError
                Quando o reconhecedor não consegue entender o áudio.
            sr.RequestError
                Erros de requisição ao serviço de reconhecimento (por exemplo, problemas de rede).
            OSError
                Erros ao processar ou converter o arquivo de áudio.

            Observações
            -----------
            - **Requer `pydub` e `ffmpeg` instalados e acessíveis no PATH para converter formatos
            diferentes para WAV.**
        """
        try:
            #Converter o audio para o formato .WAV
            self.tempo = self.__converter_wav()

            #Ação da thread - Verifica se há threads múltiplas
            if (self._update_thread is None or not self._update_thread.is_alive()):
                self._update_thread = Thread(target=self.loading, daemon=True)
                self._update_thread.start()

            #Processamento do arquivo .WAV temporário
            with sr.AudioFile(self.caminho_temp) as source:
                #Leitura do audio
                read = self._rec.record(source)
            
            #Transcrição do audio usandi Google
            self._frase = self._rec.recognize_google(read, language="pt-BR")

            #Parar o loading
            self._stop_method.set()
            self._update_thread.join()
            #Limpa a linha do loading
            print("\r" + " " * 50, end="\r" + "\n")            

            return(self._frase)

        #!!!Tratamento de possíveis erros 
        #(Deve ser testado para achar erros que podem aparecer)
        except FileNotFoundError:
            print("\nErro: Arquivo de áudio não encontrado ou FFmpeg não está no PATH.")
            #Parar o loading
            self._stop_method.set()
            self._update_thread.join()
            #Limpa a linha do loading
            print("\r" + " " * 50, end="\r" + "\n")
            return(None)
        except sr.UnknownValueError:
            print("\nNão foi possível transcrever o áudio.")
            #Parar o loading
            self._stop_method.set()
            self._update_thread.join()
            #Limpa a linha do loading
            print("\r" + " " * 50, end="\r" + "\n")
            return(None)
        except sr.RequestError as e:
            print(f"\nErro na requisição ao serviço Google: {e}")
            #Parar o loading
            self._stop_method.set()
            self._update_thread.join()
            #Limpa a linha do loading
            print("\r" + " " * 50, end="\r" + "\n")
            return(None)
        except OSError as e:
            print(f"\nErro ao processar o arquivo de áudio: {e}")
            #Parar o loading
            self._stop_method.set()
            self._update_thread.join()
            #Limpa a linha do loading
            print("\r" + " " * 50, end="\r" + "\n")
            return(None)
        
        finally:
            if self.acesso:
                self.Limpeza_dados()
            
    def loading(self):
        """
            Método apenas visual para carregamento
        """
        pontos = ["Processando som [ . ]  ", "Processando som [ .. ] ", "Processando som [ ... ]"]
        i = 0
        while not self._stop_method.is_set():
            print(f"\r{pontos[i]}", end="", flush=True)
            i = (i + 1) % len(pontos)
            sleep(0.5)

class Music_recognition(Speech_audio_recognition):
    """
        Classe secundária, filha de Speech_audio_recognition
    """
    def __init__(self, audio):
        super().__init__(audio)
        self.shazam = Shazam()
        self.acr_access_key = "54102623e155975d35cfced21a29fa16"
        self.acr_access_secret = "AINEa9tZg3XdCwmxh5TPevmCSujUwYibGwmNvs4J"
        self.acr_requrl = "http://identify-us-west-2.acrcloud.com/v1/identify"    

    def search_music(self):
        """
            Método que indentifica uma determinada música pela letra ou melodia por 3 passos condicionados
            (Deve ser melhorado)

            Método 1) Uso do speech_recognition, caso não identifique usa o método 2
            
            Método 2) Uso do ShazamIO, caso não identifique usa o método 3
            
            Método 3) Uso do ACRCloud - pago, caso não identifique a última retorna ou printa **música não identificada** - 
        """

        print("\n---INICIANDO RECONHECIMENTO INTELIGENTE---")
        # Comparação entre speech_recongnition e Shazam()
        self.acesso = False
        texto_transcrito = self.transcrever_audio()

        if (self.tempo >= 12): #Conferir se a duração do audio é superior a 20 segundos
            # (Passo 1) Pesquisa por voz e captura o título
            titulo_voz = None
            resultado_parcial = False
            
            if texto_transcrito:
                lista_pesquisa = self._buscar_youtuber(texto_transcrito)
                if lista_pesquisa:
                    titulo_voz = lista_pesquisa[1]
                else:
                    print("Busca no YouTube não retornou resultados a partir da transcrição.")
            
            # (Passo 2) Pesquisa no banco de dados do Shazam - Pela melodia ou sons conhecido
            titulo_shazam = asyncio.run(self._identificar_shazam())

            # Comparação cruzada
            if (titulo_voz and titulo_shazam): #Compara se os dois são diferentes de None
                similaridade = difflib.SequenceMatcher(None, titulo_voz.lower(), titulo_shazam.lower()).ratio()  
                
                if similaridade > 0.4: # Se houver 40% de semelhança nos nomes - Deve ser mudado caso de erros consecutivos
                    print("Voz e Shazam confirmam a mesma música.")
                    self.abrir_video(titulo_shazam)                        
                else:
                    print("Divergência encontrada. O Shazam é mais preciso para melodias.")
                    self.abrir_video(titulo_shazam)
            
            elif titulo_shazam:
                print("Pesquisado apenas pelo shazam")
                self.abrir_video(titulo_shazam)
            elif titulo_voz:
                print("Pesquisado apenas pelo speech_recognition")
                self.abrir_video(titulo_voz)
            else:
                print("\nNão foi possível identificar a música nem por speech e nem por shazam")
                resultado_parcial = True #Só troca se não achar a pesquisa do speech_recognition e Shazam
            
            if resultado_parcial:
                resultado_final = self.identificar_pela_acrcloud()
                if resultado_final:
                    self.abrir_video(resultado_final)

        else:
            print("Tempo insuficiente para análise e pesquisa da música, envie um com um tempo superior a 20 segundos")
        
        self.Limpeza_dados()
    

    def identificar_pela_acrcloud(self):
        """
        Lê o áudio de self.caminho_temp e envia para a ACRCloud.
        Retorna 'Título - Artista' ou None.
        """
        import time, hmac, hashlib, base64, requests 

        print("\nConsultando banco de dados ACRCloud...")

        # 1. Preparar a Assinatura (Exigência da API)
        timestamp = str(int(time.time()))
        string_to_sign = f"POST\n/v1/identify\n{self.acr_access_key}\naudio\n1\n{timestamp}"
        
        sign = base64.b64encode(
            hmac.new(self.acr_access_secret.encode('utf-8'), 
                    string_to_sign.encode('utf-8'), 
                    hashlib.sha1).digest()
        ).decode('utf-8')

        # 2. Ler o arquivo e enviar
        try:
            # Aqui é onde o Python 'lê' o áudio para enviar
            with open(self.caminho_temp, 'rb') as arquivo_audio:
                arquivos = {'sample': arquivo_audio}
                dados_post = {
                    'access_key': self.acr_access_key,
                    'sample_bytes': str(os.path.getsize(self.caminho_temp)),
                    'timestamp': timestamp,
                    'signature': sign,
                    'data_type': 'audio',
                    'signature_version': '1'
                }

                resposta = requests.post(self.acr_requrl, files=arquivos, data=dados_post, timeout=20)
                res_json = resposta.json()

            status = res_json.get('status', {})
            code = status.get('code')
            msg = status.get('msg')

            if code == 0:
                # 3. Processar o resultado
                if res_json.get('status', {}).get('code') == 0:
                    metadata = res_json.get('metadata', {})
                    
                    # A ACRCloud separa 'humming' (cantarolar) de 'music' (original)
                    # Tentamos pegar o primeiro que aparecer
                    musica = metadata.get('humming', metadata.get('music', []))
                    
                    if musica: 
                        item = musica[0]
                        titulo = item.get('title')
                        artista = item.get('artists', [{}])[0].get('name')                    
                        return (titulo + ", "+ artista)

            elif code == 1001:
                print("ACRCloud: Requisição OK, mas não reconheci esse som/cantarolar.")
            elif code == 3003:
                print("LIMITE EXCEDIDO: Você usou todas as suas consultas gratuitas da ACRCloud!")
            else:
                print(f"Erro ACRCloud {code}: {msg}")          
            return None

        except Exception as e:
            print(f"Erro na comunicação com ACRCloud: {e}")
            return None
        
    def abrir_video(self,titulo_pesquisa):
        lista_pesquisa = self._buscar_youtuber(titulo_pesquisa)
        if not lista_pesquisa:
            print("Nenhum vídeo encontrado para a pesquisa.")
            return
        while True:
            try:
                escolha = int(input("\nDeseja abrir a música no YouTuber Music? (1-sim / 0-Não)"))
                if (escolha == 1):
                    webbrowser.open(lista_pesquisa[0])
                    print("Vídeo aberto no navegador")
                    break
                elif escolha == 0:
                    print(f"Link do vídeo: {lista_pesquisa[0]}")
            except Exception as erro:
                print("Entrada inválida, digite apenas 1 para sim e 0 para não")
    
    async def _identificar_shazam(self):
        """
            Método auxiliar que identifica a música pela frequência e pesquisa 
            no banco de dados do Shazam
        
        """
        print("\nTentando reconhecer a melodia (Shazam)...")
        try:
            out = await self.shazam.recognize(self.caminho_temp)
            if 'track' in out:
                titulo = out['track']['title']
                artista = out['track']['subtitle']
                return f"{titulo} {artista}"
            return None
        except Exception as e:
            print(f"Erro no Shazam: {e}")
            return None    

    def _buscar_youtuber(self, texto_busca):
        """
            Método auxiliar que procura o título no youtuber

        :param texto_transcrito: Texto transcrito pelo speech_recognition para obtenção da pesquisa
        :type  texto_transcrito: str
        """
        busca_qtd = 3
        ydl_opts = {
            'format': 'best',
            'quiet': True,
            'noplaylist': True,
            'extract_flat': True,
        }
        print("\nBuscando os vídeos mais relevantes no YouTube...\n")
        try:
            with YoutubeDL(ydl_opts) as ydl:
                result = ydl.extract_info(f"ytsearch{busca_qtd}:{texto_busca}", download=False)

                if result and 'entries' in result and len(result['entries']) > 0:
                    videos = result['entries']
                    # Pega o vídeo com mais visualizações
                    video_mais_visto = max(videos, key=lambda x: x.get('view_count', 0))
                    link_direto = video_mais_visto['url']
                    url_music = link_direto.replace("www.youtube.com", "music.youtube.com")
                    titulo = video_mais_visto.get('title')
                    views = video_mais_visto.get('view_count', 0)

                    print(f" Vídeo mais relevante encontrado:")
                    print(f"   Título: {titulo}")
                    print(f"   Visualizações: {views:,}\n")

                    # Retorna [url, titulo, views]
                    return [url_music, titulo, views]
                else:
                    print("Transcrição dita, não encontrou o vídeo")
                    return None
        except Exception as e:
            print(f"Erro ao buscar no YouTube: {e}")
            return None


    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    


    def _buscar_curiosidades(self,titulo):
        """
            Método que pesquisa no wikipedia as curiosidade sobre o titulo da música

        Args:
            titulo (str): Título da música puxado do Youtuber
        """ 
        #Definir o idioma da pesquisa
        wk.set_lang("pt")
        
        query = "(canção)" + titulo

        try:
            # ajustar o sentences para pegar mais ou menos frases
            resume = wk.summary(query, sentences = 10)
            print(f"\n Cusiosidades sobre {titulo} por Wikipedia")
            print(resume)
        except wk.exceptions.PageError:
            #Caso não ache
            try:
                # ajustar o sentences para pegar mais ou menos frases
                resume = wk.summary(titulo, sentence = 10)
                print(f"\n Cusiosidades sobre {titulo} por Wikipedia")
                print(resume)
            except wk.exceptions.PageError:
                print("Pesquisa ou página não encontrada")
            except wk.exceptions.DisambiguationError as erro:
                print("Múltiplas páginas encontradas. Sugestões:")
                print(erro.options[:5])
        except wk.exceptions.DisambiguationError as erro:
            #Caso há páginas com mesmo nome ou nõa tem pesquisas relacionadas
            print("Múltiplas páginas encontradas. Escolhendo a primeira opção automaticamente...")
            pagina = wk.page(erro.options[0])  # Pega a primeira sugestão
            print(f"\nCuriosidades sobre '{pagina.title}' (da Wikipedia):")
            print(pagina.summary[0:800] + "...") 

            
        


                
       






    
    



