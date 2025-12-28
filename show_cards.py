from pathlib import Path
import cv2

IMG_DIR = Path(r"C:\clash_royale\dataset\raw\video_jogo1")

current_index = 0
images = []

def mouse_event(event, x, y, flags, param):
    if event == cv2.EVENT_MOUSEMOVE:
        img, img_name = param
        img_copy = img.copy()
        text = f"x={x}, y={y}"
        cv2.putText(img_copy, text, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
        cv2.imshow("Coords Viewer", img_copy)

def show_image(idx):
    img_path = images[idx]
    img = cv2.imread(str(img_path))
    if img is None:
        print(f"Erro ao ler {img_path}")
        return None, None

    h, w = img.shape[:2]
    print(f"\nImagem {idx+1}/{len(images)}: {img_path.name}  (resolução: {w}x{h})")
    print("Use o mouse para ver x,y. Teclas: ← (A) anterior, → (D) próxima, ESC sai.")

    cv2.namedWindow("Coords Viewer", cv2.WINDOW_NORMAL)
    cv2.setMouseCallback("Coords Viewer", mouse_event, param=(img, img_path.name))
    cv2.imshow("Coords Viewer", img)
    return img, img_path

def main():
    global images, current_index

    images = sorted(IMG_DIR.glob("*.png"))
    if not images:
        print(f"Nenhuma imagem encontrada em {IMG_DIR}")
        return

    print(f"{len(images)} imagens encontradas em {IMG_DIR}")

    img, img_path = show_image(current_index)
    if img is None:
        return

    while True:
        key = cv2.waitKey(0) & 0xFF

        # ESC para sair
        if key == 27:
            break

        # tecla D ou seta direita -> próxima imagem
        if key in (ord('d'), ord('D'), 0x27):
            current_index = (current_index + 1) % len(images)
            img, img_path = show_image(current_index)

        # tecla A ou seta esquerda -> imagem anterior
        if key in (ord('a'), ord('A'), 0x25):
            current_index = (current_index - 1) % len(images)
            img, img_path = show_image(current_index)

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()