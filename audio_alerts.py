from pathlib import Path
from PyQt6.QtMultimedia import QSoundEffect
from PyQt6.QtCore import QUrl


class AudioAlerts:
    def __init__(self, sounds_dir: str):
        self.sounds_dir = Path(sounds_dir)

        self.sounds = {
            "high": QSoundEffect(),
            "medium": QSoundEffect(),
            "match_end": QSoundEffect(),
        }

        # Arquivos de som ESPERADOS (nomes corrigidos)
        self._load_sound("high", "high_priority.wav")
        self._load_sound("medium", "medium_priority.wav")
        self._load_sound("match_end", "match_end.wav")

    def _load_sound(self, key: str, filename: str):
        path = self.sounds_dir / filename
        if not path.exists():
            print(f"⚠️ Sound file not found: {path}")
            return

        effect = self.sounds[key]
        effect.setSource(QUrl.fromLocalFile(str(path)))
        effect.setVolume(0.8)

    def play_priority(self, level: str):
        """
        level: 'low', 'medium', 'high'
        """
        if level is None:
            return

        level = level.lower()
        if level == "high":
            snd = self.sounds.get("high")
            if snd and snd.source().isLocalFile():
                snd.play()
        elif level == "medium":
            snd = self.sounds.get("medium")
            if snd and snd.source().isLocalFile():
                snd.play()
        # low = sem som para não ficar chato demais

    def play_match_end(self):
        snd = self.sounds.get("match_end")
        if snd and snd.source().isLocalFile():
            snd.play()