"""
elixir_tracker.py
Sistema de rastreamento de elixir do oponente
Integrado com detecção de cartas e anti-spam
"""

import time
from collections import deque
from threading import Lock


class ElixirTracker:
    """Rastreia elixir do oponente baseado em cartas jogadas"""
    
    def __init__(self):
        """Inicializa o rastreador de elixir"""
        # Configurações
        self.ELIXIR_MAX = 10
        self.ELIXIR_START = 5  # Elixir inicial no começo da partida
        self.REGEN_RATE = 1.0  # +1 elixir por segundo
        self.DOUBLE_ELIXIR_RATE = 2.0  # x2 no último minuto
        
        # Estado atual
        self.opponent_elixir = self.ELIXIR_START
        self.last_update_time = time.time()
        self.match_start_time = time.time()
        self.double_elixir_mode = False
        
        # Histórico de jogadas (anti-spam)
        self.recent_plays = deque(maxlen=50)
        self.play_history = []  # Histórico completo
        
        # Thread safety
        self.lock = Lock()
        
        # Estatísticas
        self.total_elixir_spent = 0
        self.play_count = 0
        
    def update(self, detected_cards):
        """
        Atualiza elixir baseado em cartas detectadas
        
        Args:
            detected_cards: Lista de cartas detectadas [{'name': str, 'elixir': int, 'confidence': float}]
            
        Returns:
            int: Elixir estimado do oponente
        """
        with self.lock:
            current_time = time.time()
            
            # 1. REGENERAÇÃO AUTOMÁTICA
            time_elapsed = current_time - self.last_update_time
            regen_rate = self.DOUBLE_ELIXIR_RATE if self.double_elixir_mode else self.REGEN_RATE
            elixir_regenerated = time_elapsed * regen_rate
            
            self.opponent_elixir = min(self.ELIXIR_MAX, self.opponent_elixir + elixir_regenerated)
            self.last_update_time = current_time
            
            # 2. PROCESSA CARTAS DETECTADAS (com anti-spam)
            for card in detected_cards:
                if not isinstance(card, dict):
                    continue
                
                card_name = card.get('name', '')
                elixir_cost = card.get('elixir', 0)
                confidence = card.get('confidence', 0)
                
                # Filtra detecções com baixa confiança
                if confidence < 0.75 or elixir_cost == 0:
                    continue
                
                # ANTI-SPAM: Ignora se mesma carta foi detectada recentemente
                if self._is_duplicate_detection(card_name, current_time):
                    continue
                
                # Registra jogada
                self._register_play(card_name, elixir_cost, confidence, current_time)
                
                # Subtrai elixir
                self.opponent_elixir -= elixir_cost
                
                # Permite elixir negativo (empréstimo)
                # O jogo permite gastar até 10 de elixir emprestado
            
            # 3. Garante que elixir não ultrapasse máximo
            self.opponent_elixir = min(self.ELIXIR_MAX, self.opponent_elixir)
            
            # 4. Retorna elixir estimado (mínimo 0 para display)
            return max(0, int(round(self.opponent_elixir)))
    
    def _is_duplicate_detection(self, card_name, current_time):
        """
        Verifica se é uma detecção duplicada (anti-spam)
        
        Args:
            card_name: Nome da carta
            current_time: Timestamp atual
            
        Returns:
            bool: True se é duplicata
        """
        # Janela de tempo para considerar duplicata (segundos)
        DUPLICATE_WINDOW = 2.5
        
        # Verifica nas jogadas recentes
        for play in reversed(self.recent_plays):
            time_diff = current_time - play['timestamp']
            
            # Se passou tempo suficiente, não é mais duplicata
            if time_diff > DUPLICATE_WINDOW:
                break
            
            # Mesma carta dentro da janela = duplicata
            if play['card'] == card_name:
                return True
        
        return False
    
    def _register_play(self, card_name, elixir_cost, confidence, timestamp):
        """Registra uma jogada no histórico"""
        play_data = {
            'card': card_name,
            'cost': elixir_cost,
            'confidence': confidence,
            'timestamp': timestamp,
            'elixir_after': self.opponent_elixir - elixir_cost
        }
        
        self.recent_plays.append(play_data)
        self.play_history.append(play_data)
        
        self.total_elixir_spent += elixir_cost
        self.play_count += 1
    
    def enable_double_elixir(self):
        """Ativa modo de elixir duplo (último minuto)"""
        with self.lock:
            if not self.double_elixir_mode:
                self.double_elixir_mode = True
                print("⚡⚡ MODO ELIXIR DUPLO ATIVADO!")
    
    def disable_double_elixir(self):
        """Desativa modo de elixir duplo"""
        with self.lock:
            self.double_elixir_mode = False
    
    def check_double_elixir_time(self):
        """
        Verifica se já passou 2 minutos de partida (elixir duplo)
        
        Returns:
            bool: True se deve ativar elixir duplo
        """
        match_duration = time.time() - self.match_start_time
        
        # Elixir duplo começa aos 2 minutos (120 segundos)
        if match_duration >= 120 and not self.double_elixir_mode:
            self.enable_double_elixir()
            return True
        
        return False
    
    def get_recent_plays(self, count=5):
        """
        Retorna últimas N jogadas
        
        Args:
            count: Número de jogadas a retornar
            
        Returns:
            list: Lista com últimas jogadas
        """
        with self.lock:
            return list(self.recent_plays)[-count:]
    
    def get_elixir_spent(self):
        """Retorna total de elixir gasto pelo oponente"""
        with self.lock:
            return self.total_elixir_spent
    
    def get_average_cost_per_play(self):
        """Retorna custo médio por jogada"""
        with self.lock:
            if self.play_count == 0:
                return 0
            return round(self.total_elixir_spent / self.play_count, 1)
    
    def get_stats(self):
        """
        Retorna estatísticas completas
        
        Returns:
            dict: Estatísticas do tracker
        """
        with self.lock:
            match_duration = time.time() - self.match_start_time
            
            return {
                'current_elixir': max(0, int(round(self.opponent_elixir))),
                'total_spent': self.total_elixir_spent,
                'play_count': self.play_count,
                'avg_cost': self.get_average_cost_per_play(),
                'match_duration': round(match_duration, 1),
                'double_elixir': self.double_elixir_mode,
                'recent_plays': self.get_recent_plays(5)
            }
    
    def reset(self):
        """Reseta o tracker para nova partida"""
        with self.lock:
            self.opponent_elixir = self.ELIXIR_START
            self.last_update_time = time.time()
            self.match_start_time = time.time()
            self.double_elixir_mode = False
            
            self.recent_plays.clear()
            self.play_history = []
            
            self.total_elixir_spent = 0
            self.play_count = 0
            
            print("🔄 Elixir Tracker resetado - Nova partida!")
    
    def can_afford_cards(self, deck_cards):
        """
        Retorna quais cartas do deck o oponente pode jogar agora
        
        Args:
            deck_cards: Lista de cartas do deck [{'name': str, 'elixir': int}]
            
        Returns:
            list: Cartas que podem ser jogadas
        """
        with self.lock:
            current_elixir = max(0, self.opponent_elixir)
            affordable = []
            
            for card in deck_cards:
                if isinstance(card, dict):
                    card_elixir = card.get('elixir', 0)
                    if card_elixir <= current_elixir:
                        affordable.append(card)
            
            return affordable
    
    def get_time_until_card(self, elixir_cost):
        """
        Calcula tempo até oponente ter elixir para carta
        
        Args:
            elixir_cost: Custo da carta em elixir
            
        Returns:
            float: Tempo em segundos (0 se já pode jogar)
        """
        with self.lock:
            elixir_needed = elixir_cost - self.opponent_elixir
            
            if elixir_needed <= 0:
                return 0.0
            
            regen_rate = self.DOUBLE_ELIXIR_RATE if self.double_elixir_mode else self.REGEN_RATE
            return elixir_needed / regen_rate
    
    def get_visual_bar(self, width=10):
        """
        Retorna barra visual do elixir
        
        Args:
            width: Largura da barra
            
        Returns:
            str: Barra formatada
        """
        with self.lock:
            current = max(0, self.opponent_elixir)
            filled = int((current / self.ELIXIR_MAX) * width)
            empty = width - filled
            
            bar = "⚡" * filled + "○" * empty
            mode = " (2x)" if self.double_elixir_mode else ""
            
            return f"[{bar}] {current:.1f}/10{mode}"


