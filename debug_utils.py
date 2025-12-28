"""
debug_utils.py
Ferramentas de debug para o sistema de detecção
"""

import cv2
import numpy as np
from pathlib import Path
from datetime import datetime


class DebugTools:
    """Ferramentas para debug e visualização"""
    
    def __init__(self, save_dir="debug_screenshots"):
        """
        Inicializa ferramentas de debug
        
        Args:
            save_dir: Diretório para salvar screenshots
        """
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(exist_ok=True)
        self.screenshot_count = 0
        
    def save_detection_screenshot(self, frame_bgr, detections, prefix="detection"):
        """
        Salva screenshot com detecções marcadas
        
        Args:
            frame_bgr: Frame em BGR (OpenCV)
            detections: Lista de detecções [{'name': str, 'bbox': [x1,y1,x2,y2], 'confidence': float}]
            prefix: Prefixo do nome do arquivo
            
        Returns:
            str: Caminho do arquivo salvo
        """
        if not detections:
            return None
        
        # Copia frame
        debug_frame = frame_bgr.copy()
        
        # Cores para diferentes níveis de confiança
        def get_color(confidence):
            if confidence > 0.9:
                return (0, 255, 0)  # Verde - alta confiança
            elif confidence > 0.8:
                return (0, 255, 255)  # Amarelo - média confiança
            else:
                return (0, 0, 255)  # Vermelho - baixa confiança
        
        # Desenha detecções
        for det in detections:
            if not isinstance(det, dict):
                continue
            
            name = det.get('name', 'Unknown')
            confidence = det.get('confidence', 0)
            bbox = det.get('bbox')
            
            if bbox and len(bbox) == 4:
                x1, y1, x2, y2 = map(int, bbox)
                color = get_color(confidence)
                
                # Retângulo
                cv2.rectangle(debug_frame, (x1, y1), (x2, y2), color, 2)
                
                # Label
                label = f"{name} {confidence:.2%}"
                label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
                
                # Fundo do label
                cv2.rectangle(
                    debug_frame,
                    (x1, y1 - label_size[1] - 10),
                    (x1 + label_size[0], y1),
                    color,
                    -1
                )
                
                # Texto
                cv2.putText(
                    debug_frame,
                    label,
                    (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 0, 0),
                    2
                )
        
        # Adiciona timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        cv2.putText(
            debug_frame,
            f"[{timestamp}] {len(detections)} detecções",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )
        
        # Salva
        self.screenshot_count += 1
        filename = f"{prefix}_{self.screenshot_count:04d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        filepath = self.save_dir / filename
        
        cv2.imwrite(str(filepath), debug_frame)
        
        return str(filepath)
    
    def create_comparison_image(self, frames_with_labels):
        """
        Cria imagem comparando múltiplos frames
        
        Args:
            frames_with_labels: Lista de tuplas (frame, label)
            
        Returns:
            np.ndarray: Imagem combinada
        """
        if not frames_with_labels:
            return None
        
        # Redimensiona todos para mesmo tamanho
        target_height = 300
        resized_frames = []
        
        for frame, label in frames_with_labels:
            h, w = frame.shape[:2]
            scale = target_height / h
            new_w = int(w * scale)
            
            resized = cv2.resize(frame, (new_w, target_height))
            
            # Adiciona label
            cv2.putText(
                resized,
                label,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )
            
            resized_frames.append(resized)
        
        # Concatena horizontalmente
        combined = np.hstack(resized_frames)
        
        return combined
    
    def visualize_roi(self, frame_bgr, roi_coords, label="ROI"):
        """
        Visualiza uma região de interesse
        
        Args:
            frame_bgr: Frame completo
            roi_coords: Coordenadas (y1, y2, x1, x2)
            label: Label da ROI
            
        Returns:
            np.ndarray: Frame com ROI marcada
        """
        debug_frame = frame_bgr.copy()
        y1, y2, x1, x2 = roi_coords
        
        # Desenha retângulo
        cv2.rectangle(debug_frame, (x1, y1), (x2, y2), (0, 255, 255), 2)
        
        # Label
        cv2.putText(
            debug_frame,
            label,
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2
        )
        
        return debug_frame
    
    def create_elixir_visualization(self, frame_bgr, my_elixir, opp_elixir):
        """
        Cria visualização do estado de elixir
        
        Args:
            frame_bgr: Frame do jogo
            my_elixir: Seu elixir
            opp_elixir: Elixir do oponente
            
        Returns:
            np.ndarray: Frame com visualização
        """
        debug_frame = frame_bgr.copy()
        h, w = debug_frame.shape[:2]
        
        # Cria overlay transparente
        overlay = debug_frame.copy()
        
        # Barra do jogador (parte inferior)
        player_bar_y = h - 60
        self._draw_elixir_bar(overlay, w//2 - 150, player_bar_y, my_elixir, "YOU", (0, 255, 0))
        
        # Barra do oponente (parte superior)
        opp_bar_y = 20
        self._draw_elixir_bar(overlay, w//2 - 150, opp_bar_y, opp_elixir, "OPPONENT", (0, 0, 255))
        
        # Diferença
        diff = my_elixir - opp_elixir
        diff_color = (0, 255, 0) if diff > 0 else (0, 0, 255)
        diff_text = f"Difference: {diff:+d}"
        
        cv2.putText(
            overlay,
            diff_text,
            (w//2 - 80, h//2),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            diff_color,
            3
        )
        
        # Blend
        cv2.addWeighted(overlay, 0.7, debug_frame, 0.3, 0, debug_frame)
        
        return debug_frame
    
    def _draw_elixir_bar(self, frame, x, y, elixir, label, color):
        """Desenha barra de elixir"""
        bar_width = 300
        bar_height = 30
        
        # Fundo da barra
        cv2.rectangle(frame, (x, y), (x + bar_width, y + bar_height), (50, 50, 50), -1)
        
        # Barra preenchida
        fill_width = int((elixir / 10) * bar_width)
        cv2.rectangle(frame, (x, y), (x + fill_width, y + bar_height), color, -1)
        
        # Borda
        cv2.rectangle(frame, (x, y), (x + bar_width, y + bar_height), (255, 255, 255), 2)
        
        # Texto
        text = f"{label}: {elixir}/10"
        cv2.putText(
            frame,
            text,
            (x + 10, y + 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )


# Função auxiliar para usar no main.py
def create_debug_tools(save_dir="debug_screenshots"):
    """Cria e retorna uma instância de DebugTools"""
    return DebugTools(save_dir)


# Teste
if __name__ == "__main__":
    print("🔧 Debug Tools carregado!")
    print("Use no seu main.py:")
    print()
    print("from debug_utils import create_debug_tools")
    print()
    print("debug = create_debug_tools()")
    print("debug.save_detection_screenshot(frame, detections)")
