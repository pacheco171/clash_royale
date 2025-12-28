"""
Clash Royale AI Assistant - Versão Melhorada
Requisitos: pip install mss pillow ultralytics opencv-python numpy PyQt6 pytesseract
"""

import sys
import time
import json
import traceback
from threading import Thread, Event, Lock
from datetime import datetime
from pathlib import Path
from queue import Queue, Empty
from collections import deque

import mss
import numpy as np
import cv2
import pytesseract
from PIL import Image
from ultralytics import YOLO
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QLabel, QSlider, QTextEdit,
    QGroupBox, QSpinBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QFont
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# ==== CONFIGURAÇÕES ====
ANALYSIS_INTERVAL = 2000  # ms entre análises
MATCH_RESET_THRESHOLD = 30  # segundos para detectar nova partida
BASE_DIR = Path(__file__).resolve().parent
FPS_LIMIT = 15
MAX_QUEUE_SIZE = 3

# ==== CARDS DATABASE ====
def load_cards_db():
    """Carrega banco de dados de cartas com fallback"""
    json_path = BASE_DIR / "cards_db.json"
    
    # Tenta carregar do arquivo
    if json_path.exists():
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
                if isinstance(data, dict) and "cards" in data:
                    cards_list = data["cards"]
                elif isinstance(data, list):
                    cards_list = data
                else:
                    cards_list = []
                
                # Converte lista para dicionário
                cards_dict = {}
                for card in cards_list:
                    name = card.get("name") or card.get("card") or card.get("id")
                    if name:
                        cards_dict[name] = card
                
                if cards_dict:
                    print(f"✅ {len(cards_dict)} cartas carregadas do banco de dados")
                    return cards_dict
        except Exception as e:
            print(f"⚠️ Erro ao carregar cards_db.json: {e}")

    # Banco de dados expandido como fallback
    print("⚠️ Usando banco de dados padrão")
    return {
        # Tropas
        'Knight': {'elixir': 3, 'type': 'melee', 'counters': ['Mini PEKKA', 'Prince'], 'weakness': ['Swarm']},
        'Archers': {'elixir': 3, 'type': 'ranged', 'counters': ['Valkyrie', 'Knight'], 'weakness': ['Arrows', 'Log']},
        'Giant': {'elixir': 5, 'type': 'tank', 'counters': ['Mini PEKKA', 'Inferno Tower'], 'weakness': ['PEKKA']},
        'PEKKA': {'elixir': 7, 'type': 'tank', 'counters': ['Giant', 'Golem'], 'weakness': ['Swarm', 'Inferno']},
        'Mini PEKKA': {'elixir': 4, 'type': 'melee', 'counters': ['Giant', 'Knight'], 'weakness': ['Swarm']},
        'Prince': {'elixir': 5, 'type': 'melee', 'counters': ['Wizard', 'Musketeer'], 'weakness': ['Swarm']},
        'Wizard': {'elixir': 5, 'type': 'ranged', 'counters': ['Swarm', 'Witch'], 'weakness': ['Lightning']},
        'Musketeer': {'elixir': 4, 'type': 'ranged', 'counters': ['Balloon', 'Baby Dragon'], 'weakness': ['Fireball']},
        'Hog Rider': {'elixir': 4, 'type': 'melee', 'counters': ['Buildings'], 'weakness': ['Cannon', 'Tesla']},
        'Valkyrie': {'elixir': 4, 'type': 'melee', 'counters': ['Swarm', 'Witch'], 'weakness': ['Mini PEKKA']},
        
        # Feitiços
        'Fireball': {'elixir': 4, 'type': 'spell', 'counters': ['Musketeer', 'Wizard', '3 Musketeers'], 'weakness': []},
        'Arrows': {'elixir': 2, 'type': 'spell', 'counters': ['Minions', 'Skeleton Army'], 'weakness': []},
        'Zap': {'elixir': 2, 'type': 'spell', 'counters': ['Inferno', 'Sparky'], 'weakness': []},
        'Lightning': {'elixir': 6, 'type': 'spell', 'counters': ['3 Musketeers', 'Sparky'], 'weakness': []},
        'Rocket': {'elixir': 6, 'type': 'spell', 'counters': ['Elixir Collector', 'Towers'], 'weakness': []},
        
        # Construções
        'Inferno Tower': {'elixir': 5, 'type': 'building', 'counters': ['Tanks'], 'weakness': ['Zap', 'Swarm']},
        'Cannon': {'elixir': 3, 'type': 'building', 'counters': ['Hog Rider', 'Giant'], 'weakness': ['Fireball']},
        'Tesla': {'elixir': 4, 'type': 'building', 'counters': ['Hog Rider', 'Balloon'], 'weakness': ['Lightning']},
    }

CARDS_DB = load_cards_db()

# ==== MAPEAMENTO CLASS_ID -> CARTA ====
CLASS_ID_TO_CARD = {
    0: 'Knight', 1: 'Archers', 2: 'Giant', 3: 'Fireball',
    4: 'Arrows', 5: 'Inferno Tower', 6: 'PEKKA', 7: 'Mini PEKKA',
    8: 'Prince', 9: 'Wizard', 10: 'Musketeer', 11: 'Hog Rider',
    12: 'Valkyrie', 13: 'Zap', 14: 'Lightning', 15: 'Rocket',
    16: 'Cannon', 17: 'Tesla',
}

