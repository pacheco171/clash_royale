"""
elixir_tracker.py
Sistema inteligente para rastrear elixir do oponente baseado em cartas jogadas
"""

import time
from collections import deque

class ElixirTracker:
    """
    Rastreia elixir do oponente baseado em:
    1. Cartas detectadas sendo jogadas
    2. Tempo passado (regeneração)
    3. Lógica do jogo
    """
    
    def __init__(self):
        # Estado do elixir
        self.opponent_elixir = 10.0  # Começa com 10
        self.last_update = time.time()
        
        # Taxa de regeneração
        self.REGEN_RATE = 1.0  # 1 elixir por segundo (normal)
        self.DOUBLE_REGEN_TIME = 120  # Depois de 2 minutos, dobra
        
        # Histórico de jogadas
        self.card_plays = deque(maxlen=20)
        self.last_card_time = {}  # {card_name: timestamp}
        
        # Anti-spam: evita contar mesma carta múltiplas vezes
        self.SPAM_THRESHOLD = 2.0  # segundos mínimos entre mesma carta
        
        # Tempo de partida
        self.match_start = time.time()
        
    def update(self, detected_cards):
        """
        Atualiza estado do elixir baseado em cartas detectadas
        
        Args:
            detected_cards: Lista de dicts com cartas detectadas
                           [{'name': 'Knight', 'confidence': 0.95, ...}, ...]
        """
        current_time = time.time()
        
        # 1. Adiciona regeneração natural
        elapsed = current_time - self.last_update
        match_time = current_time - self.match_start
        
        # Taxa de regeneração (dobra após 2 minutos)
        regen_rate = self.REGEN_RATE
        if match_time > self.DOUBLE_REGEN_TIME:
            regen_rate *= 2
        
        # Regenera elixir
        self.opponent_elixir += elapsed * regen_rate
        self.opponent_elixir = min(10.0, self.opponent_elixir)  # Cap em 10
        
        # 2. Processa cartas detectadas
        for card_dict in detected_cards:
            if not isinstance(card_dict, dict):
                continue
            
            card_name = card_dict.get('name')
            confidence = card_dict.get('confidence', 0)
            elixir_cost = card_dict.get('elixir', 0)
            
            if not card_name or elixir_cost == 0:
                continue
            
            # Anti-spam: verifica se já detectou essa carta recentemente
            last_time = self.last_card_time.get(card_name, 0)
            if current_time - last_time < self.SPAM_THRESHOLD:
                continue
            
            # Valida confiança mínima
            if confidence < 0.85:
                continue
            
            # Desconta elixir
            self.opponent_elixir -= elixir_cost
            self.opponent_elixir = max(0.0, self.opponent_elixir)
            
            # Registra jogada
            self.card_plays.append({
                'card': card_name,
                'cost': elixir_cost,
                'time': current_time,
                'confidence': confidence
            })
            
            self.last_card_time[card_name] = current_time
        
        self.last_update = current_time
        
        return int(round(self.opponent_elixir))
    
    def get_elixir(self):
        """Retorna elixir atual estimado"""
        # Atualiza com regeneração antes de retornar
        current_time = time.time()
        elapsed = current_time - self.last_update
        match_time = current_time - self.match_start
        
        regen_rate = self.REGEN_RATE
        if match_time > self.DOUBLE_REGEN_TIME:
            regen_rate *= 2
        
        estimated = self.opponent_elixir + (elapsed * regen_rate)
        estimated = min(10.0, estimated)
        
        return int(round(estimated))
    
    def get_recent_plays(self, count=5):
        """Retorna últimas N jogadas"""
        return list(self.card_plays)[-count:]
    
    def get_elixir_spent(self):
        """Retorna elixir total gasto pelo oponente"""
        return sum(play['cost'] for play in self.card_plays)
    
    def reset(self):
        """Reseta para nova partida"""
        self.opponent_elixir = 10.0
        self.last_update = time.time()
        self.match_start = time.time()
        self.card_plays.clear()
        self.last_card_time.clear()
    
    def set_match_start(self, timestamp=None):
        """Define início da partida manualmente"""
        self.match_start = timestamp or time.time()
    
    def force_set_elixir(self, value):
        """Define elixir manualmente (para correções)"""
        self.opponent_elixir = max(0.0, min(10.0, float(value)))
        self.last_update = time.time()


# ===== EXEMPLO DE USO =====
if __name__ == "__main__":
    tracker = ElixirTracker()
    
    print("🧪 Simulação de Rastreamento de Elixir\n")
    
    # Simula detecções
    detected_cards = [
        {'name': 'Knight', 'confidence': 0.95, 'elixir': 3},
    ]
    
    print(f"Elixir inicial: {tracker.get_elixir()}")
    
    # Primeira jogada
    elixir = tracker.update(detected_cards)
    print(f"Após Knight (3): {elixir}")
    
    # Aguarda regeneração
    time.sleep(2)
    print(f"Após 2s (regen): {tracker.get_elixir()}")
    
    # Segunda jogada
    detected_cards = [
        {'name': 'Fireball', 'confidence': 0.92, 'elixir': 4},
    ]
    elixir = tracker.update(detected_cards)
    print(f"Após Fireball (4): {elixir}")
    
    print(f"\nTotal gasto: {tracker.get_elixir_spent()} elixir")
    print(f"Jogadas recentes: {len(tracker.get_recent_plays())}")