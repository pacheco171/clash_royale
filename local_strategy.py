"""
ESTRATÉGIA LOCAL - Substitui Gemini
Sistema de decisão baseado em regras + ML simples
100% offline, latência < 50ms
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass

# ==== CONFIGURAÇÕES ====

BASE_DIR = Path(__file__).resolve().parent
CARDS_DB_PATH = BASE_DIR / "cards_db.json"

# Carregar database de cartas
def load_cards_db() -> Dict[str, Dict[str, Any]]:
    if not CARDS_DB_PATH.exists():
        return {}
    
    try:
        with open(CARDS_DB_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if isinstance(data, dict) and "cards" in data:
            cards_list = data["cards"]
        elif isinstance(data, list):
            cards_list = data
        else:
            return {}
        
        cards_db = {}
        for card in cards_list:
            name = card.get("name")
            if name:
                cards_db[name] = card
        
        return cards_db
    except:
        return {}

CARDS_DB = load_cards_db()

# ==== SISTEMA DE DECISÃO ====

@dataclass
class GameState:
    my_elixir: float
    opp_elixir: float
    my_cards: List[str]
    my_troops: List[str]
    opp_troops: List[str]
    my_tower_hp: int = 100
    opp_tower_hp: int = 100
    time_remaining: int = 180  # segundos

class LocalStrategy:
    def __init__(self):
        self.cards_db = CARDS_DB
        
        # Contadores de tipo
        self.troop_types = {
            "ground": ["Knight", "Valkyrie", "Mini P.E.K.K.A", "P.E.K.K.A", "Giant", "Golem"],
            "air": ["Minions", "Mega Minion", "Baby Dragon", "Balloon", "Lava Hound"],
            "swarm": ["Skeletons", "Goblins", "Goblin Gang", "Skeleton Army"],
            "building": ["Cannon", "Tesla", "Inferno Tower", "X-Bow"],
            "spell": ["Zap", "Fireball", "Lightning", "Rocket", "Arrows"]
        }
    
    def analyze(self, state: GameState) -> Tuple[str, str, int]:
        """
        Retorna: (sugestão, prioridade, confiança)
        """
        
        # 1. AMEAÇAS URGENTES
        if state.opp_troops:
            threat_level = self.calculate_threat(state.opp_troops)
            
            if threat_level >= 8:
                counter = self.find_counter(state.opp_troops, state.my_cards, state.my_elixir)
                if counter:
                    return (
                        f"🚨 URGENTE: Jogue {counter} para defender!",
                        "urgent",
                        95
                    )
                else:
                    return (
                        f"🚨 Ameaça crítica! Defenda com qualquer carta disponível!",
                        "urgent",
                        90
                    )
        
        # 2. VANTAGEM DE ELIXIR
        elixir_diff = state.my_elixir - state.opp_elixir
        
        if elixir_diff >= 3 and state.my_elixir >= 7:
            # Ataque pesado
            heavy_card = self.find_heavy_card(state.my_cards)
            if heavy_card:
                return (
                    f"⚡ Vantagem de elixir! Ataque com {heavy_card}",
                    "high",
                    85
                )
        
        # 3. ELIXIR CHEIO
        if state.my_elixir >= 9.5:
            cheapest = self.find_cheapest_card(state.my_cards)
            if cheapest:
                return (
                    f"⚠️ Elixir cheio! Jogue {cheapest} para não desperdiçar",
                    "medium",
                    80
                )
        
        # 4. PRESSÃO CONSTANTE
        if not state.opp_troops and state.my_elixir >= 5:
            if state.opp_tower_hp < 50:
                # Torre baixa, pressionar
                spell = self.find_spell(state.my_cards)
                if spell:
                    return (
                        f"🎯 Torre baixa! Use {spell} para finalizar",
                        "high",
                        90
                    )
            
            # Pressão normal
            pressure_card = self.find_pressure_card(state.my_cards, state.my_elixir)
            if pressure_card:
                return (
                    f"➡️ Pressione com {pressure_card}",
                    "medium",
                    70
                )
        
        # 5. ECONOMIA
        if state.my_elixir < 4:
            return (
                "⏳ Aguarde elixir regenerar",
                "low",
                60
            )
        
        # 6. PADRÃO
        return (
            "👀 Monitore o oponente e prepare defesa",
            "low",
            50
        )
    
    def calculate_threat(self, opp_troops: List[str]) -> int:
        """Calcula nível de ameaça (0-10)"""
        threat = 0
        
        for troop in opp_troops:
            card_info = self.cards_db.get(troop, {})
            elixir = card_info.get("elixir", 0)
            
            # Tropas caras = mais ameaça
            threat += elixir
            
            # Tipos específicos
            if troop in ["Balloon", "Hog Rider", "Royal Giant"]:
                threat += 3  # Ameaça direta à torre
            
            if troop in ["Golem", "Lava Hound", "Giant"]:
                threat += 2  # Tanques
        
        return min(10, threat)
    
    def find_counter(self, opp_troops: List[str], my_cards: List[str], my_elixir: float) -> str:
        """Encontra melhor carta para contra-atacar"""
        
        # Detectar tipo de ameaça
        has_air = any(t in self.troop_types["air"] for t in opp_troops)
        has_swarm = any(t in self.troop_types["swarm"] for t in opp_troops)
        has_tank = any(t in ["Golem", "Giant", "P.E.K.K.A", "Lava Hound"] for t in opp_troops)
        
        for card in my_cards:
            card_info = self.cards_db.get(card, {})
            elixir = card_info.get("elixir", 0)
            
            if elixir > my_elixir:
                continue
            
            card_type = card_info.get("type", "")
            
            # Counters específicos
            if has_swarm and card in ["Zap", "Arrows", "Log", "Valkyrie"]:
                return card
            
            if has_air and card in ["Musketeer", "Mega Minion", "Tesla", "Inferno Dragon"]:
                return card
            
            if has_tank and card in ["Inferno Tower", "Inferno Dragon", "Mini P.E.K.K.A"]:
                return card
        
        # Fallback: carta mais barata
        return self.find_cheapest_card(my_cards)
    
    def find_heavy_card(self, my_cards: List[str]) -> str:
        """Encontra carta pesada para ataque"""
        heavy = []
        for card in my_cards:
            card_info = self.cards_db.get(card, {})
            elixir = card_info.get("elixir", 0)
            if elixir >= 5:
                heavy.append((card, elixir))
        
        if heavy:
            heavy.sort(key=lambda x: x[1], reverse=True)
            return heavy[0][0]
        
        return ""
    
    def find_cheapest_card(self, my_cards: List[str]) -> str:
        """Encontra carta mais barata"""
        cheapest = None
        min_elixir = 999
        
        for card in my_cards:
            card_info = self.cards_db.get(card, {})
            elixir = card_info.get("elixir", 0)
            if elixir < min_elixir:
                min_elixir = elixir
                cheapest = card
        
        return cheapest or ""
    
    def find_spell(self, my_cards: List[str]) -> str:
        """Encontra spell para finalizar torre"""
        for card in my_cards:
            if card in self.troop_types["spell"]:
                return card
        return ""
    
    def find_pressure_card(self, my_cards: List[str], my_elixir: float) -> str:
        """Encontra carta para pressionar"""
        pressure = []
        
        for card in my_cards:
            card_info = self.cards_db.get(card, {})
            elixir = card_info.get("elixir", 0)
            
            if 3 <= elixir <= 5 and elixir <= my_elixir:
                # Cartas médias são boas para pressão
                if card in ["Hog Rider", "Miner", "Battle Ram", "Ram Rider"]:
                    return card  # Prioridade
                pressure.append(card)
        
        return pressure[0] if pressure else ""

# ==== TESTE ====

if __name__ == "__main__":
    strategy = LocalStrategy()
    
    # Teste 1: Ameaça urgente
    state = GameState(
        my_elixir=6.0,
        opp_elixir=2.0,
        my_cards=["Zap", "Fireball", "Knight", "Musketeer"],
        my_troops=[],
        opp_troops=["Skeleton Army", "Goblin Gang"]
    )
    
    suggestion, priority, confidence = strategy.analyze(state)
    print(f"Teste 1: {suggestion} [{priority}] ({confidence}%)")
    
    # Teste 2: Vantagem de elixir
    state = GameState(
        my_elixir=9.0,
        opp_elixir=3.0,
        my_cards=["Giant", "Hog Rider", "Zap", "Fireball"],
        my_troops=[],
        opp_troops=[]
    )
    
    suggestion, priority, confidence = strategy.analyze(state)
    print(f"Teste 2: {suggestion} [{priority}] ({confidence}%)")
    
    # Teste 3: Elixir baixo
    state = GameState(
        my_elixir=2.0,
        opp_elixir=5.0,
        my_cards=["Giant", "Hog Rider", "Zap", "Fireball"],
        my_troops=[],
        opp_troops=[]
    )
    
    suggestion, priority, confidence = strategy.analyze(state)
    print(f"Teste 3: {suggestion} [{priority}] ({confidence}%)")