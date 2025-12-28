import cv2
from pathlib import Path

# ===== CONFIGURAÇÕES =====

# Caminho do vídeo de entrada
VIDEO_PATH = Path(r"C:\clash_royale\videos\videoclash.mp4")

# Pasta de saída das imagens
OUTPUT_DIR = Path(r"C:\clash_royale\dataset\raw\video_jogo1")

# Quantos FRAMES POR SEGUNDO você quer extrair do vídeo
TARGET_FPS = 1.0   # 1 imagem por segundo. Pode aumentar para 2.0, 3.0, etc.

# Ativar filtro simples para tentar pegar só frames de partida (opcional)
USE_SIMPLE_MATCH_FILTER = False


def is_probable_match_frame(frame):
    """
    Filtro MUITO simples:
    - Olha a faixa inferior da tela (onde costumam ficar cartas + elixir)
    - Verifica se há bastante cor "viva" (evita telas muito escuras / menus)
    Isso não é perfeito, mas pode reduzir um pouco menus/telas pretas.
    """
    h, w = frame.shape[:2]
    roi = frame[int(h * 0.70):, :]  # parte de baixo da tela

    # Converte para HSV para medir saturação / brilho
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    h_ch, s_ch, v_ch = cv2.split(hsv)

    mean_sat = s_ch.mean()
    mean_val = v_ch.mean()

    # Heurística: partidas costumam ter bastante cor e brilho
    if mean_sat > 60 and mean_val > 60:
        return True
    return False


def main():
    if not VIDEO_PATH.exists():
        print(f"❌ Vídeo não encontrado: {VIDEO_PATH}")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(str(VIDEO_PATH))
    if not cap.isOpened():
        print("❌ Erro ao abrir vídeo:", VIDEO_PATH)
        return

    native_fps = cap.get(cv2.CAP_PROP_FPS)
    if native_fps <= 0:
        native_fps = 30.0  # fallback

    frame_interval = max(1, int(round(native_fps / TARGET_FPS)))
    print(f"🎥 FPS do vídeo: {native_fps:.2f}")
    print(f"🖼️ Salvando ~{TARGET_FPS} frame(s)/segundo (a cada {frame_interval} frames)")
    print(f"📁 Saída: {OUTPUT_DIR}")

    frame_idx = 0
    saved = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Pula frames até o intervalo desejado
        if frame_idx % frame_interval != 0:
            frame_idx += 1
            continue

        # Filtro opcional para tentar pegar só tela de partida
        if USE_SIMPLE_MATCH_FILTER and not is_probable_match_frame(frame):
            frame_idx += 1
            continue

        filename = f"frame_{frame_idx:07d}.png"
        filepath = OUTPUT_DIR / filename
        cv2.imwrite(str(filepath), frame)
        saved += 1

        if saved % 50 == 0:
            print(f"🖼️ {saved} frames salvos...")

        frame_idx += 1

    cap.release()
    print(f"✅ Finalizado! Total de frames salvos: {saved}")
    print(f"📁 Pasta: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()