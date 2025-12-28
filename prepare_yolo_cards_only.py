from pathlib import Path
import shutil
import random
import yaml

# Pasta com as imagens + labels (.txt) gerados
SOURCE_DIR = Path(r"C:\clash_royale\dataset\raw\video_jogo1")

# Pasta destino no formato YOLO
DATASET_DIR = Path(r"C:\clash_royale\dataset\yolo_cards")
IMAGES_TRAIN = DATASET_DIR / "images" / "train"
IMAGES_VAL = DATASET_DIR / "images" / "val"
LABELS_TRAIN = DATASET_DIR / "labels" / "train"
LABELS_VAL = DATASET_DIR / "labels" / "val"

# Classes (mesma ordem usada no auto_label_fixed_cards.py)
CLASSES = [
    "my_card",  # classe 0
]

VAL_SPLIT = 0.2  # 20% para validação


def main():
    # Cria as pastas
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_TRAIN.mkdir(parents=True, exist_ok=True)
    IMAGES_VAL.mkdir(parents=True, exist_ok=True)
    LABELS_TRAIN.mkdir(parents=True, exist_ok=True)
    LABELS_VAL.mkdir(parents=True, exist_ok=True)

    # Pega todas as imagens que têm label (.txt)
    images = sorted(SOURCE_DIR.glob("*.png"))
    labeled = [img for img in images if img.with_suffix(".txt").exists()]
    
    if not labeled:
        print(f"❌ Nenhuma imagem com label encontrada em {SOURCE_DIR}")
        print("Execute primeiro: py -3.11 auto_label_fixed_cards.py")
        return

    print(f"✅ {len(labeled)} imagens com labels encontradas.")

    # Embaralha e divide em train/val
    random.shuffle(labeled)
    n_val = int(len(labeled) * VAL_SPLIT)
    val_images = set(labeled[:n_val])

    train_count = 0
    val_count = 0

    for img_path in labeled:
        txt_path = img_path.with_suffix(".txt")

        if img_path in val_images:
            dst_img = IMAGES_VAL / img_path.name
            dst_lbl = LABELS_VAL / txt_path.name
            val_count += 1
        else:
            dst_img = IMAGES_TRAIN / img_path.name
            dst_lbl = LABELS_TRAIN / txt_path.name
            train_count += 1

        shutil.copy(img_path, dst_img)
        shutil.copy(txt_path, dst_lbl)

    print(f"📦 Train: {train_count} imagens")
    print(f"📦 Val: {val_count} imagens")

    # Cria data.yaml
    data_yaml = {
        "path": str(DATASET_DIR.resolve()),
        "train": "images/train",
        "val": "images/val",
        "names": {i: name for i, name in enumerate(CLASSES)},
    }

    yaml_path = DATASET_DIR / "data.yaml"
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(data_yaml, f, allow_unicode=True, default_flow_style=False)

    print(f"✅ Dataset YOLO preparado em: {DATASET_DIR}")
    print(f"📄 Arquivo de config: {yaml_path}")
    print("\n🚀 Próximo passo:")
    print(f"   py -3.11 -m ultralytics train model=yolov8n.pt data={yaml_path} epochs=20 imgsz=640")


if __name__ == "__main__":
    main()