# Função auxiliar para usar no main.py
def create_elixir_tracker():
    """Cria e retorna uma nova instância do ElixirTracker"""
    return ElixirTracker()


# Teste do sistema
if __name__ == "__main__":
    import random
    
    print("="*60)
    print("🧪 TESTE DO ELIXIR TRACKER COM ANTI-SPAM")
    print("="*60)
    
    tracker = ElixirTracker()
    
    # Simula detecções com spam
    test_detections = [
        # Golem jogado (detecções múltiplas - SPAM)
        {'name': 'Golem', 'elixir': 8, 'confidence': 0.95},
        {'name': 'Golem', 'elixir': 8, 'confidence': 0.93},  # DUPLICATA
        {'name': 'Golem', 'elixir': 8, 'confidence': 0.94},  # DUPLICATA
        
        # Baby Dragon (detecções múltiplas - SPAM)
        {'name': 'Baby Dragon', 'elixir': 4, 'confidence': 0.88},
        {'name': 'Baby Dragon', 'elixir': 4, 'confidence': 0.90},  # DUPLICATA
        
        # Zap (carta rápida)
        {'name': 'Zap', 'elixir': 2, 'confidence': 0.85},
    ]
    
    print("\n📊 Simulando detecções com ANTI-SPAM...")
    
    for i, detection in enumerate(test_detections, 1):
        print(f"\n--- Detecção #{i} ---")
        print(f"Carta: {detection['name']} ({detection['elixir']}⚡) - {detection['confidence']:.0%}")
        
        # Passa lista com uma carta
        elixir = tracker.update([detection])
        
        print(f"Elixir estimado: {elixir}")
        print(tracker.get_visual_bar())
        
        # Simula tempo entre detecções
        time.sleep(0.3)
    
    # Aguarda regeneração
    print("\n\n⏳ Aguardando 3 segundos (regeneração)...")
    time.sleep(3)
    
    elixir = tracker.update([])  # Atualiza sem detecções
    print(f"Após regeneração: {elixir}")
    print(tracker.get_visual_bar())
    
    # Estatísticas
    print("\n" + "="*60)
    print("📊 ESTATÍSTICAS")
    print("="*60)
    stats = tracker.get_stats()
    print(f"Jogadas registradas: {stats['play_count']}")
    print(f"Elixir total gasto: {stats['total_spent']}")
    print(f"Custo médio: {stats['avg_cost']}⚡")
    
    print("\n🎯 Últimas jogadas:")
    for play in stats['recent_plays']:
        print(f"  • {play['card']} ({play['cost']}⚡) - {play['confidence']:.0%}")
    
    print("\n✅ TESTE CONCLUÍDO!")
    print(f"Total de detecções: {len(test_detections)}")
    print(f"Jogadas únicas registradas: {stats['play_count']}")
    print(f"Duplicatas filtradas: {len(test_detections) - stats['play_count']}")
    print("="*60)
