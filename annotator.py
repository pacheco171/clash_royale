import cv2
import os
from pathlib import Path

# ===== CONFIGURAÇÕES =====

# Pasta onde estão suas imagens brutas
RAW_DIR = Path(r"C:\clash_royale\dataset\raw\video_jogo1")

# Arquivo com as classes (você pode editar depois)
CLASSES = [
    "card_giant",
    "card_musketeer",
    "card_archers",
    "troop_giant",
    "troop_musketeer",
    "troop_archers",
    # Adicione aqui as classes que você quer detectar
]

WINDOW_NAME = "Annotator - Clash Royale"
IMAGE_EXTENSIONS = [".png", ".jpg", ".jpeg"]


# ===== CÓDIGO =====

class AnnotationSession:
    def __init__(self, image_path, classes):
        self.image_path = image_path
        self.img = cv2.imread(str(image_path))
        if self.img is None:
            raise ValueError(f"Não foi possível ler a imagem {image_path}")

        self.h, self.w = self.img.shape[:2]
        self.clone = self.img.copy()
        self.classes = classes
        self.boxes = []  # lista de (x1, y1, x2, y2, class_id)
        self.drawing = False
        self.ix, self.iy = -1, -1
        self.current_class = 0

        # Se já existir anotação, carrega
        self.load_existing_annotation()

    def load_existing_annotation(self):
        txt_path = self.image_path.with_suffix(".txt")
        if not txt_path.exists():
            return
        with open(txt_path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) != 5:
                    continue
                cls_id = int(parts[0])
                x_center, y_center, w_norm, h_norm = map(float, parts[1:])
                x1 = int((x_center - w_norm / 2) * self.w)
                y1 = int((y_center - h_norm / 2) * self.h)
                x2 = int((x_center + w_norm / 2) * self.w)
                y2 = int((y_center + h_norm / 2) * self.h)
                self.boxes.append([x1, y1, x2, y2, cls_id])

    def mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.drawing = True
            self.ix, self.iy = x, y

        elif event == cv2.EVENT_MOUSEMOVE:
            if self.drawing:
                img_temp = self.clone.copy()
                cv2.rectangle(img_temp, (self.ix, self.iy), (x, y), (0, 255, 0), 2)
                self.draw_boxes(img_temp)
                cv2.imshow(WINDOW_NAME, img_temp)

        elif event == cv2.EVENT_LBUTTONUP:
            self.drawing = False
            x1, y1 = min(self.ix, x), min(self.iy, y)
            x2, y2 = max(self.ix, x), max(self.iy, y)
            self.boxes.append([x1, y1, x2, y2, self.current_class])
            self.refresh()

    def draw_boxes(self, img_draw):
        for (x1, y1, x2, y2, cls_id) in self.boxes:
            color = (0, 255, 0)
            cv2.rectangle(img_draw, (x1, y1), (x2, y2), color, 2)
            label = self.classes[cls_id]
            cv2.putText(img_draw, label, (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)

        class_info = f"Classe atual [{self.current_class}]: {self.classes[self.current_class]}"
        cv2.putText(img_draw, class_info, (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(img_draw, "Teclas: [0-9]=classe  DEL=remove ultima  S=salvar e prox  Q=salvar e sair",
                    (10, self.h - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

    def refresh(self):
        img_draw = self.clone.copy()
        self.draw_boxes(img_draw)
        cv2.imshow(WINDOW_NAME, img_draw)

    def save_annotations(self):
        txt_path = self.image_path.with_suffix(".txt")
        lines = []
        for (x1, y1, x2, y2, cls_id) in self.boxes:
            x_center = ((x1 + x2) / 2) / self.w
            y_center = ((y1 + y2) / 2) / self.h
            w_norm = (x2 - x1) / self.w
            h_norm = (y2 - y1) / self.h
            lines.append(
                f"{cls_id} {x_center:.6f} {y_center:.6f} {w_norm:.6f} {h_norm:.6f}"
            )
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"Anotações salvas em {txt_path}")


def get_image_list(raw_dir):
    images = []
    for root, _, files in os.walk(raw_dir):
        for f in sorted(files):
            if any(f.lower().endswith(ext) for ext in IMAGE_EXTENSIONS):
                images.append(Path(root) / f)
    return images


def main():
    images = get_image_list(RAW_DIR)
    if not images:
        print(f"Nenhuma imagem encontrada em {RAW_DIR}")
        return

    print(f"{len(images)} imagens encontradas. Começando anotação...")

    idx = 0
    total = len(images)
    while 0 <= idx < total:
        img_path = images[idx]
        print(f"[{idx+1}/{total}] {img_path}")

        session = AnnotationSession(img_path, CLASSES)

        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
        cv2.setMouseCallback(WINDOW_NAME, session.mouse_callback)
        session.refresh()

        while True:
            key = cv2.waitKey(0) & 0xFF

            # Teclas numéricas para trocar de classe
            if ord("0") <= key <= ord("9"):
                cls_id = key - ord("0")
                if cls_id < len(CLASSES):
                    session.current_class = cls_id
                    session.refresh()
                else:
                    print(f"Classe {cls_id} não existe (só {len(CLASSES)} classes)")
            # Delete: remove última box
            elif key in (8, 255):  # 8 = Backspace, 255 = DEL em alguns teclados
                if session.boxes:
                    session.boxes.pop()
                    session.refresh()
            # S = salvar e próxima
            elif key in (ord("s"), ord("S")):
                session.save_annotations()
                idx += 1
                break
            # A = voltar imagem anterior (sem salvar)
            elif key in (ord("a"), ord("A")):
                idx = max(0, idx - 1)
                break
            # Q = salvar e sair
            elif key in (ord("q"), ord("Q")):
                session.save_annotations()
                cv2.destroyAllWindows()
                print("Saindo...")
                return
            # ESC = sair sem salvar
            elif key == 27:
                cv2.destroyAllWindows()
                print("Saindo sem salvar a imagem atual...")
                return

        cv2.destroyAllWindows()

    print("Anotação concluída para todas as imagens.")


if __name__ == "__main__":
    main()