"""
elixir_tracker.py
Sistema completo de rastreamento de elixir do oponente
Inclui regeneração automática e cálculo preciso
"""

import time
import json
from typing import Dict, Optional

class ElixirTracker:
    def __init__(self, cards_db_path: str = "cards_db.json"):
        """
        Inicializa o rastreador de elixir
        
        Args:
            cards_db_path: Caminho para o arquivo com custos das cartas
        """
        # Configurações de elixir
        self.max_elixir: float = 10.0
        self.initial_elixir: float = 5.0
        self.regen_rate: float = 1.0  # +1 elixir por segundo
        self.double_elixir_rate: float = 2.0  # x2 Elixir
        
        # Estado atual
        self.current_elixir: float = self.initial_elixir
        self.last_update: float = time.time()
        self.double_elixir_mode: bool = False
        self.match_start_time: float = time.time()
        
        # Carrega custos das cartas
        self.card_costs: Dict[str, int] = {}
        self._load_card_costs(cards_db_path)
        
        # Histórico de gastos
        self.spending_history: list = []
        
        print(f"⚡ Elixir Tracker iniciado! Elixir inicial: {self.current_elixir}")
    
    def _load_card_costs(self, path: str):
        """Carrega os custos de elixir de cada carta"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                cards = json.load(f)
                for card in cards:
                    self.card_costs[card['name'].lower()] = card['elixir']
        except FileNotFoundError:
            print(f"⚠️ Arquivo {path} não encontrado. Usando custos padrão.")
            # Custos padrão de algumas cartas comuns
            self.card_costs = {
                'golem': 8, 'pekka': 7, 'mega knight': 7,
                'lightning': 6, 'rocket': 6, 'elixir pump': 6,
                'baby dragon': 4, 'wizard': 5, 'witch': 5,
                'hog rider': 4, 'valkyrie': 4, 'mini pekka': 4,
                'knight': 3, 'musketeer': 4, 'fireball': 4,
                'zap': 2, 'arrows': 3, 'log': 2,
                'skeletons': 1, 'ice spirit': 1
            }
    
    def update(self):
        """
        Atualiza o elixir baseado no tempo passado (regeneração)
        Deve ser chamado constantemente (loop principal)
        """
        current_time = time.time()
        time_passed = current_time - self.last_update
        
        # Calcula regeneração
        regen_amount = time_passed * (
            self.double_elixir_rate if self.double_elixir_mode 
            else self.regen_rate
        )
        
        # Atualiza elixir (max 10)
        self.current_elixir = min(
            self.max_elixir,
            self.current_elixir + regen_amount
        )
        
        self.last_update = current_time
    
    def card_played(self, card_name: str) -> Dict:
        """
        Registra que uma carta foi jogada e subtrai o elixir
        
        Args:
            card_name: Nome da carta jogada
            
        Returns:
            Dict com informações sobre o gasto
        """
        # Primeiro atualiza (regeneração até agora)
        self.update()
        
        # Busca custo da carta
        cost = self.card_costs.get(card_name.lower(), 0)
        
        if cost == 0:
            return {
                'success': False,
                'message': f'Carta {card_name} não encontrada',
                'current_elixir': self.current_elixir
            }
        
        # Subtrai o custo
        self.current_elixir -= cost
        
        # Registra no histórico
        self.spending_history.append({
            'card': card_name,
            'cost': cost,
            'timestamp': time.time(),
            'elixir_after': self.current_elixir
        })
        
        # Verifica se ficou negativo (empréstimo)
        borrowed = False
        if self.current_elixir < 0:
            borrowed = True
            print(f"💸 ELIXIR NEGATIVO! Oponente pegou emprestado {abs(self.current_elixir):.1f}")
        
        return {
            'success': True,
            'card': card_name,
            'cost': cost,
            'current_elixir': self.current_elixir,
            'borrowed': borrowed,
            'borrowed_amount': abs(self.current_elixir) if borrowed else 0
        }
    
    def get_current(self) -> float:
        """
        Retorna o elixir atual (com atualização automática)
        
        Returns:
            Quantidade atual de elixir
        """
        self.update()
        return max(0, self.current_elixir)  # Não mostra negativo
    
    def can_afford(self, card_name: str) -> bool:
        """
        Verifica se o oponente pode jogar determinada carta
        
        Args:
            card_name: Nome da carta
            
        Returns:
            True se tem elixir suficiente
        """
        cost = self.card_costs.get(card_name.lower(), 0)
        return self.get_current() >= cost
    
    def get_affordable_cards(self, deck_cards: list) -> list:
        """
        Retorna lista de cartas que o oponente pode jogar agora
        
        Args:
            deck_cards: Lista de cartas do deck (dicts com 'name' e 'elixir')
            
        Returns:
            Lista de cartas que podem ser jogadas
        """
        current = self.get_current()
        affordable = []
        
        for card in deck_cards:
            if card['elixir'] <= current:
                affordable.append(card)
        
        return affordable
    
    def enable_double_elixir(self):
        """Ativa modo de elixir duplo (último minuto)"""
        self.double_elixir_mode = True
        print("⚡⚡ MODO ELIXIR DUPLO ATIVADO! ⚡⚡")
    
    def disable_double_elixir(self):
        """Desativa modo de elixir duplo"""
        self.double_elixir_mode = False
    
    def reset(self):
        """Reseta o tracker para nova partida"""
        self.current_elixir = self.initial_elixir
        self.last_update = time.time()
        self.double_elixir_mode = False
        self.match_start_time = time.time()
        self.spending_history = []
        print("🔄 Elixir Tracker resetado")
    
    def get_stats(self) -> Dict:
        """
        Retorna estatísticas de uso de elixir
        
        Returns:
            Dict com estatísticas
        """
        if not self.spending_history:
            return {
                'current_elixir': self.get_current(),
                'total_spent': 0,
                'avg_cost_per_play': 0
            }
        
        total_spent = sum(play['cost'] for play in self.spending_history)
        avg_cost = total_spent / len(self.spending_history)
        
        match_duration = time.time() - self.match_start_time
        
        return {
            'current_elixir': round(self.get_current(), 1),
            'total_spent': total_spent,
            'total_plays': len(self.spending_history),
            'avg_cost_per_play': round(avg_cost, 2),
            'match_duration': round(match_duration, 1),
            'double_elixir_mode': self.double_elixir_mode
        }
    
    def get_visual_bar(self, width: int = 10) -> str:
        """
        Retorna uma barra visual do elixir
        
        Args:
            width: Largura da barra em caracteres
            
        Returns:
            String com a barra visual
        """
        current = self.get_current()
        filled = int((current / self.max_elixir) * width)
        empty = width - filled
        
        bar = "⚡" * filled + "○" * empty
        return f"[{bar}] {current:.1f}/{self.max_elixir}"
    
    def print_status(self):
        """Imprime status atual do elixir formatado"""
        current = self.get_current()
        bar = self.get_visual_bar(10)
        mode = " (2x ELIXIR)" if self.double_elixir_mode else ""
        
        print(f"\n⚡ Elixir Oponente: {bar}{mode}")


# Exemplo de uso
if __name__ == "__main__":
    import random
    
    print("="*60)
    print("🧪 TESTE DO ELIXIR TRACKER")
    print("="*60)
    
    tracker = ElixirTracker()
    
    # Simula uma partida
    test_cards = [
        ("Golem", 8),
        ("Baby Dragon", 4),
        ("Night Witch", 4),
        ("Zap", 2),
        ("Lightning", 6)
    ]
    
    print("\n📊 Simulando partida...")
    
    for i, (card, cost) in enumerate(test_cards, 1):
        print(f"\n--- JOGADA {i} ---")
        
        # Simula tempo passando (1-3 segundos entre jogadas)
        time.sleep(random.uniform(1, 3))
        
        # Mostra elixir antes
        print(f"Elixir antes: {tracker.get_current():.1f}")
        tracker.print_status()
        
        # Joga carta
        result = tracker.card_played(card)
        print(f"\n🃏 Jogou: {card} ({cost} elixir)")
        
        if result['borrowed']:
            print(f"⚠️ Pegou emprestado {result['borrowed_amount']:.1f} de elixir!")
        
        # Mostra elixir depois
        print(f"Elixir depois: {tracker.get_current():.1f}")
        tracker.print_status()
    
    # Simula regeneração
    print("\n\n⏳ Esperando 5 segundos (regeneração)...")
    time.sleep(5)
    tracker.update()
    tracker.print_status()
    
    # Ativa elixir duplo
    print("\n\n⚡⚡ ATIVANDO ELIXIR DUPLO...")
    tracker.enable_double_elixir()
    
    print("⏳ Esperando 3 segundos...")
    time.sleep(3)
    tracker.update()
    tracker.print_status()
    
    # Estatísticas finais
    print("\n\n" + "="*60)
    print("📊 ESTATÍSTICAS FINAIS")
    print("="*60)
    stats = tracker.get_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")
    print("="*60)
