"""
strategy_predictor.py
Sistema inteligente de previsão de jogadas e sugestão de counters
"""

from typing import List, Dict, Tuple, Optional


class StrategyPredictor:
    """Prevê jogadas do oponente e sugere estratégias"""
    
    def __init__(self):
        """Inicializa o previsor de estratégias"""
        
        # Database de counters
        self.counters = {
            # Win Conditions
            'Golem': ['Inferno Tower', 'Inferno Dragon', 'P.E.K.K.A', 'Mini P.E.K.K.A'],
            'Giant': ['Inferno Tower', 'Inferno Dragon', 'Mini P.E.K.K.A', 'Cannon'],
            'Hog Rider': ['Tornado', 'Cannon', 'Tesla', 'Mini P.E.K.K.A'],
            'X-Bow': ['Lightning', 'Earthquake', 'Rocket', 'Giant'],
            'Balloon': ['Inferno Dragon', 'Mega Minion', 'Musketeer', 'Wizard'],
            'P.E.K.K.A': ['Inferno Tower', 'Swarm', 'Kiting'],
            
            # Spells
            'Lightning': ['Spread units', 'Bait with cheap troops'],
            'Rocket': ['Spread towers', 'Pressure opposite lane'],
            'Fireball': ['Bait with cheap troops', 'Space units'],
            'Poison': ['Quick pushes', 'Escape poison area'],
            
            # Support
            'Baby Dragon': ['Mega Minion', 'Musketeer', 'Air defense'],
            'Wizard': ['Lightning', 'Fireball', 'Snipe with Musketeer'],
            'Witch': ['Valkyrie', 'Poison', 'Lightning'],
            
            # Swarm
            'Goblin Gang': ['Log', 'Zap', 'Arrows'],
            'Skeleton Army': ['Log', 'Zap', 'Arrows'],
            'Minion Horde': ['Arrows', 'Fireball', 'Wizard']
        }
        
        # Cartas perigosas por categoria
        self.dangerous_cards = {
            'damage_spells': ['Lightning', 'Rocket', 'Fireball', 'Poison'],
            'win_conditions': ['Golem', 'Giant', 'Hog Rider', 'Balloon', 'X-Bow'],
            'splash_damage': ['Baby Dragon', 'Wizard', 'Valkyrie', 'Bomber'],
            'reset_cards': ['Zap', 'Lightning', 'Electro Wizard'],
            'cycle_cards': ['Ice Spirit', 'Skeletons', 'Log']
        }
        
        # Synergies conhecidas
        self.synergies = [
            ['Golem', 'Baby Dragon', 'Night Witch'],
            ['Giant', 'Graveyard'],
            ['Hog Rider', 'Freeze'],
            ['X-Bow', 'Tesla', 'Ice Golem'],
            ['Balloon', 'Lumberjack'],
            ['Miner', 'Poison'],
            ['Royal Giant', 'Furnace']
        ]
    
    def predict_next_play(
        self, 
        current_hand: List[Dict],
        elixir_available: float,
        game_situation: str = 'normal'
    ) -> Dict:
        """
        Prevê a próxima jogada mais provável do oponente
        
        Args:
            current_hand: Cartas na mão do oponente
            elixir_available: Elixir disponível
            game_situation: Situação do jogo ('defending', 'attacking', 'normal')
            
        Returns:
            Dict com previsão e probabilidades
        """
        affordable_cards = [c for c in current_hand if c['elixir'] <= elixir_available]
        
        if not affordable_cards:
            return {
                'prediction': None,
                'message': 'Nenhuma carta disponível',
                'wait_time': self._calculate_wait_time(current_hand, elixir_available)
            }
        
        # Pontua cada carta baseado na situação
        scored_cards = []
        for card in affordable_cards:
            score = self._score_card(card, game_situation, current_hand)
            scored_cards.append({
                'card': card,
                'score': score,
                'probability': 0  # Será calculado depois
            })
        
        # Normaliza probabilidades
        total_score = sum(c['score'] for c in scored_cards)
        for card_data in scored_cards:
            card_data['probability'] = (card_data['score'] / total_score) * 100
        
        # Ordena por probabilidade
        scored_cards.sort(key=lambda x: x['probability'], reverse=True)
        
        most_likely = scored_cards[0]
        
        return {
            'prediction': most_likely['card']['name'],
            'probability': round(most_likely['probability'], 1),
            'all_possibilities': scored_cards,
            'situation': game_situation
        }
    
    def _score_card(
        self, 
        card: Dict, 
        situation: str,
        full_hand: List[Dict]
    ) -> float:
        """
        Calcula score de probabilidade para uma carta
        
        Args:
            card: Carta a pontuar
            situation: Situação do jogo
            full_hand: Mão completa (para detectar combos)
            
        Returns:
            Score da carta
        """
        score = 1.0
        card_name = card['name']
        
        # Ajuste baseado na situação
        if situation == 'defending':
            # Prioriza defesa
            defensive_cards = ['Cannon', 'Tesla', 'Inferno Tower', 'Mini P.E.K.K.A']
            if card_name in defensive_cards:
                score *= 2.0
            
            # Spells defensivos
            if card_name in ['Tornado', 'Zap', 'Log']:
                score *= 1.5
        
        elif situation == 'attacking':
            # Prioriza win conditions
            if card_name in self.dangerous_cards['win_conditions']:
                score *= 2.5
            
            # Suporte ao ataque
            if card_name in self.dangerous_cards['splash_damage']:
                score *= 1.8
        
        # Detecta combos possíveis
        combo_bonus = self._check_combo_potential(card_name, full_hand)
        score *= (1 + combo_bonus)
        
        # Ajuste por custo (cartas mais baratas = mais prováveis em emergências)
        if card['elixir'] <= 3:
            score *= 1.2
        
        return score
    
    def _check_combo_potential(
        self, 
        card_name: str, 
        hand: List[Dict]
    ) -> float:
        """
        Verifica se a carta faz parte de um combo conhecido
        
        Args:
            card_name: Nome da carta
            hand: Cartas na mão
            
        Returns:
            Bônus de score (0.0 a 1.0)
        """
        hand_names = [c['name'] for c in hand]
        
        for synergy in self.synergies:
            if card_name in synergy:
                # Verifica quantas cartas do combo estão na mão
                combo_cards_in_hand = sum(1 for c in synergy if c in hand_names)
                if combo_cards_in_hand >= 2:
                    return 0.5  # Forte indicação de combo
        
        return 0.0
    
    def _calculate_wait_time(
        self, 
        hand: List[Dict], 
        current_elixir: float
    ) -> Dict:
        """
        Calcula quanto tempo até próxima carta disponível
        
        Args:
            hand: Cartas na mão
            current_elixir: Elixir atual
            
        Returns:
            Dict com informações de espera
        """
        # Carta mais barata
        cheapest = min(hand, key=lambda x: x['elixir'])
        elixir_needed = cheapest['elixir'] - current_elixir
        
        if elixir_needed <= 0:
            return {
                'card': cheapest['name'],
                'wait_seconds': 0
            }
        
        # Tempo de espera (1 elixir/segundo)
        wait_seconds = elixir_needed
        
        return {
            'card': cheapest['name'],
            'elixir_needed': elixir_needed,
            'wait_seconds': round(wait_seconds, 1)
        }
    
    def suggest_counters(self, card_name: str) -> List[str]:
        """
        Sugere counters para uma carta
        
        Args:
            card_name: Nome da carta a counterar
            
        Returns:
            Lista de counters sugeridos
        """
        return self.counters.get(card_name, ['Counter genérico: Defesa adequada'])
    
    def analyze_deck_threats(self, opponent_deck: List[Dict]) -> Dict:
        """
        Analisa as maiores ameaças do deck oponente
        
        Args:
            opponent_deck: Deck completo do oponente
            
        Returns:
            Dict com análise de ameaças
        """
        threats = {
            'critical': [],
            'high': [],
            'medium': []
        }
        
        deck_names = [c['name'] for c in opponent_deck]
        
        # Identifica ameaças críticas
        for card in opponent_deck:
            if card['name'] in self.dangerous_cards['damage_spells']:
                if card['elixir'] >= 6:
                    threats['critical'].append({
                        'card': card['name'],
                        'reason': 'Spell de alto dano',
                        'counters': self.suggest_counters(card['name'])
                    })
            
            if card['name'] in self.dangerous_cards['win_conditions']:
                threats['high'].append({
                    'card': card['name'],
                    'reason': 'Win condition',
                    'counters': self.suggest_counters(card['name'])
                })
        
        # Detecta combos perigosos
        detected_combos = []
        for synergy in self.synergies:
            combo_cards = [c for c in synergy if c in deck_names]
            if len(combo_cards) >= 2:
                detected_combos.append(combo_cards)
        
        return {
            'threats': threats,
            'combos': detected_combos,
            'overall_danger': self._calculate_danger_level(threats, detected_combos)
        }
    
    def _calculate_danger_level(
        self, 
        threats: Dict, 
        combos: List
    ) -> str:
        """Calcula nível geral de perigo do deck"""
        critical_count = len(threats['critical'])
        high_count = len(threats['high'])
        combo_count = len(combos)
        
        danger_score = (critical_count * 3) + (high_count * 2) + (combo_count * 1.5)
        
        if danger_score >= 8:
            return 'MUITO ALTO'
        elif danger_score >= 5:
            return 'ALTO'
        elif danger_score >= 3:
            return 'MÉDIO'
        else:
            return 'BAIXO'
    
    def suggest_gameplay_strategy(
        self, 
        opponent_deck: List[Dict],
        archetype: str
    ) -> Dict:
        """
        Sugere estratégia geral contra o deck
        
        Args:
            opponent_deck: Deck do oponente
            archetype: Arquétipo do deck
            
        Returns:
            Dict com sugestões estratégicas
        """
        strategies = {
            'Beatdown': {
                'approach': 'Defensiva e counter-push',
                'tips': [
                    'Defenda eficientemente no seu lado',
                    'Não deixe acumular elixir (Pump)',
                    'Counter-push na outra lane',
                    'Save spells para suporte dele'
                ]
            },
            'Cycle': {
                'approach': 'Controle de ritmo',
                'tips': [
                    'Não deixe ciclar rápido demais',
                    'Pressione constantemente',
                    'Mantenha elixir advantage',
                    'Defenda com custo baixo'
                ]
            },
            'Control': {
                'approach': 'Trocar elixir positivamente',
                'tips': [
                    'Evite commitments grandes',
                    'Faça trades positivos',
                    'Cuidado com spells',
                    'Pressione no timing certo'
                ]
            },
            'Siege': {
                'approach': 'Pressão constante',
                'tips': [
                    'Nunca deixe buildar',
                    'Pressione mesma lane',
                    'Use tanques para tankar',
                    'Guarde spell para siege'
                ]
            }
        }
        
        base_strategy = strategies.get(archetype, strategies['Control'])
        
        # Adiciona alertas específicos do deck
        threats = self.analyze_deck_threats(opponent_deck)
        
        return {
            'archetype': archetype,
            'approach': base_strategy['approach'],
            'tips': base_strategy['tips'],
            'key_threats': threats['threats']['critical'] + threats['threats']['high'],
            'danger_level': threats['overall_danger']
        }


