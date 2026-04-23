# NutriScan

**Real-time food detection and nutrition estimation using YOLOv8.**

NutriScan detects food items from a live webcam feed, looks up nutritional data from a local database, and displays per-item calorie badges alongside an aggregated macronutrient summary through an OpenCV overlay.

> CS 5330 Pattern Recognition and Computer Vision, Spring 2026
> Khoury College of Computer Sciences, Northeastern University

**Authors:** Yu Cao, Na Yin, Fan Zhang

## Key Results

| Model | Classes | P | R | F1 | mAP@0.5 |
|-------|---------|---|---|-----|---------|
| v1: YOLOv8n | 255 | .679 | .644 | .66 | .711 |
| v2: YOLOv8s | 194 | .837 | .812 | .81 | **.871** |

v2 achieves +16.0 pp mAP@0.5 over v1 and +17.0 pp over the published YOLOv5 baseline (0.701) on UEC FOOD-256.

## Features

- **YOLOv8s** fine-tuned on a quality-filtered 194-class subset of UEC FOOD-256
- **Cross-class NMS** eliminates duplicate detections across different food labels
- **Temporal smoothing** via 9-frame majority voting, no label flickering, no ghost boxes
- **Local nutrition database** covering all 194 categories, zero latency, no API needed
- **Redesigned UI** with rounded bounding boxes, capsule labels, kcal badges, and macronutrient donut chart

## Project Structure

```
nutriscan/
├── data/outputs/                <- Composed demo test images
├── src/
│   ├── main.py                  <- Real-time detection app
│   ├── nutrition.py             <- Local nutrition database
│   ├── compose_food_images.py   <- Demo test image generator
│   └── classes_v2.txt           <- 194 class labels
├── train.py                     <- v2 training script (local GPU)
├── train.ipynb                  <- v2 training notebook (Colab)
├── train_v1.ipynb               <- v1 training notebook (Colab)
└── requirements.txt
```

## Setup

```bash
pip install -r requirements.txt
```

Download model weights from [Google Drive](https://drive.google.com/drive/folders/1NJWpitbZurFdss-3rMXMIePQRX00-9gJ?usp=sharing) and place `best.pt` in `models/`.

## Usage

```bash
# Run with trained food model
python src/main.py

# Preview UI with pretrained COCO model (no food weights needed)
python src/main.py --demo
```

Options: `--model PATH`, `--camera INDEX`, `--conf THRESHOLD`

## Dataset

UEC FOOD-256 is publicly available at http://foodcam.mobi/dataset256.html. Our filtered 194-class subset is defined by `src/classes_v2.txt`.

## Training

**v2 (local GPU):**
```bash
python train.py
```

**v1 (Colab):** Open `train_v1.ipynb` in Google Colab with A100 GPU.
