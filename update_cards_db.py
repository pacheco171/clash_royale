import json
import os

# Mapeamento de nomes PT -> EN (apenas as cartas que faltam)
card_translations = {
    # Campeões que faltam
    "Goblinstein": "Goblinstein",
    "Boss Bandit": "Boss Bandit",
    
    # Lendárias que podem faltar
    "Spirit Empress": "Spirit Empress",
    "Goblin Machine": "Goblin Machine",
    "Domadora de Cordeiro": "Shepherd",
    
    # Épicas que podem faltar
    "Goblin Curse": "Goblin Curse",
    "Vines": "Vines",
    "Void": "Void",
    "Rune Giant": "Rune Giant",
    
    # Raras que podem faltar
    "Suspicious Bush": "Suspicious Bush",
    "Goblin Demolisher": "Goblin Demolisher",
    "Curadora Guerreira": "Battle Healer",
    "Eletrocutadores": "Zappies",
    "Corredor": "Royal Hogs",
    
    # Comuns que podem faltar
    "Berserker": "Berserker",
    "Patifes": "Rascals",
    "Dragões Esqueleto": "Skeleton Dragons",
    "Entrega real": "Royal Delivery",
    "Pirotécnica": "Firecracker"
}

# Cartas adicionais que podem estar faltando no seu JSON
missing_cards = [
    {"name": "Skeleton Dragons", "elixir": 4, "rarity": "Common", "type": "Troop", "hasEvolution": False},
    {"name": "Battle Healer", "elixir": 4, "rarity": "Rare", "type": "Troop", "hasEvolution": False},
    {"name": "Goblinstein", "elixir": 5, "rarity": "Champion", "type": "Troop", "hasEvolution": False, "hasHero": True, "isChampion": True},
    {"name": "Boss Bandit", "elixir": 6, "rarity": "Champion", "type": "Troop", "hasEvolution": False, "hasHero": True, "isChampion": True},
    {"name": "Spirit Empress", "elixir": 6, "rarity": "Legendary", "type": "Troop", "hasEvolution": False},
    {"name": "Goblin Machine", "elixir": 5, "rarity": "Legendary", "type": "Troop", "hasEvolution": False},
    {"name": "Shepherd", "elixir": 5, "rarity": "Legendary", "type": "Troop", "hasEvolution": False},
    {"name": "Berserker", "elixir": 2, "rarity": "Common", "type": "Troop", "hasEvolution": False},
    {"name": "Goblin Demolisher", "elixir": 4, "rarity": "Rare", "type": "Troop", "hasEvolution": False},
    {"name": "Suspicious Bush", "elixir": 2, "rarity": "Rare", "type": "Building", "hasEvolution": False},
    {"name": "Goblin Curse", "elixir": 2, "rarity": "Epic", "type": "Spell", "hasEvolution": False},
    {"name": "Vines", "elixir": 3, "rarity": "Epic", "type": "Spell", "hasEvolution": False},
    {"name": "Rune Giant", "elixir": 4, "rarity": "Epic", "type": "Troop", "hasEvolution": False}
]

def update_cards_json():
    """Atualiza o cards_db.json adicionando cartas que estão faltando"""
    
    json_path = "cards_db.json"
    backup_path = "cards_db_backup.json"
    
    # Ler arquivo existente
    if not os.path.exists(json_path):
        print(f"❌ Arquivo {json_path} não encontrado!")
        return
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Fazer backup
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ Backup criado: {backup_path}")
    
    # Verificar cartas existentes
    existing_names = {card['name'] for card in data['cards']}
    print(f"\n📊 Cartas existentes: {len(existing_names)}")
    
    # Adicionar cartas que faltam
    added = 0
    for card in missing_cards:
        if card['name'] not in existing_names:
            # Adicionar campos que podem faltar
            if 'hasHero' not in card:
                card['hasHero'] = False
            if 'isChampion' not in card:
                card['isChampion'] = card['rarity'] == 'Champion'
            
            data['cards'].append(card)
            print(f"  + Adicionada: {card['name']}")
            added += 1
    
    # Ordenar por elixir, depois por nome
    data['cards'].sort(key=lambda x: (x['elixir'], x['name']))
    
    # Salvar arquivo atualizado
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Arquivo atualizado: {json_path}")
    print(f"📈 Total de cartas: {len(data['cards'])}")
    print(f"➕ Cartas adicionadas: {added}")
    
    # Estatísticas por raridade
    rarities = {}
    for card in data['cards']:
        rarity = card['rarity']
        rarities[rarity] = rarities.get(rarity, 0) + 1
    
    print(f"\n📋 Estatísticas por raridade:")
    for rarity, count in sorted(rarities.items()):
        print(f"   - {rarity}: {count}")
    
    # Verificar cartas com evolução
    evolutions = sum(1 for card in data['cards'] if card.get('hasEvolution', False))
    print(f"\n⚡ Cartas com evolução: {evolutions}")
    
    return data

