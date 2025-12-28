"""
deck_tracker.py
Rastreia o deck completo do oponente (8 cartas) e gerencia o ciclo de cartas
"""

import json
from datetime import datetime
from typing import List, Dict, Optional

class DeckTracker:
    def __init__(self, cards_db_path: str = "cards_db.json"):
        """
        Inicializa o rastreador de deck
        
        Args:
            cards_db_path: Caminho para o arquivo JSON com dados das cartas
        """
        self.cards_known: List[Dict] = []  # Cartas descobertas
        self.cycle_history: List[Dict] = []  # Histórico de cartas jogadas
        self.deck_complete: bool = False
        self.max_deck_size: int = 8
        
        # Carrega database de cartas
        with open(cards_db_path, 'r', encoding='utf-8') as f:
            self.cards_db = json.load(f)
        
        print("🎯 Deck Tracker iniciado!")
    
    def add_card(self, card_name: str) -> Dict:
        """
        Adiciona uma carta detectada ao rastreamento
        
        Args:
            card_name: Nome da carta detectada
            
        Returns:
            Dict com informações sobre a adição
        """
        # Busca informações da carta no database
        card_info = self._get_card_info(card_name)
        
        if not card_info:
            return {
                'success': False,
                'message': f'Carta {card_name} não encontrada no database'
            }
        
        # Adiciona ao histórico de ciclo
        play_info = {
            'card': card_name,
            'elixir_cost': card_info['elixir'],
            'timestamp': datetime.now().isoformat(),
            'cycle_position': len(self.cycle_history)
        }
        self.cycle_history.append(play_info)
        
        # Verifica se é uma carta nova no deck
        if not self._is_card_known(card_name):
            self.cards_known.append(card_info)
            
            # Verifica se completou o deck
            if len(self.cards_known) == self.max_deck_size:
                self.deck_complete = True
                print(f"\n✅ DECK COMPLETO REVELADO! ({self.max_deck_size} cartas)")
                self._print_deck()
            else:
                remaining = self.max_deck_size - len(self.cards_known)
                print(f"📊 Carta nova: {card_name} | Faltam {remaining} cartas")
            
            return {
                'success': True,
                'new_card': True,
                'cards_known': len(self.cards_known),
                'deck_complete': self.deck_complete
            }
        
        # Carta já conhecida
        return {
            'success': True,
            'new_card': False,
            'cards_known': len(self.cards_known),
            'deck_complete': self.deck_complete
        }
    
    def get_next_in_cycle(self, count: int = 4) -> List[Dict]:
        """
        Retorna as próximas cartas no ciclo
        
        Args:
            count: Quantas cartas mostrar (4 = mão atual)
            
        Returns:
            Lista com as próximas cartas no ciclo
        """
        if not self.deck_complete:
            return []
        
        # Calcula posição atual no ciclo
        total_plays = len(self.cycle_history)
        cycle_position = total_plays % self.max_deck_size
        
        # Monta lista de próximas cartas
        next_cards = []
        for i in range(count):
            card_index = (cycle_position + i) % self.max_deck_size
            next_cards.append(self.cards_known[card_index])
        
        return next_cards
    
    def get_current_hand(self) -> List[Dict]:
        """
        Retorna as 4 cartas que estão na mão do oponente agora
        
        Returns:
            Lista com as 4 cartas da mão atual
        """
        return self.get_next_in_cycle(4)
    
    def get_deck_archetype(self) -> str:
        """
        Identifica o arquétipo do deck baseado nas cartas
        
        Returns:
            Nome do arquétipo (Beatdown, Control, Cycle, etc)
        """
        if not self.deck_complete:
            return "Desconhecido"
        
        # Calcula custo médio de elixir
        avg_elixir = sum(c['elixir'] for c in self.cards_known) / len(self.cards_known)
        
        # Identifica cartas-chave
        win_conditions = ['Golem', 'Giant', 'Hog Rider', 'Royal Giant', 'X-Bow', 
                         'Mortar', 'Graveyard', 'Miner', 'Balloon', 'P.E.K.K.A']
        
        cycle_cards = ['Ice Spirit', 'Skeletons', 'The Log', 'Zap']
        
        has_win_con = any(c['name'] in win_conditions for c in self.cards_known)
        has_cycle = sum(1 for c in self.cards_known if c['name'] in cycle_cards) >= 2
        
        # Classifica arquétipo
        if avg_elixir > 4.0 and has_win_con:
            return "Beatdown"
        elif avg_elixir < 3.0 and has_cycle:
            return "Cycle"
        elif avg_elixir < 3.5:
            return "Fast Cycle"
        elif 'X-Bow' in [c['name'] for c in self.cards_known] or \
             'Mortar' in [c['name'] for c in self.cards_known]:
            return "Siege"
        elif has_win_con:
            return "Control"
        else:
            return "Hybrid"
    
    def get_stats(self) -> Dict:
        """
        Retorna estatísticas do deck rastreado
        
        Returns:
            Dict com estatísticas completas
        """
        if not self.cards_known:
            return {
                'cards_discovered': 0,
                'deck_complete': False
            }
        
        avg_elixir = sum(c['elixir'] for c in self.cards_known) / len(self.cards_known)
        
        return {
            'cards_discovered': len(self.cards_known),
            'deck_complete': self.deck_complete,
            'archetype': self.get_deck_archetype(),
            'avg_elixir': round(avg_elixir, 2),
            'total_plays': len(self.cycle_history),
            'cycle_position': len(self.cycle_history) % self.max_deck_size if self.deck_complete else 0
        }
    
    def reset(self):
        """Reseta o rastreador para uma nova partida"""
        self.cards_known = []
        self.cycle_history = []
        self.deck_complete = False
        print("🔄 Deck Tracker resetado para nova partida")
    
    def _is_card_known(self, card_name: str) -> bool:
        """Verifica se uma carta já está no deck conhecido"""
        return any(c['name'] == card_name for c in self.cards_known)
    
    def _get_card_info(self, card_name: str) -> Optional[Dict]:
        """Busca informações de uma carta no database"""
        for card in self.cards_db:
            if card['name'].lower() == card_name.lower():
                return card
        return None
    
    def _print_deck(self):
        """Imprime o deck completo formatado"""
        print("\n" + "="*50)
        print("📋 DECK COMPLETO DO OPONENTE")
        print("="*50)
        
        for i, card in enumerate(self.cards_known, 1):
            status = "JOGADA" if any(p['card'] == card['name'] for p in self.cycle_history) else "EM MÃO"
            print(f"{i}. {card['name']} ({card['elixir']} elixir) - {status}")
        
        avg_elixir = sum(c['elixir'] for c in self.cards_known) / len(self.cards_known)
        archetype = self.get_deck_archetype()
        
        print(f"\n📊 Custo médio: {avg_elixir:.2f} elixir")
        print(f"🎯 Arquétipo: {archetype}")
        print("="*50 + "\n")
    
    def export_to_json(self, filename: str = "opponent_deck.json"):
        """Exporta o deck atual para JSON"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'deck_complete': self.deck_complete,
            'cards': self.cards_known,
            'cycle_history': self.cycle_history,
            'stats': self.get_stats()
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Deck exportado para {filename}")


# Exemplo de uso
if __name__ == "__main__":
    # Teste do sistema
    tracker = DeckTracker()
    
    # Simula detecção de cartas durante uma partida
    test_cards = [
        "Golem", "Baby Dragon", "Night Witch", "Tornado",
        "Lightning", "Mega Minion", "Elixir Pump", "Guards",
        "Golem", "Baby Dragon"  # Cartas repetidas no ciclo
    ]
    
    for card in test_cards:
        print(f"\n🎮 Detectada: {card}")
        result = tracker.add_card(card)
        
        if tracker.deck_complete:
            next_cards = tracker.get_next_in_cycle(4)
            print(f"\n🔮 Próximas 4 cartas no ciclo:")
            for c in next_cards:
                print(f"  → {c['name']} ({c['elixir']} elixir)")
    
    # Mostra estatísticas finais
    print("\n" + "="*50)
    stats = tracker.get_stats()
    print("📊 ESTATÍSTICAS FINAIS:")
    print(f"  Cartas descobertas: {stats['cards_discovered']}/8")
    print(f"  Arquétipo: {stats['archetype']}")
    print(f"  Custo médio: {stats['avg_elixir']} elixir")
    print(f"  Total de jogadas: {stats['total_plays']}")
    print("="*50)
