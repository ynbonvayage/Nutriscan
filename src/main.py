"""
NutriScan — real-time food detection + nutrition overlay.

Usage:
    python src/main.py [--model models/best.pt] [--camera 0] [--conf 0.15]

Press 'q' to quit.
"""

import argparse
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

from nutrition import get_nutrition

# IoU overlap threshold for per-class NMS (applied after YOLOv8's built-in NMS)
_NMS_IOU = 0.45

# ── colour palette (BGR) for bounding boxes ────────────────────────────────
_PALETTE = [
    (0, 200, 255),
    (0, 255, 128),
    (255, 100, 0),
    (200, 0, 255),
    (0, 165, 255),
    (255, 200, 0),
]


def _box_color(class_id: int) -> tuple:
    return _PALETTE[class_id % len(_PALETTE)]


def _draw_label(frame, text: str, x: int, y: int, color: tuple) -> None:
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale, thickness = 0.75, 2
    (tw, th), baseline = cv2.getTextSize(text, font, scale, thickness)
    cv2.rectangle(frame, (x, y - th - baseline - 6), (x + tw + 6, y), color, -1)
    cv2.putText(
        frame, text, (x + 3, y - baseline - 2),
        font, scale, (0, 0, 0), thickness, cv2.LINE_AA,
    )


def _draw_nutrition_panel(frame, totals: dict) -> None:
    """Render aggregated nutrition in the top-left corner."""
    lines = [
        "--- Nutrition Totals ---",
        f"Calories : {totals['calories']:.0f} kcal",
        f"Protein  : {totals['protein_g']:.1f} g",
        f"Carbs    : {totals['carbs_g']:.1f} g",
        f"Fat      : {totals['fat_g']:.1f} g",
    ]
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale, thickness = 0.6, 1
    pad = 8
    line_h = 22
    panel_w = 240
    panel_h = pad * 2 + line_h * len(lines)

    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (panel_w, panel_h), (30, 30, 30), -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

    for i, line in enumerate(lines):
        color = (0, 255, 200) if i == 0 else (255, 255, 255)
        cv2.putText(
            frame, line, (pad, pad + line_h * (i + 1) - 4),
            font, scale, color, thickness, cv2.LINE_AA,
        )


def _apply_nms(boxes, iou_threshold: float = _NMS_IOU) -> list[int]:
    """
    Per-class NMS on top of YOLOv8's built-in NMS.

    YOLOv8 suppresses cross-class overlaps globally, but same-class boxes
    that survive with slightly different scores can still stack.  This pass
    groups detections by class and runs cv2.dnn.NMSBoxes on each group,
    returning the indices (into `boxes`) of detections to keep.
    """
    if len(boxes) == 0:
        return []

    by_class: dict[int, list[int]] = {}
    for i, box in enumerate(boxes):
        by_class.setdefault(int(box.cls[0]), []).append(i)

    kept: list[int] = []
    for indices in by_class.values():
        bboxes_xywh: list[list[float]] = []
        scores: list[float] = []
        for i in indices:
            x1, y1, x2, y2 = map(float, boxes[i].xyxy[0].tolist())
            bboxes_xywh.append([x1, y1, x2 - x1, y2 - y1])
            scores.append(float(boxes[i].conf[0]))

        survivors = cv2.dnn.NMSBoxes(
            bboxes_xywh, scores,
            score_threshold=0.0,   # confidence already filtered by YOLO
            nms_threshold=iou_threshold,
        )
        # NMSBoxes returns shape (N,1) in older OpenCV, (N,) in newer — flatten both
        for idx in np.array(survivors).flatten():
            kept.append(indices[int(idx)])

    return kept


def run(model_path: str, camera_index: int, conf_threshold: float) -> None:
    if not Path(model_path).exists():
        raise FileNotFoundError(
            f"Model not found: {model_path}\n"
            "Train a model first using train.ipynb and place best.pt in models/."
        )

    model = YOLO(model_path)
    class_names = model.names  # dict[int, str]

    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open camera index {camera_index}.")

    print("NutriScan running — press 'q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame.")
            break

        results = model(frame, conf=conf_threshold, verbose=False)[0]
        kept = _apply_nms(results.boxes)

        seen_labels: set[str] = set()
        totals = {"calories": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0}

        for i in kept:
            box = results.boxes[i]
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            label = class_names.get(cls_id, str(cls_id))
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            color = _box_color(cls_id)

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
            _draw_label(frame, f"{label} {conf:.0%}", x1, y1, color)

            if label not in seen_labels:
                seen_labels.add(label)
                print(f"[detect] {label} ({conf:.0%})")
                nutrients = get_nutrition(label)
                for k in totals:
                    totals[k] += nutrients.get(k, 0.0)

        _draw_nutrition_panel(frame, totals)

        cv2.imshow("NutriScan", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NutriScan real-time food detector")
    parser.add_argument("--model", default="models/best.pt", help="Path to YOLOv8 weights")
    parser.add_argument("--camera", type=int, default=0, help="Camera device index")
    parser.add_argument("--conf", type=float, default=0.15, help="Detection confidence threshold (default: 0.15)")
    args = parser.parse_args()

    run(args.model, args.camera, args.conf)