def get_card_name_by_id(class_id):
    """Retorna nome da carta pelo ID"""
    return CLASS_ID_TO_CARD.get(class_id, f"Unknown_{class_id}")

def get_elixir_cost(card_name):
    """Retorna custo de elixir da carta"""
    info = CARDS_DB.get(card_name, {})
    return info.get('elixir', 0)

# ==== SISTEMA DE CAPTURA OTIMIZADO ====
class ScreenCapture:
    """Sistema de captura de tela thread-safe"""
    
    def __init__(self, region=None, fps_limit=FPS_LIMIT):
        self.region = region
        self.fps_limit = fps_limit
        self.frame_queue = Queue(maxsize=MAX_QUEUE_SIZE)
        self.stop_event = Event()
        self.thread = None
        self.lock = Lock()
        self.is_running = False
        
    def start(self):
        """Inicia captura de tela"""
        with self.lock:
            if self.is_running:
                print("⚠️ Captura já está rodando")
                return False
            
            self.stop_event.clear()
            self.thread = Thread(target=self._capture_worker, daemon=True, name="ScreenCapture")
            self.thread.start()
            self.is_running = True
            print("✅ Captura de tela iniciada")
            return True
    
    def stop(self, timeout=2.0):
        """Para captura de tela"""
        with self.lock:
            if not self.is_running:
                return
            
            self.stop_event.set()
            
        if self.thread:
            self.thread.join(timeout)
            if self.thread.is_alive():
                print("⚠️ Thread de captura não terminou no tempo esperado")
            else:
                print("✅ Captura de tela encerrada")
        
        self.is_running = False
        self.thread = None
        
        # Limpa fila
        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
            except Empty:
                break
    
    def get_frame(self):
        """Obtém frame mais recente"""
        try:
            return self.frame_queue.get_nowait()
        except Empty:
            return None
    
    def _capture_worker(self):
        """Worker de captura em thread separada"""
        sct = mss.mss()
        interval = 1.0 / max(1, self.fps_limit)
        
        try:
            while not self.stop_event.is_set():
                start_time = time.time()
                
                try:
                    # Captura frame
                    if self.region is None:
                        monitor = sct.monitors[1]
                        screenshot = sct.grab(monitor)
                    else:
                        screenshot = sct.grab(self.region)
                    
                    # Converte para numpy array
                    img = np.array(screenshot)
                    
                    # Remove canal alpha se presente
                    if img.ndim == 3 and img.shape[2] == 4:
                        img = img[:, :, :3]
                    
                    # Adiciona à fila (descarta se cheia)
                    try:
                        self.frame_queue.put_nowait(img)
                    except:
                        try:
                            # Remove frame antigo e adiciona novo
                            self.frame_queue.get_nowait()
                            self.frame_queue.put_nowait(img)
                        except:
                            pass
                    
                    # Controle de FPS
                    elapsed = time.time() - start_time
                    sleep_time = interval - elapsed
                    if sleep_time > 0:
                        time.sleep(sleep_time)
                        
                except Exception as e:
                    print(f"❌ Erro na captura: {e}")
                    time.sleep(0.5)
                    
        except Exception as e:
            print(f"❌ Erro crítico na captura: {e}")
            traceback.print_exc()
        finally:
            try:
                sct.close()
            except:
                pass

# ==== DETECTOR DE NOVA PARTIDA ====
class MatchDetector:
    """Detecta quando uma nova partida começa"""
    
    def __init__(self, reset_threshold=MATCH_RESET_THRESHOLD):
        self.last_towers_state = (3, 3)
        self.match_start_time = time.time()
        self.last_activity = time.time()
        self.reset_threshold = reset_threshold
        self.match_started = False  # Nova flag para indicar se a partida começou
        
    def check_new_match(self, my_towers, opp_towers):
        """Verifica se é uma nova partida"""
        current_time = time.time()
        current_state = (my_towers, opp_towers)
        
        # Detecta reset completo das torres
        if current_state == (3, 3) and self.last_towers_state != (3, 3):
            time_since_activity = current_time - self.last_activity
            
            if time_since_activity > self.reset_threshold:
                self.match_start_time = current_time
                self.last_towers_state = current_state
                self.last_activity = current_time
                self.match_started = True  # Marca que a partida começou
                return True
        
        self.last_towers_state = current_state
        self.last_activity = current_time
        return False
    
    def reset(self):
        """Reseta o detector"""
        self.last_towers_state = (3, 3)
        self.match_start_time = time.time()
        self.last_activity = time.time()
        self.match_started = False  # Reseta a flag

