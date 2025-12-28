"""
COLETOR DE DADOS - Clash Royale
Captura screenshots automaticamente durante partidas
"""

import sys
import time
from pathlib import Path
from datetime import datetime
import numpy as np
import cv2
import mss

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QPushButton, QLabel, QSpinBox, QHBoxLayout, QTextEdit
)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont

# ==== CONFIGURAÇÕES ====

BASE_DIR = Path(__file__).resolve().parent
DATASET_DIR = BASE_DIR / "dataset" / "raw"
DATASET_DIR.mkdir(parents=True, exist_ok=True)

CAPTURE_INTERVAL = 2000  # 2 segundos (ms)
MONITOR_INDEX = 1

# ==== CAPTURADOR ====

class DataCollector(QMainWindow):
    def __init__(self):
        super().__init__()
        self.is_collecting = False
        self.capture_count = 0
        self.session_dir = None
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.capture_frame)
        
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle("📸 Data Collector - Clash Royale")
        self.setGeometry(100, 100, 500, 400)
        
        central = QWidget()
        layout = QVBoxLayout()
        
        # Título
        title = QLabel("📸 Coletor de Screenshots")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Instruções
        instructions = QLabel(
            "1. Abra Clash Royale no BlueStacks\n"
            "2. Configure o intervalo de captura\n"
            "3. Clique em 'Iniciar Coleta'\n"
            "4. Jogue normalmente\n"
            "5. Clique em 'Parar' quando terminar"
        )
        instructions.setStyleSheet(
            "background-color: #1f2937; color: #10b981; padding: 10px; "
            "border-radius: 5px; font-size: 11px;"
        )
        layout.addWidget(instructions)
        
        # Intervalo
        interval_layout = QHBoxLayout()
        interval_label = QLabel("Intervalo (segundos):")
        self.interval_spin = QSpinBox()
        self.interval_spin.setMinimum(1)
        self.interval_spin.setMaximum(10)
        self.interval_spin.setValue(2)
        self.interval_spin.valueChanged.connect(self.update_interval)
        interval_layout.addWidget(interval_label)
        interval_layout.addWidget(self.interval_spin)
        interval_layout.addStretch()
        layout.addLayout(interval_layout)
        
        # Botões
        btn_layout = QHBoxLayout()
        
        self.btn_start = QPushButton("▶️ Iniciar Coleta")
        self.btn_start.clicked.connect(self.start_collection)
        self.btn_start.setStyleSheet(
            "background-color: #22c55e; color: white; padding: 12px; "
            "font-weight: bold; font-size: 14px;"
        )
        
        self.btn_stop = QPushButton("⏹️ Parar")
        self.btn_stop.clicked.connect(self.stop_collection)
        self.btn_stop.setEnabled(False)
        self.btn_stop.setStyleSheet(
            "background-color: #ef4444; color: white; padding: 12px; "
            "font-weight: bold; font-size: 14px;"
        )
        
        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_stop)
        layout.addLayout(btn_layout)
        
        # Status
        self.status_label = QLabel("Status: Aguardando")
        self.status_label.setStyleSheet(
            "background-color: #1f2937; color: #fbbf24; padding: 10px; "
            "border-radius: 5px; font-weight: bold; font-size: 13px;"
        )
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Contador
        self.count_label = QLabel("Capturas: 0")
        self.count_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.count_label.setStyleSheet("color: #3b82f6;")
        layout.addWidget(self.count_label)
        
        # Logs
        log_label = QLabel("📋 Logs:")
        layout.addWidget(log_label)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(120)
        layout.addWidget(self.log_text)
        
        central.setLayout(layout)
        self.setCentralWidget(central)
    
    def update_interval(self, value):
        global CAPTURE_INTERVAL
        CAPTURE_INTERVAL = value * 1000
        self.add_log(f"⏱️ Intervalo alterado para {value}s")
    
    def start_collection(self):
        # Criar pasta da sessão
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = DATASET_DIR / f"session_{timestamp}"
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
        self.is_collecting = True
        self.capture_count = 0
        
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.interval_spin.setEnabled(False)
        
        self.timer.start(CAPTURE_INTERVAL)
        
        self.status_label.setText("Status: 🔴 COLETANDO")
        self.status_label.setStyleSheet(
            "background-color: #dc2626; color: white; padding: 10px; "
            "border-radius: 5px; font-weight: bold; font-size: 13px;"
        )
        
        self.add_log(f"✅ Coleta iniciada - Pasta: {self.session_dir.name}")
        self.add_log(f"⏱️ Capturando a cada {CAPTURE_INTERVAL // 1000}s")
    
    def stop_collection(self):
        self.is_collecting = False
        self.timer.stop()
        
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.interval_spin.setEnabled(True)
        
        self.status_label.setText("Status: ⏸️ Pausado")
        self.status_label.setStyleSheet(
            "background-color: #1f2937; color: #fbbf24; padding: 10px; "
            "border-radius: 5px; font-weight: bold; font-size: 13px;"
        )
        
        self.add_log(f"⏸️ Coleta pausada - Total: {self.capture_count} imagens")
        self.add_log(f"📁 Salvo em: {self.session_dir}")
    
    def capture_frame(self):
        try:
            with mss.mss() as sct:
                monitor = sct.monitors[MONITOR_INDEX]
                screenshot = sct.grab(monitor)
                img = np.array(screenshot)[:, :, :3]  # BGRA -> BGR
            
            # Salvar
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            filename = f"frame_{timestamp}.png"
            filepath = self.session_dir / filename
            
            cv2.imwrite(str(filepath), img)
            
            self.capture_count += 1
            self.count_label.setText(f"Capturas: {self.capture_count}")
            
            if self.capture_count % 10 == 0:
                self.add_log(f"📸 {self.capture_count} imagens capturadas")
        
        except Exception as e:
            self.add_log(f"❌ Erro na captura: {e}")
    
    def add_log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f'<span style="color: gray;">[{timestamp}]</span> {message}')
        
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

# ==== MAIN ====

def main():
    app = QApplication(sys.argv)
    collector = DataCollector()
    collector.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()