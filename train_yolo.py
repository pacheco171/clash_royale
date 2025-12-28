"""
TREINAMENTO YOLO - Clash Royale
Script automatizado para treinar modelo YOLO
"""

import sys
from pathlib import Path
from ultralytics import YOLO

BASE_DIR = Path(__file__).resolve().parent
DATASET_DIR = BASE_DIR / "dataset" / "yolo"
DATA_YAML = DATASET_DIR / "data.yaml"

def train():
    if not DATA_YAML.exists():
        print("❌ data.yaml não encontrado!")
        print("Execute o annotator.py e clique em 'Exportar Dataset' primeiro.")
        sys.exit(1)
    
    print("🚀 Iniciando treinamento YOLO...")
    print(f"📁 Dataset: {DATASET_DIR}")
    
    # Carregar modelo base
    model = YOLO("yolov8n.pt")  # Nano (mais rápido)
    
    # Treinar
    results = model.train(
        data=str(DATA_YAML),
        epochs=100,              # Ajuste conforme necessário
        imgsz=640,
        batch=16,
        device=0,                # GPU (use 'cpu' se não tiver GPU)
        patience=20,             # Early stopping
        save=True,
        project=str(BASE_DIR / "runs"),
        name="clash_royale",
        exist_ok=True,
        
        # Otimizações
        cache=True,              # Cache imagens na RAM
        workers=4,
        amp=True,                # Mixed precision (mais rápido)
        
        # Augmentations (para dataset pequeno)
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=10,
        translate=0.1,
        scale=0.5,
        flipud=0.0,
        fliplr=0.5,
        mosaic=1.0,
    )
    
    print("\n✅ Treinamento concluído!")
    print(f"📁 Modelo salvo em: {BASE_DIR / 'runs' / 'clash_royale' / 'weights' / 'best.pt'}")
    print("\nPróximo passo:")
    print("1. Copie o arquivo 'best.pt' para 'yolo_clash_royale.pt'")
    print("2. Execute main_realtime.py")

if __name__ == "__main__":
    train()