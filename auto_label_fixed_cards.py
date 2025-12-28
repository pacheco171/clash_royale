from pathlib import Path
import cv2

# Pasta com as imagens brutas
RAW_DIR = Path(r"C:\clash_royale\dataset\raw\video_jogo1")

# Nome da classe (vai ser índice 0 no YOLO)
CLASS_ID = 0  # "my_card"

# >>>>> COORDENADAS NORMALIZADAS DOS SLOTS DE CARTA <<<<<
# Formato: (x1_norm, y1_norm, x2_norm, y2_norm)
# Valores de 0.0 a 1.0 (proporção da largura/altura da imagem)
# Baseado no layout padrão do Clash Royale (barra inferior)

CARD_SLOTS_NORMALIZED = [
    (0.24, 0.86, 0.34, 0.98),  # slot 1 (esquerda)
    (0.37, 0.86, 0.47, 0.98),  # slot 2
    (0.50, 0.86, 0.60, 0.98),  # slot 3
    (0.63, 0.86, 0.73, 0.98),  # slot 4 (direita)
]


def main():
    images = sorted(RAW_DIR.glob("*.png"))
    if not images:
        print(f"Nenhuma imagem encontrada em {RAW_DIR}")
        return

    print(f"{len(images)} imagens encontradas em {RAW_DIR}")

    for idx, img_path in enumerate(images, start=1):
        txt_path = img_path.with_suffix(".txt")

        # Se já tiver label, não sobrescreve
        if txt_path.exists():
            continue

        img = cv2.imread(str(img_path))
        if img is None:
            print(f"⚠️ Não foi possível ler {img_path.name}, pulando")
            continue

        h, w = img.shape[:2]

        lines = []
        for (x1_norm, y1_norm, x2_norm, y2_norm) in CARD_SLOTS_NORMALIZED:
            # Converte para pixels
            x1 = int(x1_norm * w)
            y1 = int(y1_norm * h)
            x2 = int(x2_norm * w)
            y2 = int(y2_norm * h)

            # Garante que está dentro da imagem
            x1 = max(0, min(x1, w - 1))
            x2 = max(0, min(x2, w - 1))
            y1 = max(0, min(y1, h - 1))
            y2 = max(0, min(y2, h - 1))

            if x2 <= x1 or y2 <= y1:
                continue

            # Converte para formato YOLO (centro + largura/altura normalizados)
            x_center = ((x1 + x2) / 2) / w
            y_center = ((y1 + y2) / 2) / h
            box_w = (x2 - x1) / w
            box_h = (y2 - y1) / h

            lines.append(
                f"{CLASS_ID} {x_center:.6f} {y_center:.6f} {box_w:.6f} {box_h:.6f}"
            )

        if lines:
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))

        if idx % 500 == 0:
            print(f"Labels gerados: {idx}/{len(images)}")

    print("✅ Labels automáticos gerados para todas as imagens.")


if __name__ == "__main__":
    main()