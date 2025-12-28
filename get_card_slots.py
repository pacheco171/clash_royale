import cv2
import numpy as np
import mss

# Se você souber a região exata do Bluestacks, coloque aqui.
# Senão, deixe None para capturar a tela inteira.
SCREEN_REGION = None  # ou {"top": 0, "left": 0, "width": 1920, "height": 1080}

def main():
    with mss.mss() as sct:
        if SCREEN_REGION:
            monitor = SCREEN_REGION
        else:
            monitor = sct.monitors[1]  # monitor principal

        print(f"Capturando região: {monitor}")
        print("Abra o Clash Royale no Bluestacks e entre em uma partida.")
        print("Pressione ENTER quando estiver pronto...")
        input()

        # Captura a tela
        screenshot = sct.grab(monitor)
        img = np.array(screenshot)
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

        h, w = img.shape[:2]
        print(f"Resolução capturada: {w}x{h}")
        print("\nInstruções:")
        print("  1) Clique no CANTO SUPERIOR ESQUERDO das 4 cartas (ordem: 1, 2, 3, 4)")
        print("  2) Depois clique no CANTO INFERIOR DIREITO das 4 cartas (ordem: 1, 2, 3, 4)")
        print("  3) Total: 8 cliques")
        print("  ESC para cancelar\n")

        clicks = []

        def mouse_cb(event, x, y, flags, param):
            nonlocal clicks
            if event == cv2.EVENT_LBUTTONDOWN:
                clicks.append((x, y))
                print(f"Clique {len(clicks)}: x={x}, y={y}")
                # Desenha um círculo no clique
                cv2.circle(img, (x, y), 5, (0, 255, 0), -1)
                cv2.imshow("Measure Screen", img)

        win_name = "Measure Screen"
        cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
        cv2.setMouseCallback(win_name, mouse_cb)
        cv2.imshow(win_name, img)

        while True:
            key = cv2.waitKey(20) & 0xFF
            if key == 27:  # ESC
                break
            if len(clicks) >= 8:
                break

        cv2.destroyAllWindows()

        if len(clicks) < 8:
            print("Você não clicou 8 vezes. Tente novamente.")
            return

        # Separa cliques
        top_lefts = clicks[:4]
        bot_rights = clicks[4:8]

        print("\n=== Coordenadas absolutas (pixels) ===")
        for i, (tl, br) in enumerate(zip(top_lefts, bot_rights), start=1):
            print(f"Slot {i}: x1={tl[0]}, y1={tl[1]}, x2={br[0]}, y2={br[1]}")

        print("\n=== Coordenadas normalizadas (para usar no código) ===")
        print("CARD_SLOTS_NORMALIZED = [")
        for i, (tl, br) in enumerate(zip(top_lefts, bot_rights), start=1):
            x1_n = tl[0] / w
            y1_n = tl[1] / h
            x2_n = br[0] / w
            y2_n = br[1] / h
            print(f"    ({x1_n:.6f}, {y1_n:.6f}, {x2_n:.6f}, {y2_n:.6f}),  # slot {i}")
        print("]")
        print("\n✅ Copie isso para o seu auto_label_fixed_cards.py ou main.py")

if __name__ == "__main__":
    main()