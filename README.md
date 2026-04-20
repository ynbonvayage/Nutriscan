# NutriScan

**Authors:** Yu Cao, Fan Zhang, Na Yin  
**Course:** CS 5330 — Pattern Recognition and Computer Vision  
**Date:** April 2026

---

## Overview

NutriScan is a real-time food detection and nutrition tracking application. It uses a YOLOv8s model trained on the UEC FOOD-256 dataset to detect food items from a live webcam feed, then looks up and displays per-item and aggregated nutrition information (calories, protein, carbs, fat) as an overlay on the video stream.

---

## Project Structure

```
nutriscan/
├── data/                    # Training data (dataset zip goes here)
├── models/
│   └── best.pt              # Trained YOLOv8s weights
├── src/
│   ├── main.py              # Webcam inference app with NMS and overlay rendering
│   ├── nutrition.py         # Offline nutrition database (194 food classes)
│   ├── classes_v2.txt       # Filtered class list used for training and lookup
│   └── compose_food_images.py  # Utility for assembling sample food images
├── train_v1.ipynb           # training notebook (v1, original class list,yolov8m, no NMS, no temporal smoothing)
├── train.ipynb              # training notebook (v2, filtered class list, yolov8s, per-class + cross-class NMS, max-size filter, temporal smoothing)
├── train.py                 # training script (v2, same functionality as train.ipynb but for local/GPU server use)
├── requirements.txt
└── README.md
```

---

## Setup

```bash
pip install -r requirements.txt
```

No API keys or network access required at runtime.

---

## Running

Place trained weights at `models/best.pt`, then:

```bash
python src/main.py
```

Press `q` to quit.

### Options

| Flag | Default | Description |
|---|---|---|
| `--model` | `models/best.pt` | Path to YOLOv8 weights |
| `--camera` | `0` | Camera device index |
| `--conf` | `0.20` | Detection confidence threshold |

Example — use a different camera at higher confidence:

```bash
python src/main.py --camera 1 --conf 0.30
```

Preview the overlay UI without a trained food model:

```bash
python src/main.py --demo
```

---

## Detection Pipeline

Each frame goes through:

1. **YOLOv8s inference** at the configured confidence threshold
2. **Per-class NMS** (`IoU = 0.45`) — removes stacked duplicate boxes within each food class
3. **Cross-class NMS** (`IoU = 0.7`) — removes lower-confidence boxes that overlap a stronger detection across different classes
4. **Max-size filter** — discards any box covering more than 70% of the frame area (suppresses whole-scene false positives)
5. **Temporal smoothing** — a rolling 8-frame history promotes the highest-confidence label seen at each spatial location, suppressing single-frame misdetections without introducing ghost boxes
6. **Nutrition lookup** — each detected label is looked up in the local database and totals are aggregated across the frame
7. **Overlay rendering** — rounded bounding boxes, per-box food name + confidence capsules, per-box calorie badges, and a footer strip with total calories and a protein/carbs/fat donut chart

Terminal output prints each new detection so lookups can be verified without reading the overlay:

```
[detect] ramen_noodle (84%)
[detect] gyoza (67%)
```

---

## Training

Open `train_v2.ipynb` in Google Colab (GPU runtime recommended).

**Before running:** download `dataset256.zip` from the [UEC FOOD-256 dataset page](http://foodcam.mobi/dataset256.html) and upload it to `MyDrive/nutriscan/v2/dataset256.zip`.

The notebook will:

1. Mount Google Drive
2. Install `ultralytics`
3. Check whether a converted YOLO dataset already exists in Drive — skips re-conversion if so
4. Extract and convert `bb_info.txt` bounding boxes to YOLO format (85 / 15 train/val split)
5. Filter out 62 classes with too few samples or poor prior-run mAP50 (< 0.55)
6. Copy the converted dataset to Drive for reuse across sessions
7. Train YOLOv8s for up to 400 epochs with early stopping (patience = 40)
8. Save `best_v2.pt` to `MyDrive/nutriscan/v2/`
9. Run final validation and print mAP50, mAP50-95, and top/bottom 10 per-class results

To train locally or on a GPU server, use `train.py` instead:

```bash
python train.py --zip_file data/dataset256.zip --epochs 400 --batch 8
```

---

## Dataset

[UEC FOOD-256](http://foodcam.mobi/dataset256.html) — 256 Japanese and international food categories, ~31,000 images with bounding-box annotations stored in per-category `bb_info.txt` files.

After filtering, **194 classes** are used for training and inference. The filtered class list is in `src/classes_v2.txt`.

---

## Nutrition Database

`src/nutrition.py` ships a fully offline database covering all 194 retained food classes. Data is sourced from the USDA FoodData Central and the Japanese Standard Tables of Food Composition (8th ed.).

```python
from nutrition import get_nutrition, aggregate

get_nutrition("ramen_noodle")
# {'calories': 450.0, 'protein_g': 22.0, 'carbs_g': 58.0, 'fat_g': 14.0,
#  'serving_g': 400, 'serving_desc': '1 bowl'}

aggregate(["sushi", "tempura_bowl", "clear_soup"])
# {'calories': 760.0, 'protein_g': 34.0, 'carbs_g': 98.0, 'fat_g': 20.0}
```

Lookup falls back from exact match → normalised match → partial match → zero fallback.

---

## Dependencies

- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics)
- [OpenCV](https://opencv.org/)
- [Pillow](https://python-pillow.org/)
- NumPy
