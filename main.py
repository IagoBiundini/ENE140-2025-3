from speech_music_recognition import Speech_audio_recognition, Music_recognition

""" 
    Aqui que roda o programa para ser testado.
    1 - Você deve criar um arquivo de áudio e importar para pasta (não é o final, mas para testes)
    2 - TROQUE O CAMINHO PARA O CAMINHO DO AUDIO UTILIZADO
    3 - Escolher o que você que fazer (1 para transcrição de áudio ou 2 para pesquisa de músicas)
    4 - Existe umas condições que precisam ter para rodar o código e está no READ ME

    IMPORTANTE- LEIA A READ ME
    MAIS IMPORTANTE -- O API ACRCloud é limitado então cuidado não use com frequência porque os
    creditos podem acabar e não dará para apresentar no dia, mas o shazam é tranquilo (API grátis).

    O shazam ele não reconhece linguagem "hummg" apenas melodias de músias tocadas
"""
caminho = r"Colocar o caminho do arquivo para testar"
escolha = input("Digite o que deseja fazer 1 Transcrição ou 2 presquisa de música?")
if escolha == "1":
    leitura = Speech_audio_recognition(caminho)
    print(f"Transcrição: {leitura.transcrever_audio()}")
elif escolha == "2":
    leitura = Music_recognition(caminho)
    leitura.search_music()