# ==== RASTREADOR DE DECK ====
class DeckTracker:
    """Rastreia deck do oponente"""
    
    def __init__(self):
        self.opponent_deck = []
        self.card_history = deque(maxlen=20)
        self.lock = Lock()
        self.cards_detected = 0  # Contador de cartas detectadas
        
    def add_card(self, card_name, elixir_cost, confidence=1.0):
        """Adiciona carta COM FILTRO ANTI-SPAM"""
        # Exige confiança mínima de 80%
        if confidence < 0.80:
            return False
        
        with self.lock:
            current_time = time.time()
            
            # Verifica se carta já existe no deck
            for card in self.opponent_deck:
                if card['name'] == card_name:
                    # Ignora se detectou a mesma carta há menos de 3 segundos
                    if current_time - card['last_seen'] < 3.0:
                        return False
                        
                    card['last_seen'] = current_time
                    card['times_played'] += 1
                    self.card_history.append(card_name)
                    self.cards_detected += 1
                    return True
                
            # Adiciona nova carta
            if len(self.opponent_deck) < 8:
                self.opponent_deck.append({
                    'name': card_name,
                    'elixir': elixir_cost,
                    'last_seen': current_time,
                    'times_played': 1
                })
                self.card_history.append(card_name)
                self.cards_detected += 1
                return True
            
            return False
        
    def get_cycle_prediction(self, count=4):
        """Prevê próximas cartas do ciclo"""
        with self.lock:
            if not self.opponent_deck:
                return []
            
            # Ordena por última vez vista (mais antigas primeiro)
            sorted_deck = sorted(self.opponent_deck, key=lambda x: x['last_seen'])
            return sorted_deck[:min(count, len(sorted_deck))]
    
    def get_deck_info(self):
        """Analisa tipo do deck"""
        with self.lock:
            if len(self.opponent_deck) < 3:
                return "Analisando deck..."
            
            types = [CARDS_DB.get(c['name'], {}).get('type', 'unknown') 
                    for c in self.opponent_deck]
            
            tank_count = types.count('tank')
            spell_count = types.count('spell')
            building_count = types.count('building')
            
            if tank_count >= 2:
                return "BEATDOWN (Tanques pesados)"
            elif spell_count >= 3:
                return "CYCLE (Cartas rápidas)"
            elif building_count >= 2:
                return "DEFENSIVE (Construções)"
            else:
                return "HÍBRIDO"
    
    def get_average_elixir(self):
        """Calcula elixir médio do deck"""
        with self.lock:
            if not self.opponent_deck:
                return 0
            total = sum(c['elixir'] for c in self.opponent_deck)
            return round(total / len(self.opponent_deck), 1)
    
    def reset(self):
        """Reseta o tracker"""
        with self.lock:
            self.opponent_deck = []
            self.card_history.clear()
            self.cards_detected = 0  # Reseta contador

# ==== ESTRATEGISTA ====
class StrategicAdvisor:
    """Sistema de aconselhamento estratégico"""
    
    def __init__(self):
        self.cards_db = CARDS_DB
        
    def get_advanced_advice(self, game_state, opponent_cycle, elixir_diff, match_started, cards_detected):
        """Gera conselho estratégico avançado"""
        # Se a partida não começou ou não detectou cartas suficientes, não dá conselhos
        if not match_started or cards_detected < 3:
            return {
                'advice': 'Aguardando início da partida...',
                'priority': 'low'
            }
        
        advice_parts = []
        priority = 'low'
        
        # Análise de elixir
        if elixir_diff >= 4:
            advice_parts.append("ATAQUE AGORA! +4 elixir")
            priority = 'high'
        elif elixir_diff >= 2:
            advice_parts.append("Pressione com +2 elixir")
            priority = 'medium'
        elif elixir_diff <= -4:
            advice_parts.append("DEFENDA! -4 elixir")
            priority = 'urgent'
        elif elixir_diff <= -2:
            advice_parts.append("Cuidado, -2 elixir")
            priority = 'high'
        
        # Análise do ciclo do oponente
        dangerous_cards = ['Fireball', 'Lightning', 'Rocket', 'PEKKA', 'Prince']
        
        # Trata opponent_cycle que pode ser lista de strings ou lista de dicts
        cycle_card_names = []
        if isinstance(opponent_cycle, list):
            for item in opponent_cycle:
                if isinstance(item, dict):
                    cycle_card_names.append(item.get('name', ''))
                elif isinstance(item, str):
                    cycle_card_names.append(item)
        
        for card in cycle_card_names[:2]:
            if card in dangerous_cards:
                card_info = self.cards_db.get(card, {})
                if card_info.get('type') == 'spell':
                    advice_parts.append(f"⚠️ {card} próximo - espalhe tropas")
                else:
                    advice_parts.append(f"⚠️ {card} próximo - prepare counter")
                priority = 'high' if priority == 'low' else priority
        
        # Análise de torres
        my_towers = game_state.get('myTowers', 3)
        opp_towers = game_state.get('opponentTowers', 3)
        
        if my_towers < opp_towers:
            advice_parts.append("Desvantagem de torres - defenda")
            priority = 'high' if priority == 'low' else priority
        elif my_towers > opp_towers:
            advice_parts.append("Vantagem de torres - pressione")
        
        # Se não há conselhos específicos
        if not advice_parts:
            advice_parts.append("Continue monitorando o jogo")
        
        return {
            'advice': ' | '.join(advice_parts[:3]),
            'priority': priority
        }
    
    def get_counter_suggestion(self, opponent_card):
        """Sugere counter para carta do oponente"""
        if opponent_card not in self.cards_db:
            return None
        
        card_info = self.cards_db[opponent_card]
        counters = card_info.get('counters', [])
        
        if counters:
            return f"Counter: {', '.join(counters[:3])}"
        return None

