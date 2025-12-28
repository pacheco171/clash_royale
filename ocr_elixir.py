"""
ocr_elixir.py - Versão Melhorada
Sistema de OCR focado APENAS na região correta do elixir
"""

import cv2
import numpy as np
import pytesseract
from pathlib import Path

class ElixirOCR:
    """Sistema de OCR otimizado para detecção de elixir"""
    
    def __init__(self):
        # Configuração do Tesseract
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        
        # Regiões calibradas (AJUSTE ESTES VALORES PARA SUA RESOLUÇÃO!)
        # Formato: (y1, y2, x1, x2) em porcentagem da tela
        self.regions = {
            'my_elixir': {
                'y': (0.88, 0.95),      # 88% a 95% da altura (parte inferior)
                'x': (0.05, 0.15),      # 5% a 15% da largura (esquerda)
            },
            'opponent_elixir': {
                'y': (0.05, 0.12),      # 5% a 12% da altura (parte superior)
                'x': (0.05, 0.15),      # 5% a 15% da largura (esquerda)
            }
        }
        
        # Histórico para suavização
        self.my_history = []
        self.opp_history = []
        self.max_history = 3  # Usa média dos últimos 3 valores
        
    def extract_my_elixir(self, frame_bgr):
        """Extrai SEU elixir"""
        return self._extract_elixir(frame_bgr, 'my_elixir', self.my_history)
    
    def extract_opponent_elixir(self, frame_bgr):
        """Extrai elixir do OPONENTE"""
        return self._extract_elixir(frame_bgr, 'opponent_elixir', self.opp_history)
    
    def _extract_elixir(self, frame_bgr, region_key, history_list):
        """Método interno para extrair elixir de uma região"""
        try:
            h, w = frame_bgr.shape[:2]
            region = self.regions[region_key]
            
            # Calcula coordenadas em pixels
            y1 = int(h * region['y'][0])
            y2 = int(h * region['y'][1])
            x1 = int(w * region['x'][0])
            x2 = int(w * region['x'][1])
            
            # Extrai região
            roi = frame_bgr[y1:y2, x1:x2]
            
            if roi.size == 0:
                return self._get_smoothed_value(history_list)
            
            # Pré-processamento AGRESSIVO
            # 1. Converte para escala de cinza
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            
            # 2. Aumenta contraste
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
            enhanced = clahe.apply(gray)
            
            # 3. Binarização adaptativa
            binary = cv2.adaptiveThreshold(
                enhanced, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                11, 2
            )
            
            # 4. Inverte se necessário (texto branco em fundo escuro)
            if np.mean(binary) < 127:
                binary = cv2.bitwise_not(binary)
            
            # 5. Remove ruído
            kernel = np.ones((2,2), np.uint8)
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
            
            # 6. Redimensiona para melhorar OCR (3x maior)
            h_roi, w_roi = binary.shape
            resized = cv2.resize(binary, (w_roi * 3, h_roi * 3), interpolation=cv2.INTER_CUBIC)
            
            # OCR APENAS NÚMEROS
            config = '--psm 7 -c tessedit_char_whitelist=0123456789'
            text = pytesseract.image_to_string(resized, config=config)
            
            # Extrai apenas dígitos
            digits = ''.join(filter(str.isdigit, text))
            
            if digits:
                value = int(digits)
                # Valida range (elixir vai de 0 a 10)
                if 0 <= value <= 10:
                    history_list.append(value)
                    if len(history_list) > self.max_history:
                        history_list.pop(0)
                    return value
            
            # Se falhou, usa valor suavizado do histórico
            return self._get_smoothed_value(history_list)
            
        except Exception as e:
            print(f"❌ OCR Erro: {e}")
            return self._get_smoothed_value(history_list)
    
    def _get_smoothed_value(self, history_list):
        """Retorna média dos últimos valores válidos"""
        if not history_list:
            return 0
        
        # Usa mediana ao invés de média (mais robusto contra outliers)
        return int(np.median(history_list))
    
    def calibrate_regions(self, frame_bgr, save_debug=True):
        """
        Modo de calibração: salva imagens das regiões para você ajustar
        Use isso para encontrar as coordenadas corretas!
        """
        h, w = frame_bgr.shape[:2]
        
        for region_name, region in self.regions.items():
            y1 = int(h * region['y'][0])
            y2 = int(h * region['y'][1])
            x1 = int(w * region['x'][0])
            x2 = int(w * region['x'][1])
            
            roi = frame_bgr[y1:y2, x1:x2]
            
            if save_debug:
                debug_path = Path(f"debug_{region_name}.png")
                cv2.imwrite(str(debug_path), roi)
                print(f"✅ Salvo: {debug_path}")
            
            # Mostra coordenadas
            print(f"\n{region_name}:")
            print(f"  Coordenadas: y={y1}:{y2}, x={x1}:{x2}")
            print(f"  Tamanho ROI: {roi.shape}")
    
    def reset(self):
        """Limpa histórico"""
        self.my_history.clear()
        self.opp_history.clear()


# ===== TESTE DO SISTEMA =====
if __name__ == "__main__":
    import mss
    
    print("🎮 Teste do OCR de Elixir")
    print("Pressione Ctrl+C para parar\n")
    
    ocr = ElixirOCR()
    
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        
        # Captura uma vez para calibração
        screenshot = sct.grab(monitor)
        img = np.array(screenshot)[:, :, :3]
        frame_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        
        print("📸 Calibrando regiões...")
        ocr.calibrate_regions(frame_bgr)
        print("\n✅ Verifique as imagens debug_*.png geradas")
        print("   Ajuste as coordenadas em self.regions se necessário\n")
        
        try:
            while True:
                screenshot = sct.grab(monitor)
                img = np.array(screenshot)[:, :, :3]
                frame_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                
                my_elixir = ocr.extract_my_elixir(frame_bgr)
                opp_elixir = ocr.extract_opponent_elixir(frame_bgr)
                
                print(f"\r⚡ Meu: {my_elixir} | Oponente: {opp_elixir}", end='', flush=True)
                
                import time
                time.sleep(0.5)
                
        except KeyboardInterrupt:
            print("\n\n✅ Teste finalizado")