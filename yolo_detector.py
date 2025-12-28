"""
yolo_detector.py
Detecção de cartas usando YOLO (opcional)
"""

import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import numpy as np

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False


class YOLODetector:
    def __init__(self, model_path: str = "yolo_clash_royale.pt"):
        """
        Inicializa o detector YOLO.
        
        Args:
            model_path: Caminho para o modelo YOLO treinado (padrão: model_path fornecido ou None)
        """
        self.model = None
        self.model_path = model_path
        
        if not YOLO_AVAILABLE:
            print("⚠️ ultralytics não instalado. YOLO desabilitado.")
            print("   Para habilitar: pip install ultralytics")
            return
        
        if not model_path or not Path(model_path).exists():
            print(f"⚠️ Modelo YOLO não encontrado em: {model_path}")
            print("   YOLO desabilitado. Treine um modelo ou baixe um pré-treinado.")
            return
        
        try:
            self.model = YOLO(model_path)
            print(f"✅ Modelo YOLO carregado: {model_path}")
        except Exception as e:
            print(f"❌ Erro ao carregar YOLO: {e}")
            self.model = None

        # Regiões da tela (ajuste conforme necessário)
        self.regions = {
            "myCards": (0, 0.85, 1, 1),           # Bottom 15% - suas cartas
            "myTroops": (0, 0.5, 1, 0.85),        # Seu lado do campo
            "opponentTroops": (0, 0.15, 1, 0.5),  # Lado do oponente
        }

    def detect(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Detecta cartas e tropas na imagem.
        
        Args:
            image: Imagem em formato numpy array (RGB)
        
        Returns:
            Dicionário com detecções:
            {
                "myCards": ["Knight", "Archers", ...],
                "myTroopsOnField": ["Giant", ...],
                "opponentTroopsOnField": ["PEKKA", ...],
                "opponentLastPlay": "Fireball" ou None
            }
        """
        if self.model is None:
            return {
                "myCards": [],
                "myTroopsOnField": [],
                "opponentTroopsOnField": [],
                "opponentLastPlay": None,
            }

        try:
            h, w = image.shape[:2]
            results = {
                "myCards": [],
                "myTroopsOnField": [],
                "opponentTroopsOnField": [],
                "opponentLastPlay": None,
            }

            # Detectar em cada região
            for region_name, (x1, y1, x2, y2) in self.regions.items():
                x1_px = int(x1 * w)
                y1_px = int(y1 * h)
                x2_px = int(x2 * w)
                y2_px = int(y2 * h)

                roi = image[y1_px:y2_px, x1_px:x2_px]
                
                if roi.size == 0:
                    continue

                detections = self.model(roi, verbose=False)

                for det in detections:
                    if det.boxes is None:
                        continue
                    
                    for box in det.boxes:
                        cls_id = int(box.cls[0])
                        conf = float(box.conf[0])
                        
                        if conf < 0.5:  # Threshold de confiança
                            continue
                        
                        # Obter nome da classe
                        card_name = self.model.names.get(cls_id, f"unknown_{cls_id}")

                        if region_name == "myCards":
                            if card_name not in results["myCards"]:
                                results["myCards"].append(card_name)
                        elif region_name == "myTroops":
                            if card_name not in results["myTroopsOnField"]:
                                results["myTroopsOnField"].append(card_name)
                        elif region_name == "opponentTroops":
                            if card_name not in results["opponentTroopsOnField"]:
                                results["opponentTroopsOnField"].append(card_name)

            # Última jogada do oponente (carta mais recente detectada)
            if results["opponentTroopsOnField"]:
                results["opponentLastPlay"] = results["opponentTroopsOnField"][-1]

            return results

        except Exception as e:
            print(f"❌ Erro no YOLO detect: {e}")
            return {
                "myCards": [],
                "myTroopsOnField": [],
                "opponentTroopsOnField": [],
                "opponentLastPlay": None,
            }

    def is_available(self) -> bool:
        """Retorna True se o YOLO está disponível e carregado."""
        return self.model is not None