# ==== DETECTOR YOLO ====
class CardDetector:
    """Detector de cartas usando YOLO"""
    
    def __init__(self, model_path):
        self.model_path = Path(model_path)
        self.model = None
        self.load_model()
        
    def load_model(self):
        """Carrega modelo YOLO"""
        if not self.model_path.exists():
            print(f"⚠️ Modelo não encontrado: {self.model_path}")
            print("⚠️ Sistema funcionará sem detecção de cartas")
            return False
        
        try:
            self.model = YOLO(str(self.model_path))
            print(f"✅ Modelo YOLO carregado: {self.model_path}")
            return True
        except Exception as e:
            print(f"❌ Erro ao carregar modelo: {e}")
            return False
    
    def detect(self, frame_bgr, confidence_threshold=0.85):
        """Detecta cartas no frame"""
        if self.model is None:
            return []
        
        try:
            results = self.model(frame_bgr, verbose=False)
            detected = []
            
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    
                    if confidence > confidence_threshold:
                        card_name = get_card_name_by_id(class_id)
                        detected.append({
                            "name": card_name,
                            "confidence": confidence,
                            "bbox": box.xyxy[0].cpu().numpy().tolist()
                        })
            
            return detected
        except Exception as e:
            print(f"❌ Erro na detecção: {e}")
            return []

# ==== OCR PARA ELIXIR ====
class ElixirOCR:
    """Sistema de OCR para detecção de elixir"""
    @staticmethod
    def extract_elixir(frame_bgr, region=None):
        """OCR melhorado para elixir"""
        try:
            if region is None:
                height, width = frame_bgr.shape[:2]
                # AJUSTE ESSAS COORDENADAS PARA SUA TELA!
                region = (
                    int(height * 0.88),  # y1 - parte inferior da tela
                    int(height * 0.95),  # y2
                    int(width * 0.45),   # x1 - meio-esquerda
                    int(width * 0.55)    # x2 - meio-direita
                )
            
            y1, y2, x1, x2 = region
            elixir_region = frame_bgr[y1:y2, x1:x2]
            
            # MELHOR PRÉ-PROCESSAMENTO
            gray = cv2.cvtColor(elixir_region, cv2.COLOR_BGR2GRAY)
            
            # Threshold adaptativo (melhor para diferentes iluminações)
            thresh = cv2.adaptiveThreshold(
                gray, 255, 
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 
                11, 2
            )
            
            # Inverte se fundo for escuro
            if np.mean(thresh) < 127:
                thresh = cv2.bitwise_not(thresh)
            
            # OCR APENAS PARA NÚMEROS
            config = '--psm 7 -c tessedit_char_whitelist=0123456789'
            text = pytesseract.image_to_string(thresh, config=config)
            
            digits = ''.join(filter(str.isdigit, text))
            
            if digits:
                value = int(digits)
                return max(0, min(10, value))
            
            return 0
            
        except Exception as e:
            print(f"❌ OCR Erro: {e}")
            return 0

# ==== SINAIS PARA UI ====
class Signals(QObject):
    """Sinais Qt para comunicação thread-safe"""
    update_ui = pyqtSignal(dict)
    log_message = pyqtSignal(str, str)
    new_match_detected = pyqtSignal()
    status_changed = pyqtSignal(str)

