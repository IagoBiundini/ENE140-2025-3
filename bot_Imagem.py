from ultralytics import YOLO 
from collections import Counter

class BotImagem:
    """
    Classe responsável pela identificação de objetos em imagens usando o modelo YOLOv8.
    
    Utiliza o modelo de visão computacional YOLOv8 para detectar e classificar objetos
    presentes em arquivos de imagem.
    """
    
    def __init__(self):
        """
        Inicializa a instância de BotImagem carregando o modelo YOLOv8.
        
        Carrega o modelo pré-treinado YOLOv8 de tamanho médio (yolov8m.pt) para detecção
        de objetos em imagens. Este modelo é capaz de detectar 80 classes diferentes de
        objetos com alta precisão. Também inicializa o dicionário tradutor que converte
        os nomes dos objetos detectados de inglês para português.
        
        Raises:
            FileNotFoundError: Se o arquivo 'yolov8m.pt' não for encontrado no diretório.
        """


        print('Carregando modelo de alta precisão...')
        # Trocado para 'm' (medium) para melhor detecção
        self.__modelo = YOLO('yolov8m.pt') 
        
        # Dicionário de objtos
        self.tradutor = {
            'person': 'pessoa', 'bicycle': 'bicicleta', 'car': 'carro', 'motorcycle': 'moto',
            'airplane': 'avião', 'bus': 'ônibus', 'train': 'trem', 'truck': 'caminhão',
            'boat': 'barco', 'traffic light': 'semáforo', 'fire hydrant': 'hidrante',
            'stop sign': 'placa de pare', 'parking meter': 'parquímetro', 'bench': 'banco',
            'bird': 'pássaro', 'cat': 'gato', 'dog': 'cachorro', 'horse': 'cavalo',
            'sheep': 'ovelha', 'cow': 'vaca', 'elephant': 'elefante', 'bear': 'urso',
            'zebra': 'zebra', 'giraffe': 'girafa', 'backpack': 'mochila', 'umbrella': 'guarda-chuva',
            'handbag': 'bolsa', 'tie': 'gravata', 'suitcase': 'mala', 'frisbee': 'frisbee',
            'skis': 'esquis', 'snowboard': 'snowboard', 'sports ball': 'bola', 'kite': 'pipa',
            'baseball bat': 'taco de beisebol', 'baseball glove': 'luva de beisebol',
            'skateboard': 'skate', 'surfboard': 'prancha de surfe', 'tennis racket': 'raquete de tênis',
            'bottle': 'garrafa', 'wine glass': 'taça de vinho', 'cup': 'copo', 'fork': 'garfo',
            'knife': 'faca', 'spoon': 'colher', 'bowl': 'tigela', 'banana': 'banana',
            'apple': 'maçã', 'sandwich': 'sanduíche', 'orange': 'laranja', 'broccoli': 'brócolis',
            'carrot': 'cenoura', 'hot dog': 'cachorro-quente', 'pizza': 'pizza', 'donut': 'donut',
            'cake': 'bolo', 'chair': 'cadeira', 'couch': 'sofá', 'potted plant': 'vaso de planta',
            'bed': 'cama', 'dining table': 'mesa de jantar', 'toilet': 'vaso sanitário',
            'tv': 'televisão', 'laptop': 'notebook', 'mouse': 'mouse', 'remote': 'controle remoto',
            'keyboard': 'teclado', 'cell phone': 'celular', 'microwave': 'micro-ondas',
            'oven': 'forno', 'toaster': 'torradeira', 'sink': 'pia', 'refrigerator': 'geladeira',
            'book': 'livro', 'clock': 'relógio', 'vase': 'vaso', 'scissors': 'tesoura','urso-brinquedo'
            'teddy bear': 'urso de pelúcia', 'hair drier': 'secador de cabelo', 'toothbrush': 'escova de dentes'
        }

    def identificar_arquivo(self, imagem):
        """
        Identifica e lista todos os objetos detectados em uma imagem.
        
        Processa uma imagem utilizando o modelo YOLOv8 para detectar objetos presentes.
        Os objetos são identificados em português com contagem de quantas vezes cada
        objeto aparece na imagem. A confiança mínima é definida em 30% para permitir
        detecções sensíveis.
        
        Args:
            imagem (str): Caminho do arquivo de imagem a ser analisada. Aceita formatos
                         comuns como JPG, PNG, etc.
        
        Returns:
            str: Mensagem formatada em markdown contendo os objetos identificados com suas
                 quantidades. Cada objeto é listado como um item com a contagem. Se nenhum
                 objeto for identificado, retorna uma mensagem informando isso.
        
        """
        identificador = self.__modelo.predict(source=imagem, conf=0.3, verbose=False)

        solucao_final = identificador[0]
        objetos_observados = []

        for objeto in solucao_final.boxes.cls:
            nome_ingles = solucao_final.names[int(objeto)]
            nome_pt = self.tradutor.get(nome_ingles, nome_ingles)
            objetos_observados.append(nome_pt)
            
        contagem = Counter(objetos_observados)

        if not contagem:
            return ('🔍 Não consegui identificar objetos específicos nesta imagem.')
        
        texto_resposta = '🖼️ *Análise da Imagem:*\n\n'
        for objeto, quantidade in contagem.items():
            # Deixa a primeira letra maiúscula e formata melhor
            texto_resposta += f'• {objeto.capitalize()}: {quantidade}\n'
            
        return (texto_resposta)