def verify_missing_cards():
    """Verifica quais cartas podem estar faltando comparando com a lista completa"""
    
    # Lista completa de cartas do Clash Royale (em inglês)
    all_cards_reference = {
        "Knight", "Archers", "Goblins", "Giant", "P.E.K.K.A", "Minions", "Balloon",
        "Witch", "Barbarians", "Golem", "Skeletons", "Valkyrie", "Skeleton Army",
        "Bomber", "Musketeer", "Baby Dragon", "Prince", "Wizard", "Mini P.E.K.K.A",
        "Spear Goblins", "Giant Skeleton", "Hog Rider", "Minion Horde", "Ice Wizard",
        "Royal Giant", "Guards", "Princess", "Dark Prince", "Three Musketeers",
        "Lava Hound", "Ice Spirit", "Fire Spirit", "Miner", "Sparky", "Bowler",
        "Lumberjack", "Battle Ram", "Inferno Dragon", "Ice Golem", "Mega Minion",
        "Dart Goblin", "Goblin Gang", "Electro Wizard", "Elite Barbarians",
        "Hunter", "Executioner", "Bandit", "Royal Recruits", "Night Witch",
        "Bats", "Royal Ghost", "Ram Rider", "Zappies", "Rascals", "Cannon Cart",
        "Mega Knight", "Skeleton Barrel", "Flying Machine", "Wall Breakers",
        "Royal Hogs", "Goblin Giant", "Fisherman", "Magic Archer", "Electro Dragon",
        "Electro Spirit", "Mother Witch", "Electro Giant", "Golden Knight",
        "Archer Queen", "Skeleton King", "Mighty Miner", "Phoenix", "Monk",
        "Little Prince", "Firecracker", "Goblin Drill", "Battle Healer",
        "Skeleton Dragons", "Goblinstein", "Boss Bandit", "Spirit Empress",
        "Goblin Machine", "Shepherd", "Berserker", "Goblin Demolisher",
        # Buildings
        "Cannon", "Goblin Hut", "Mortar", "Inferno Tower", "Bomb Tower",
        "Barbarian Hut", "Tesla", "Elixir Collector", "X-Bow", "Tombstone",
        "Furnace", "Goblin Cage", "Suspicious Bush",
        # Spells
        "Arrows", "Fireball", "Zap", "Poison", "Freeze", "Mirror", "Rage",
        "Lightning", "Rocket", "Goblin Barrel", "Tornado", "Clone", "Earthquake",
        "Barbarian Barrel", "Heal Spirit", "Giant Snowball", "Royal Delivery",
        "Graveyard", "The Log", "Void", "Goblin Curse", "Vines"
    }
    
    json_path = "cards_db.json"
    
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        existing_cards = {card['name'] for card in data['cards']}
        missing = all_cards_reference - existing_cards
        
        if missing:
            print(f"\n⚠️ Cartas que podem estar faltando ({len(missing)}):")
            for card in sorted(missing):
                print(f"   - {card}")
        else:
            print(f"\n✅ Todas as cartas principais estão no banco de dados!")

if __name__ == "__main__":
    print("🎮 Atualizador de cards_db.json - Clash Royale\n")
    print("="*50)
    
    # Atualizar arquivo
    update_cards_json()
    
    # Verificar se ainda falta algo
    print("\n" + "="*50)
    verify_missing_cards()
    
    print("\n✨ Processo concluído!")
    print("\n💡 Dica: O arquivo antigo foi salvo como 'cards_db_backup.json'")