# ==== OVERLAY WINDOW ====
class OverlayWindow(QMainWindow):
    """Janela de overlay para mostrar informações"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        """Inicializa interface do overlay"""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Widget central
        central = QWidget()
        central.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 180);
                border: 2px solid #a855f7;
                border-radius: 10px;
                color: white;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(8)
        
        # Header
        header = QLabel("🎮 CLASH ROYALE AI")
        header.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        header.setStyleSheet("color: #a855f7; border: none;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # Elixir
        elixir_group = QGroupBox("⚡ Elixir")
        elixir_group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #6b7280; border-radius: 5px; padding: 5px; }")
        elixir_layout = QHBoxLayout()
        
        self.my_elixir = QLabel("Você: 10")
        self.opp_elixir = QLabel("Oponente: ~5")
        self.my_elixir.setStyleSheet("background-color: rgba(37, 99, 235, 0.3); padding: 5px; border-radius: 5px;")
        self.opp_elixir.setStyleSheet("background-color: rgba(220, 38, 38, 0.3); padding: 5px; border-radius: 5px;")
        
        elixir_layout.addWidget(self.my_elixir)
        elixir_layout.addWidget(self.opp_elixir)
        elixir_group.setLayout(elixir_layout)
        layout.addWidget(elixir_group)
        
        self.elixir_diff = QLabel("Diferença: +0")
        self.elixir_diff.setStyleSheet("font-size: 10px; border: none; color: #fbbf24; font-weight: bold;")
        self.elixir_diff.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.elixir_diff)
        
        # Torres
        self.towers_label = QLabel("🏰 Torres: 3 x 3")
        self.towers_label.setStyleSheet("font-size: 10px; border: none; font-weight: bold;")
        layout.addWidget(self.towers_label)
        
        # Tipo de deck
        self.deck_type = QLabel("📊 Tipo: Analisando...")
        self.deck_type.setStyleSheet("font-size: 9px; border: none; color: #a78bfa;")
        layout.addWidget(self.deck_type)
        
        # Deck do oponente
        self.deck_label = QLabel("🃏 Deck: -")
        self.deck_label.setWordWrap(True)
        self.deck_label.setStyleSheet("""
            font-size: 9px;
            background-color: rgba(153, 27, 27, 0.3);
            padding: 5px;
            border-radius: 5px;
            border: 1px solid #991b1b;
        """)
        layout.addWidget(self.deck_label)
        
        # Próximas cartas
        self.cycle_label = QLabel("🔄 Próximas: -")
        self.cycle_label.setWordWrap(True)
        self.cycle_label.setStyleSheet("""
            font-size: 9px;
            background-color: rgba(161, 98, 7, 0.3);
            padding: 5px;
            border-radius: 5px;
            border: 1px solid #a16207;
        """)
        layout.addWidget(self.cycle_label)
        
        # Counter
        self.counter_label = QLabel("")
        self.counter_label.setWordWrap(True)
        self.counter_label.setStyleSheet("""
            font-size: 9px;
            background-color: rgba(59, 130, 246, 0.3);
            padding: 5px;
            border-radius: 5px;
            border: 1px solid #3b82f6;
        """)
        layout.addWidget(self.counter_label)
        
        # Sugestão estratégica
        self.suggestion_label = QLabel("💡 Aguardando análise...")
        self.suggestion_label.setWordWrap(True)
        self.suggestion_label.setStyleSheet("""
            font-size: 11px;
            font-weight: bold;
            background-color: rgba(34, 197, 94, 0.3);
            padding: 8px;
            border-radius: 5px;
            border: 2px solid #22c55e;
        """)
        layout.addWidget(self.suggestion_label)
        
        central.setLayout(layout)
        self.setCentralWidget(central)
        self.setGeometry(50, 50, 400, 360)
        
        # Variáveis para arrastar
        self.dragging = False
        self.offset = None
    
    def mousePressEvent(self, event):
        """Inicia arraste"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.offset = event.pos()
    
    def mouseMoveEvent(self, event):
        """Move janela"""
        if self.dragging and self.offset:
            self.move(self.pos() + event.pos() - self.offset)
    
    def mouseReleaseEvent(self, event):
        """Finaliza arraste"""
        self.dragging = False
    
    def update_data(self, data):
        """Atualiza dados do overlay"""
        try:
            # Valida dados
            if not isinstance(data, dict):
                return
            
            # Elixir
            my_elixir = data.get('myElixir', 0)
            opp_elixir = data.get('opponentElixir', 0)
            elixir_diff = my_elixir - opp_elixir
            
            self.my_elixir.setText(f"Você: {my_elixir}")
            self.opp_elixir.setText(f"Oponente: ~{opp_elixir}")
            
            # Cor da diferença
            if elixir_diff > 0:
                diff_color = "#22c55e"
                diff_symbol = "+"
            elif elixir_diff < 0:
                diff_color = "#ef4444"
                diff_symbol = ""
            else:
                diff_color = "#fbbf24"
                diff_symbol = ""
            
            self.elixir_diff.setText(f"Diferença: {diff_symbol}{elixir_diff}")
            self.elixir_diff.setStyleSheet(
                f"font-size: 10px; border: none; color: {diff_color}; font-weight: bold;"
            )
            
            # Torres
            my_towers = data.get('myTowers', 3)
            opp_towers = data.get('opponentTowers', 3)
            self.towers_label.setText(f"🏰 Torres: {my_towers} x {opp_towers}")
            
            # Tipo de deck
            deck_type = data.get('deckType', 'Analisando...')
            self.deck_type.setText(f"📊 Tipo: {deck_type}")
            
            # Deck do oponente
            deck = data.get('opponentDeck', [])
            if deck and isinstance(deck, list):
                deck_cards = []
                for c in deck:
                    if isinstance(c, dict):
                        name = c.get('name', '?')
                        elixir = c.get('elixir', 0)
                        deck_cards.append(f"{name}({elixir}⚡)")
                
                deck_str = ", ".join(deck_cards)
                avg_elixir = data.get('avgElixir', 0)
                self.deck_label.setText(f"🃏 Deck ({len(deck)}/8 | Média: {avg_elixir}⚡): {deck_str}")
            else:
                self.deck_label.setText("🃏 Deck: Descobrindo...")
            
            # Próximas cartas do ciclo
            cycle = data.get('cycle', [])
            if cycle and isinstance(cycle, list):
                cycle_cards = []
                for c in cycle:
                    if isinstance(c, dict):
                        name = c.get('name', '?')
                        elixir = c.get('elixir', 0)
                        cycle_cards.append(f"{name}({elixir}⚡)")
                
                cycle_str = ", ".join(cycle_cards)
                self.cycle_label.setText(f"🔄 Próximas: {cycle_str}")
            else:
                self.cycle_label.setText("🔄 Próximas: -")
            
            # Counter
            counter = data.get('counter', '')
            if counter:
                self.counter_label.setText(f"💡 {counter}")
                self.counter_label.show()
            else:
                self.counter_label.hide()
            
            # Sugestão estratégica
            priority = data.get('priority', 'low')
            suggestion = data.get('suggestion', 'Aguardando...')
            
            # Cores e ícones por prioridade
            priority_styles = {
                'urgent': ('rgba(220, 38, 38, 0.5)', '#dc2626', '🚨'),
                'high': ('rgba(249, 115, 22, 0.5)', '#f97316', '⚡'),
                'medium': ('rgba(234, 179, 8, 0.5)', '#eab308', '⚠️'),
                'low': ('rgba(34, 197, 94, 0.5)', '#22c55e', '✓')
            }
            
            bg, border, icon = priority_styles.get(priority, priority_styles['low'])
            
            self.suggestion_label.setStyleSheet(f"""
                font-size: 11px;
                font-weight: bold;
                background-color: {bg};
                padding: 8px;
                border-radius: 5px;
                border: 2px solid {border};
            """)
            self.suggestion_label.setText(f"{icon} {suggestion}")
            
        except Exception as e:
            print(f"❌ Erro ao atualizar overlay: {e}")
            traceback.print_exc()

# ==== PAINEL DE CONTROLE ====
from elixir_tracker import ElixirTracker

