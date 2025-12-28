from ultralytics import YOLO
from pathlib import Path

def main():
    model = YOLO("yolov8n.pt")
    data_path = Path("dataset/yolo_cards/data.yaml")
    if not data_path.exists():
        print(f"data.yaml não encontrado em {data_path.resolve()}")
        return
    model.train(
        data=str(data_path),
        epochs=20,
        imgsz=640,
        project="runs",
        name="cards_slots",
    )

if __name__ == "__main__":
    main()
