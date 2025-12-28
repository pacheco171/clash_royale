# 🎮 Clash Royale Monitor

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)

Sistema avançado de análise e monitoramento em tempo real do Clash Royale usando Computer Vision e Deep Learning.

## 📋 Índice

- [Sobre o Projeto](#sobre-o-projeto)
- [Funcionalidades](#funcionalidades)
- [Tecnologias](#tecnologias)
- [Pré-requisitos](#pré-requisitos)
- [Instalação](#instalação)
- [Uso](#uso)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Treinamento do Modelo](#treinamento-do-modelo)
- [Configuração](#configuração)
- [Contribuindo](#contribuindo)
- [Licença](#licença)
- [Autor](#autor)

## 🎯 Sobre o Projeto

Este projeto utiliza YOLOv8 e técnicas avançadas de visão computacional para:
- Detectar e identificar cartas em tempo real
- Rastrear elixir do jogador e oponente
- Analisar estratégias de jogo
- Fornecer alertas sonoros em momentos críticos
- Manter histórico detalhado de partidas

## ✨ Funcionalidades

### Principais
- ✅ **Detecção de Cartas em Tempo Real** - Identifica todas as 121 cartas do jogo
- ✅ **Rastreamento de Elixir** - Monitora elixir usando OCR
- ✅ **Análise de Slots** - Detecta posição e disponibilidade das cartas
- ✅ **Alertas Sonoros** - Notificações para eventos importantes
- ✅ **Histórico de Partidas** - Salva estatísticas detalhadas
- ✅ **Estratégia Local** - Sistema de recomendações baseado em IA

### Em Desenvolvimento
- 🔄 Análise de ciclo de cartas
- 🔄 Predição de próximas jogadas do oponente
- 🔄 Interface gráfica aprimorada
- 🔄 Modo de replay de partidas

## 🛠️ Tecnologias

### Core
- **Python 3.8+**
- **YOLOv8** - Detecção de objetos
- **OpenCV** - Processamento de imagem
- **PyTorch** - Deep Learning
- **Tesseract OCR** - Reconhecimento de texto

### Bibliotecas Auxiliares
- NumPy - Computação numérica
- Pillow - Manipulação de imagens
- pyttsx3 - Text-to-Speech
- mss - Screen capture

## 📦 Pré-requisitos

### Sistema Operacional
- Windows 10/11
- Linux (Ubuntu 20.04+)
- macOS 10.15+

### Software
- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)
- Tesseract OCR instalado no sistema

### Hardware Recomendado
- GPU NVIDIA com CUDA (opcional, mas recomendado)
- 8GB RAM mínimo
- 2GB espaço em disco

## 🚀 Instalação

### 1. Clone o Repositório
```bash
git clone https://github.com/pacheco171/clash_royale.git
cd clash_royale
```

### 2. Crie um Ambiente Virtual
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Instale as Dependências
```bash
pip install -r requirements.txt
```

### 4. Instale o Tesseract OCR

**Windows:**
- Baixe de: https://github.com/UB-Mannheim/tesseract/wiki
- Instale e adicione ao PATH

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

### 5. Configure o Projeto
```bash
# Edite config.json com suas preferências
cp config.json.example config.json
```

## 💻 Uso

### Modo Básico
```bash
python main.py
```

### Coletar Dados de Treinamento
```bash
python data_collector.py
```

### Anotar Imagens para Treinamento
```bash
python annotator.py
```

### Treinar Modelo YOLO
```bash
python train_yolo_cards.py
```

### Visualizar Cartas Detectadas
```bash
python show_cards.py
```

### Extrair Frames de Vídeo
```bash
python extract_frames_from_video.py --video caminho/video.mp4 --output dataset/frames
```

## 📁 Estrutura do Projeto

```
clash_royale/
│
├── main.py                          # Arquivo principal
├── requirements.txt                 # Dependências Python
├── config.json                      # Configurações do projeto
├── cards_db.json                    # Base de dados de cartas
├── match_history.json              # Histórico de partidas
│
├── dataset/                         # Dados de treinamento
│   ├── images/                      # Imagens anotadas
│   └── labels/                      # Anotações YOLO
│
├── runs/                            # Resultados de treinamento
│   └── cards_slots/
│       └── weights/
│           └── best.pt              # Melhor modelo treinado
│
├── yolo_detector.py                # Detector YOLO
├── elixir_tracker.py               # Rastreador de elixir
├── audio_alerts.py                 # Sistema de alertas
├── match_history.py                # Gerenciador de histórico
├── local_strategy.py               # Sistema de estratégia
│
├── annotator.py                    # Ferramenta de anotação
├── data_collector.py               # Coletor de dados
├── train_yolo_cards.py            # Script de treinamento
├── prepare_yolo_cards_only.py     # Preparação de dataset
├── auto_label_fixed_cards.py      # Auto-anotação
├── get_card_slots.py              # Detecção de slots
├── ocr_elixir.py                  # OCR para elixir
├── show_cards.py                  # Visualizador
├── extract_frames_from_video.py   # Extração de frames
├── update_cards_db.py             # Atualização de database
│
├── yolov8n.pt                     # Modelo YOLOv8 base
├── yolo_cards_slots.pt            # Modelo treinado
│
├── README.md                       # Este arquivo
├── GUIA_COMPLETO.md               # Guia detalhado
├── .gitignore                     # Arquivos ignorados
└── .gitattributes                 # Atributos Git
```

## 🎓 Treinamento do Modelo

### 1. Preparar Dataset
```bash
# Coletar imagens
python data_collector.py

# Anotar manualmente
python annotator.py

# Ou usar auto-anotação (para cartas fixas)
python auto_label_fixed_cards.py
```

### 2. Preparar Formato YOLO
```bash
python prepare_yolo_cards_only.py
```

### 3. Treinar
```bash
python train_yolo_cards.py --epochs 100 --batch 16
```

### 4. Avaliar Resultados
```bash
python show_cards.py --model runs/cards_slots/weights/best.pt
```

## ⚙️ Configuração

### config.json
```json
{
  "detection": {
    "confidence_threshold": 0.5,
    "iou_threshold": 0.4,
    "model_path": "yolo_cards_slots.pt"
  },
  "elixir": {
    "ocr_enabled": true,
    "update_interval": 0.5
  },
  "alerts": {
    "enabled": true,
    "volume": 0.7,
    "critical_elixir": 3
  },
  "screen": {
    "capture_region": null,
    "fps": 30
  }
}
```

### Ajustar Região de Captura
```python
# Em main.py
CAPTURE_REGION = {
    "top": 100,
    "left": 100,
    "width": 800,
    "height": 600
}
```

## 📊 Uso Avançado

### API Programática
```python
from yolo_detector import YOLODetector
from elixir_tracker import ElixirTracker

# Inicializar
detector = YOLODetector("yolo_cards_slots.pt")
elixir = ElixirTracker()

# Detectar cartas
cards = detector.detect(frame)

# Rastrear elixir
player_elixir = elixir.get_player_elixir(frame)
opponent_elixir = elixir.get_opponent_elixir(frame)
```

### Integração com Streaming
```python
import cv2
from main import ClashRoyaleMonitor

monitor = ClashRoyaleMonitor()
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if ret:
        results = monitor.process_frame(frame)
        # Fazer algo com os resultados
```

## 🤝 Contribuindo

Contribuições são bem-vindas! Para contribuir:

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/NovaFuncionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/NovaFuncionalidade`)
5. Abra um Pull Request

### Diretrizes
- Siga o PEP 8 para código Python
- Adicione testes para novas funcionalidades
- Atualize a documentação conforme necessário
- Use mensagens de commit descritivas

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 👨‍💻 Autor

**Enzzo Pacheco**

- GitHub: [@pacheco171](https://github.com/pacheco171)
- Projeto: [clash_royale](https://github.com/pacheco171/clash_royale)

## 🙏 Agradecimentos

- Ultralytics pela biblioteca YOLOv8
- Comunidade Clash Royale
- Contribuidores do projeto

## 📞 Suporte

Encontrou um bug ou tem uma sugestão?
- Abra uma [Issue](https://github.com/pacheco171/clash_royale/issues)
- Entre em contato via GitHub

## 🔄 Atualizações Recentes

### v1.0.0 (2025)
- Lançamento inicial
- Detecção de 121 cartas
- Sistema de alertas sonoros
- Rastreamento de elixir

---

⭐ Se este projeto te ajudou, considere dar uma estrela no GitHub!