# Exemplo de uso
if __name__ == "__main__":
    predictor = StrategyPredictor()
    
    # Simula mão do oponente
    test_hand = [
        {'name': 'Golem', 'elixir': 8},
        {'name': 'Baby Dragon', 'elixir': 4},
        {'name': 'Lightning', 'elixir': 6},
        {'name': 'Zap', 'elixir': 2}
    ]
    
    print("="*60)
    print("🧠 TESTE DO STRATEGY PREDICTOR")
    print("="*60)
    
    # Teste 1: Previsão com pouco elixir
    print("\n📊 TESTE 1: Oponente com 3 de elixir")
    prediction = predictor.predict_next_play(test_hand, 3.0, 'normal')
    print(f"Previsão: {prediction['prediction']}")
    print(f"Probabilidade: {prediction['probability']}%")
    
    # Teste 2: Previsão defendendo
    print("\n📊 TESTE 2: Oponente com 10 de elixir (defendendo)")
    prediction = predictor.predict_next_play(test_hand, 10.0, 'defending')
    print(f"Previsão: {prediction['prediction']}")
    print(f"Probabilidade: {prediction['probability']}%")
    
    # Teste 3: Counters
    print("\n📊 TESTE 3: Counters para Golem")
    counters = predictor.suggest_counters('Golem')
    print(f"Counters: {', '.join(counters)}")
    
    # Teste 4: Análise de deck
    print("\n📊 TESTE 4: Análise de ameaças")
    full_deck = test_hand + [
        {'name': 'Night Witch', 'elixir': 4},
        {'name': 'Tornado', 'elixir': 3},
        {'name': 'Mega Minion', 'elixir': 3},
        {'name': 'Guards', 'elixir': 3}
    ]
    
    analysis = predictor.analyze_deck_threats(full_deck)
    print(f"Nível de perigo: {analysis['overall_danger']}")
    print(f"Combos detectados: {analysis['combos']}")
    
    print("\n" + "="*60)
