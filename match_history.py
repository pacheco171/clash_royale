"""Match History"""
import json
from pathlib import Path
from typing import Dict, List
from dataclasses import asdict
from datetime import datetime

class MatchHistory:
    def __init__(self, history_file: str = "match_history.json"):
        self.history_file = Path(history_file)
        self.current_match = []
        self.match_id = None

    def add_state(self, game_state, advice: Dict):
        entry = {'timestamp': game_state.timestamp, 'gameState': asdict(game_state), 'advice': advice}
        self.current_match.append(entry)

    def end_match(self, result: str = "unknown", notes: str = ""):
        if not self.current_match:
            return
        match_data = {
            'matchId': self.match_id or datetime.now().isoformat(),
            'result': result,
            'notes': notes,
            'states': self.current_match
        }
        history = self._load_history()
        history.append(match_data)
        self._save_history(history)
        self.current_match = []
        self.match_id = None

    def _load_history(self) -> List[Dict]:
        if not self.history_file.exists():
            return []
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []

    def _save_history(self, history: List[Dict]):
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Save error: {e}")