class ControlPanel(QMainWindow):
    """Painel principal de controle"""
       
    
    def __init__(self):
        super().__init__()
        self.elixir_tracker = ElixirTracker()
        # Componentes
        self.signals = Signals()
        self.tracker = DeckTracker()
        self.advisor = StrategicAdvisor()
        self.match_detector = MatchDetector()
        self.screen_capture = ScreenCapture()
        self.card_detector = CardDetector(BASE_DIR / "yolo_cards_slots.pt")
        self.elixir_ocr = ElixirOCR()
        self.overlay = OverlayWindow()
        
        # Estado
        self.is_analyzing = False
        self.analysis_lock = Lock()
        self.last_cards_detected = []
        
        # Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.on_timer_tick)
        
        # UI
        self.init_ui()
        
        # Conexões
        self.signals.update_ui.connect(self.update_overlay_data)
        self.signals.log_message.connect(self.add_log)
        self.signals.new_match_detected.connect(self.on_new_match)
        self.signals.status_changed.connect(self.update_status)
        
    def init_ui(self):
        """Inicializa interface do painel"""
        self.setWindowTitle("🎮 Clash Royale AI Assistant - Controle")
        self.setGeometry(100, 100, 650, 600)
        
        central = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Título
        title = QLabel("🏆 Clash Royale AI Assistant Pro")
        title.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #a855f7; padding: 10px;")
        layout.addWidget(title)
        
        # Controles principais
        controls_group = QGroupBox("Controles")
        controls_layout = QHBoxLayout()
        
        self.btn_start = QPushButton("▶️ Iniciar Análise")
        self.btn_start.clicked.connect(self.start_analysis)
        self.btn_start.setStyleSheet("""
            QPushButton {
                background-color: #22c55e;
                color: white;
                padding: 12px;
                font-weight: bold;
                font-size: 12px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #16a34a;
            }
        """)
        
        self.btn_stop = QPushButton("⏹️ Parar")
        self.btn_stop.clicked.connect(self.stop_analysis)
        self.btn_stop.setEnabled(False)
        self.btn_stop.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                color: white;
                padding: 12px;
                font-weight: bold;
                font-size: 12px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #dc2626;
            }
            QPushButton:disabled {
                background-color: #6b7280;
            }
        """)
        
        self.btn_reset = QPushButton("🔄 Reset Completo")
        self.btn_reset.clicked.connect(self.reset_all)
        self.btn_reset.setStyleSheet("""
            QPushButton {
                background-color: #6b7280;
                color: white;
                padding: 12px;
                font-weight: bold;
                font-size: 12px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #4b5563;
            }
        """)
        
        controls_layout.addWidget(self.btn_start)
        controls_layout.addWidget(self.btn_stop)
        controls_layout.addWidget(self.btn_reset)
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)
        
        # Overlay
        overlay_group = QGroupBox("Overlay")
        overlay_layout = QVBoxLayout()
        
        self.btn_toggle = QPushButton("👁️ Mostrar/Ocultar Overlay")
        self.btn_toggle.clicked.connect(self.toggle_overlay)
        self.btn_toggle.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                padding: 8px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """)
        overlay_layout.addWidget(self.btn_toggle)
        
        opacity_layout = QHBoxLayout()
        opacity_label = QLabel("Opacidade:")
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setMinimum(20)
        self.opacity_slider.setMaximum(100)
        self.opacity_slider.setValue(90)
        self.opacity_slider.valueChanged.connect(self.change_opacity)
        self.opacity_value = QLabel("90%")
        opacity_layout.addWidget(opacity_label)
        opacity_layout.addWidget(self.opacity_slider)
        opacity_layout.addWidget(self.opacity_value)
        overlay_layout.addLayout(opacity_layout)
        
        overlay_group.setLayout(overlay_layout)
        layout.addWidget(overlay_group)
        
        # Configurações
        config_group = QGroupBox("Configurações")
        config_layout = QHBoxLayout()
        
        interval_label = QLabel("Intervalo de análise (ms):")
        self.interval_spin = QSpinBox()
        self.interval_spin.setMinimum(500)
        self.interval_spin.setMaximum(10000)
        self.interval_spin.setValue(ANALYSIS_INTERVAL)
        self.interval_spin.setSingleStep(500)
        
        config_layout.addWidget(interval_label)
        config_layout.addWidget(self.interval_spin)
        config_layout.addStretch()
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # Status
        self.status_label = QLabel("⏸️ Status: Aguardando início")
        self.status_label.setStyleSheet("""
            background-color: #1f2937;
            color: #10b981;
            padding: 10px;
            border-radius: 5px;
            font-weight: bold;
            font-size: 11px;
        """)
        layout.addWidget(self.status_label)
        
        # Logs
        log_label = QLabel("📋 Logs do Sistema:")
        log_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(log_label)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        self.log_text.setStyleSheet("""
            background-color: #1f2937;
            color: #e5e7eb;
            border: 1px solid #374151;
            border-radius: 5px;
            padding: 5px;
            font-family: 'Courier New';
            font-size: 10px;
        """)
        layout.addWidget(self.log_text)
        
        # Info
        info = QLabel(
            "💡 Dicas: Arraste o overlay para reposicionar | "
            "Sistema detecta automaticamente novas partidas | "
            "Certifique-se que o modelo YOLO está na pasta do script"
        )
        info.setStyleSheet("color: #6b7280; font-size: 9px;")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        central.setLayout(layout)
        self.setCentralWidget(central)
        
        # Mostra overlay
        self.overlay.show()
        
        # Log inicial
        self.add_log("✅ Sistema inicializado", "success")
        if self.card_detector.model is None:
            self.add_log("⚠️ Modelo YOLO não carregado - detecção desabilitada", "warning")
    
    def start_analysis(self):
        """Inicia análise automática"""
        if self.is_analyzing:
            self.add_log("⚠️ Análise já está rodando", "warning")
            return
        
        self.is_analyzing = True
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        
        # Atualiza intervalo
        interval = self.interval_spin.value()
        self.timer.start(interval)
        
        # Inicia captura
        if self.screen_capture.start():
            self.signals.status_changed.emit("🟢 Analisando")
            self.add_log("✅ Análise automática iniciada", "success")
        else:
            self.stop_analysis()
            self.add_log("❌ Erro ao iniciar captura", "error")
    
    def stop_analysis(self):
        """Para análise"""
        if not self.is_analyzing:
            return
        
        self.is_analyzing = False
        self.timer.stop()
        self.screen_capture.stop()
        
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        
        self.signals.status_changed.emit("⏸️ Pausado")
        self.add_log("⏸️ Análise pausada", "info")
    
    def on_timer_tick(self):
        """Chamado periodicamente pelo timer"""
        with self.analysis_lock:
            frame = self.screen_capture.get_frame()
            
            if frame is None:
                return
            
            # Processa em thread separada
            Thread(target=self.process_frame, args=(frame,), daemon=True).start()
    
    def process_frame(self, frame):
        """Processa frame capturado"""
        try:
            # Valida frame
            if frame is None or not isinstance(frame, np.ndarray):
                return
            
            # Converte para BGR (OpenCV)
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            # Detecta cartas APENAS na região do adversário
            detected_cards = []
            try:
                # Pega só a metade superior da tela (região do adversário)
                h, w = frame_bgr.shape[:2]
                opponent_area = frame_bgr[0:int(h*0.5), :]  # 50% superior
                detected_cards = self.card_detector.detect(opponent_area)               
                if not isinstance(detected_cards, list):
                    detected_cards = []
                if detected_cards:
                    self.save_debug_screenshot(frame_bgr, detected_cards)    
            except Exception as e:
                self.add_log(f"⚠️ Erro na detecção de cartas: {str(e)}", "warning")
            
            # Atualiza tracker com cartas detectadas
            for card in detected_cards:
                try:
                    if isinstance(card, dict) and 'name' in card:
                        card_name = card['name']
                        elixir = get_elixir_cost(card_name)
                        confidence = card.get('confidence', 0)
                        added = self.tracker.add_card(card_name, elixir, confidence)
                        
                        # Log apenas se foi realmente adicionado
                        if added:
                            self.add_log(f"🃏 Nova carta: {card_name} ({confidence:.2%})", "success")
                except Exception:
                    continue
            
            # OCR de elixir
            my_elixir = 10  # Valor inicial correto: ambos começam com 10
            try:
                my_elixir = self.elixir_ocr.extract_elixir(frame_bgr)
            except Exception as e:
                self.add_log(f"⚠️ Erro no OCR de elixir: {str(e)}", "warning")
            
            # Prepara cartas detectadas com custo de elixir
            cards_with_cost = []
            for card in detected_cards:
                if isinstance(card, dict) and 'name' in card:
                    card_name = card['name']
                    elixir = get_elixir_cost(card_name)
                    card_copy = card.copy()
                    card_copy['elixir'] = elixir
                    cards_with_cost.append(card_copy)

            # Atualiza tracker de elixir
            opponent_elixir = self.elixir_tracker.update(cards_with_cost)     
            # Debug: mostra jogadas detectadas
            if cards_with_cost:  
                  recent_plays = self.elixir_tracker.get_recent_plays(3)
                  for play in recent_plays:
                      self.add_log(
                          f"⚡ {play['card']} ({play['cost']}) - {play['confidence']:.0%}",
                          "info"
                )
            # Torres (placeholder - implemente detecção real)
            my_towers = 3
            opp_towers = 3
            
            # Detecta nova partida
            try:
                if self.match_detector.check_new_match(my_towers, opp_towers):
                    self.signals.new_match_detected.emit()
            except Exception as e:
                self.add_log(f"⚠️ Erro na detecção de nova partida: {str(e)}", "warning")
            
            # Previsão de ciclo
            cycle = []
            try:
                cycle = self.tracker.get_cycle_prediction()
                if not isinstance(cycle, list):
                    cycle = []
            except Exception as e:
                self.add_log(f"⚠️ Erro na previsão de ciclo: {str(e)}", "warning")
            
            # Diferença de elixir
            elixir_diff = my_elixir - opponent_elixir
            
            # Conselho estratégico
            game_state = {
                'myElixir': my_elixir,
                'opponentElixir': opponent_elixir,
                'myTowers': my_towers,
                'opponentTowers': opp_towers,
                'priority': 'low'
            }
            
            # Passa informações sobre o estado da partida para o aconselhamento
            strategic_advice = self.advisor.get_advanced_advice(
                game_state,
                cycle,
                elixir_diff,
                self.match_detector.match_started,
                self.tracker.cards_detected
            )
            
            # Counter para última carta detectada
            counter_suggestion = ""
            if detected_cards and len(detected_cards) > 0:
                try:
                    last_card = detected_cards[-1]
                    if isinstance(last_card, dict) and 'name' in last_card:
                        counter_suggestion = self.advisor.get_counter_suggestion(last_card['name']) or ""
                except Exception as e:
                    self.add_log(f"⚠️ Erro no counter: {str(e)}", "warning")
            
            # Prepara dados para UI
            opponent_deck = []
            deck_type = "Analisando..."
            avg_elixir = 0
            
            try:
                opponent_deck = self.tracker.opponent_deck.copy() if hasattr(self.tracker, 'opponent_deck') else []
                deck_type = self.tracker.get_deck_info()
                avg_elixir = self.tracker.get_average_elixir()
            except Exception as e:
                self.add_log(f"⚠️ Erro ao obter info do deck: {str(e)}", "warning")
            
            ui_data = {
                'myElixir': my_elixir,
                'opponentElixir': opponent_elixir,
                'myTowers': my_towers,
                'opponentTowers': opp_towers,
                'opponentDeck': opponent_deck,
                'cycle': cycle,
                'deckType': deck_type,
                'avgElixir': avg_elixir,
                'suggestion': strategic_advice.get('advice', 'Aguardando...'),
                'priority': strategic_advice.get('priority', 'low'),
                'counter': counter_suggestion,
                'totalSpent': self.elixir_tracker.get_elixir_spent(),
                'recentPlays': self.elixir_tracker.get_recent_plays(5)
            }
            
            # Atualiza UI
            self.signals.update_ui.emit(ui_data)
            
            # Log de cartas novas (compara apenas nomes)
            try:
                last_card_names = {c.get('name', '') for c in self.last_cards_detected if isinstance(c, dict)}
                current_card_names = {c.get('name', '') for c in detected_cards if isinstance(c, dict)}
                new_card_names = current_card_names - last_card_names
                
                for card in detected_cards:
                    if isinstance(card, dict) and card.get('name', '') in new_card_names:
                        confidence = card.get('confidence', 0)
                        self.add_log(
                            f"🃏 Carta detectada: {card['name']} ({confidence:.2f})",
                            "info"
                        )
                
                self.last_cards_detected = [c for c in detected_cards if isinstance(c, dict)]
            except Exception as e:
                self.add_log(f"⚠️ Erro ao processar log de cartas: {str(e)}", "warning")
            
        except Exception as e:
            self.add_log(f"❌ Erro crítico no processamento: {str(e)}", "error")
            traceback.print_exc()
    
    def estimate_opponent_elixir(self):
        """Estima elixir do oponente baseado em cartas jogadas"""
        # Implementação simples - pode ser melhorada
        if not self.tracker.opponent_deck or self.tracker.cards_detected < 3:
            # Se não detectou cartas suficientes, assume valor inicial
            return 10  # Ambos começam com 10
        
        # Calcula baseado na média e tempo
        avg = self.tracker.get_average_elixir()
        return int(avg) if avg > 0 else 10
    
    def on_new_match(self):
        """Callback para nova partida detectada"""
        self.tracker.reset()
        self.match_detector.reset()
        self.elixir_tracker.reset()
        
        self.add_log("🆕 NOVA PARTIDA DETECTADA! Dados resetados", "success")
        
        # Reseta overlay
        self.signals.update_ui.emit({
            'myElixir': 10,  # Valor inicial correto
            'opponentElixir': 10,  # Valor inicial correto
            'myTowers': 3,
            'opponentTowers': 3,
            'opponentDeck': [],
            'cycle': [],
            'deckType': 'Nova partida começando...',
            'avgElixir': 0,
            'suggestion': 'Boa sorte! Começando análise...',
            'priority': 'low',
            'counter': ''
        })
    
    def reset_all(self):
        """Reset completo do sistema"""
        self.tracker.reset()
        self.match_detector.reset()
        self.last_cards_detected = []
        self.elixir_tracker.reset()
        
        self.add_log("🔄 Reset completo realizado", "info")
        self.on_new_match()
    
    def toggle_overlay(self):
        """Mostra/oculta overlay"""
        if self.overlay.isVisible():
            self.overlay.hide()
            self.add_log("👁️ Overlay ocultado", "info")
        else:
            self.overlay.show()
            self.add_log("👁️ Overlay exibido", "info")
    
    def change_opacity(self, value):
        """Altera opacidade do overlay"""
        self.overlay.setWindowOpacity(value / 100)
        self.opacity_value.setText(f"{value}%")
    
    def update_overlay_data(self, data):
        """Atualiza dados do overlay"""
        self.overlay.update_data(data)
    
    def update_status(self, status):
        """Atualiza label de status"""
        self.status_label.setText(f"Status: {status}")
    
    def add_log(self, message, msg_type="info"):
        """Adiciona mensagem ao log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        colors = {
            "success": "#22c55e",
            "error": "#ef4444",
            "warning": "#f59e0b",
            "info": "#3b82f6"
        }
        
        color = colors.get(msg_type, "#e5e7eb")
        
        self.log_text.append(
            f'<span style="color: #6b7280;">[{timestamp}]</span> '
            f'<span style="color: {color};">{message}</span>'
        )
        
        # Auto-scroll
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def closeEvent(self, event):
        """Cleanup ao fechar"""
        if self.is_analyzing:
            self.stop_analysis()
        self.overlay.close()
        event.accept()

# ==== MAIN ====
def main():
    """Função principal"""
    app = QApplication(sys.argv)
    
    # Estilo da aplicação
    app.setStyle('Fusion')
    
    # Cria e mostra painel de controle
    control = ControlPanel()
    control.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()