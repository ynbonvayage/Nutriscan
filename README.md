# NutriScan

Real-time food detection and nutrition tracking using YOLOv8 and a webcam.

## Overview

NutriScan uses a YOLOv8 model trained on the UEC FOOD-256 dataset to detect food items in a live webcam feed. Detected items are looked up in a local nutrition database (279 foods, no API key required) and aggregated calorie, protein, carb, and fat totals are rendered as an overlay on the video stream.

## Project Structure

```
nutriscan/
├── data/                  # Training data (UEC FOOD-256 images + YOLO labels)
├── models/                # Trained model weights (best.pt)
├── src/
│   ├── nutrition.py       # Local nutrition database — no external API
│   └── main.py            # Webcam inference app with NMS post-processing
├── train.ipynb            # Google Colab training notebook
├── requirements.txt
└── README.md
```

## Setup

```bash
pip install -r requirements.txt
```

No API keys or network access required at runtime.

## Running

Place a trained `best.pt` in the `models/` directory, then:

```bash
python src/main.py
```

Press `q` to quit.

### Options

| Flag | Default | Description |
|---|---|---|
| `--model` | `models/best.pt` | Path to YOLOv8 weights |
| `--camera` | `0` | Camera device index |
| `--conf` | `0.15` | Detection confidence threshold |

Example — use a different camera at higher confidence:

```bash
python src/main.py --camera 1 --conf 0.25
```

## Detection pipeline

Each frame goes through:

1. **YOLOv8 inference** at the configured confidence threshold
2. **Per-class NMS** (`IoU = 0.45`) — removes stacked duplicate boxes of the same food class that survive YOLO's built-in NMS
3. **Nutrition lookup** — each unique detected label is looked up in the local database; results are aggregated across the frame
4. **Overlay rendering** — bounding boxes with class + confidence labels, and a nutrition panel (calories, protein, carbs, fat) in the top-left corner

Detected class names are also printed to the terminal on each new detection, so you can verify lookups even when the overlay is hard to read:

```
[detect] ramen (82%)
[detect] gyoza (61%)
```

## Training

Open `train.ipynb` in Google Colab (GPU runtime recommended).

**Before running:** download `dataset256.zip` from the [UEC FOOD-256 dataset page](http://foodcam.mobi/dataset256.html) and upload it to `MyDrive/nutriscan/dataset256.zip`.

The notebook will:

1. Mount your Google Drive
2. Install `ultralytics`
3. Extract `dataset256.zip` and verify the folder structure
4. Read category names from `UECFOOD256/category.txt`
5. Convert `bb_info.txt` bounding boxes to YOLO format (85 / 15 train/val split)
6. Train YOLOv8n for 50 epochs (early stopping at patience 10)
7. Save `best.pt` and `results.csv` to `MyDrive/nutriscan/`
8. Run a final validation and print mAP50 / mAP50-95

## Dataset

[UEC FOOD-256](http://foodcam.mobi/dataset256.html) — 256 Japanese and international food categories, ~31,000 images. Bounding boxes are stored in per-category `bb_info.txt` files (space-separated, one box per row).

## Nutrition database

`src/nutrition.py` ships a fully offline database covering all 256 UEC FOOD-256 categories plus common variants and aliases (346 total lookup keys). Data is sourced from the USDA FoodData Central and the Japanese Standard Tables of Food Composition (8th ed.).

```python
from nutrition import get_nutrition, aggregate

get_nutrition("ramen")
# {'calories': 450.0, 'protein_g': 22.0, 'carbs_g': 58.0, 'fat_g': 14.0,
#  'serving_g': 400, 'serving_desc': '1 bowl'}

aggregate(["sushi", "tempura", "miso soup"])
# {'calories': 800.0, 'protein_g': 37.0, 'carbs_g': 96.8, 'fat_g': 29.5}
```

## Dependencies

- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics)
- [OpenCV](https://opencv.org/)
- [Pillow](https://python-pillow.org/)
- NumPy
