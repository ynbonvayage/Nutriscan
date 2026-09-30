<div align="center">

# 🍱 NutriScan

### Point a webcam at your meal and get calories and macros in real time.

**Real-time multi-dish food detection + nutrition estimation with YOLOv8**

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![YOLOv8](https://img.shields.io/badge/Ultralytics-YOLOv8s-111F68)
![OpenCV](https://img.shields.io/badge/OpenCV-real--time-5C3EE8?logo=opencv&logoColor=white)
![mAP](https://img.shields.io/badge/mAP%400.5-0.871-2ea44f)
![Classes](https://img.shields.io/badge/food%20classes-194-orange)

<img src="assets/demo.gif" alt="NutriScan live demo: detecting soba noodles, zoni, tempura bowl and cutlet curry with per-dish calories and a macro summary" width="720">

*Live webcam demo. Every dish gets its own box, label and kcal badge. The bottom strip shows the meal total and a protein / carbs / fat donut chart.*

[📦 Model weights](https://drive.google.com/drive/folders/1NJWpitbZurFdss-3rMXMIePQRX00-9gJ?usp=sharing) · [🗂 Dataset](http://foodcam.mobi/dataset256.html)

</div>

---

## ✨ Why NutriScan?

Keeping a food diary helps people eat better, but typing in every meal is tedious and most people stop doing it. NutriScan skips the typing: **show the camera your plate and the nutrition shows up on screen**, with no photos to upload, no forms and no network calls.

| | |
|---|---|
| 🎯 **Accurate** | **0.871 mAP@0.5** on UEC FOOD-256, **+17.0 pp** over the published YOLOv5 baseline (0.701) |
| 🍜 **Multi-dish** | Detects and labels several dishes in one frame, then sums the whole meal |
| ⚡ **Real-time & offline** | Runs live on a webcam feed. The nutrition lookup is a local table, so there are no API calls and it works without internet |
| 🧊 **Stable** | A 9-frame temporal vote stops labels from flickering without leaving "ghost" boxes behind |
| 🎨 **Polished UI** | Rounded boxes, capsule labels, kcal badges and a macro donut chart, all drawn with plain OpenCV |

## 🚀 What's new in this project

### 1. Data-centric model improvement: fewer, cleaner classes → +16 pp mAP
Instead of only scaling up the model, we **audited the dataset**. Of the 255 usable UEC FOOD-256 categories, 61 were unreliable: 15 had fewer than 100 training samples and 46 scored below 0.55 mAP in v1. Removing them and moving from YOLOv8n to YOLOv8s gave:

| Model | Classes | Precision | Recall | F1 | mAP@0.5 | mAP@0.5:0.95 |
|-------|:-------:|:---:|:---:|:---:|:---:|:---:|
| YOLOv5 (Tan et al., published) | 256 | – | – | – | .701 | – |
| v1: YOLOv8n | 255 | .679 | .644 | .66 | .711 | .559 |
| **v2: YOLOv8s** | **194** | **.837** | **.812** | **.81** | **.871** | **.692** |

**77.8%** of classes reach ≥ 0.80 mAP and **91.2%** reach ≥ 0.70. The result reproduces across hardware: a Colab A100 run reached 0.859.

### 2. Temporal majority voting: stable labels, no ghost boxes
Frame-by-frame detectors "flicker": the same bowl can read *rice → fried rice → rice* from one frame to the next. Our `_DetectionCache` fixes this with a **two-step vote** over the last 9 frames:

1. **Per-frame vote.** For each current box, find IoU > 0.3 matches in each of the 9 previous frames. Each frame casts **one** vote: the label of its highest-confidence match.
2. **Label selection.** The label with the most votes wins. Because 9 is odd, there are no ties.

The box coordinates are also averaged over the winning label's history to remove jitter. Only boxes found in the **current** frame are drawn, so stale "ghost" boxes never appear. When the food changes, the new label takes over in about 5 frames.

### 3. Multi-stage post-processing pipeline

```
Webcam → YOLOv8s → Per-class NMS (IoU 0.45) → Cross-class NMS (IoU 0.70)
       → Large-box filter (>70% of frame) → 9-frame voting → Nutrition lookup → UI overlay
```

- **Cross-class NMS** merges overlapping detections of the *same* food that got *different* labels (e.g. `rice 24%` + `mixed rice 58%` → one box).
- **Large-box filter** drops detections covering more than 70% of the frame, which are almost always background false positives.

### 4. Zero-latency local nutrition database
[`src/nutrition.py`](src/nutrition.py) maps **all 194 classes** to calories, protein, carbs, fat and serving size. Labels are looked up by exact key first, then by a normalised or partial match. The per-item values are summed for the meal totals shown in the bottom strip.

### 5. Designed interface (pure OpenCV)
The nutrition strip sits *below* the camera frame so it never covers the food. Labels shift automatically so they don't overlap each other, and the macro donut chart is drawn directly with OpenCV masks.

<p align="center">
  <img src="assets/screenshot_soba_zoni.jpg" width="49%" alt="Soba noodle and zoni detected, 580 kcal total">
  <img src="assets/screenshot_tempura_curry.jpg" width="49%" alt="Tempura bowl and cutlet curry detected, 1240 kcal total">
</p>

## 📊 Results

<p align="center">
  <img src="assets/pr_curve_v2.png" width="49%" alt="v2 precision-recall curve">
  <img src="assets/val_predictions_v2.jpg" width="49%" alt="v2 predictions on validation images">
</p>
<p align="center"><em>Left: v2 precision–recall curve across 194 classes. Right: v2 predictions on validation images.</em></p>

## 🛠 Quick start

```bash
git clone https://github.com/ynbonvayage/Nutriscan.git
cd Nutriscan
pip install -r requirements.txt
```

Download `best.pt` from [Google Drive](https://drive.google.com/drive/folders/1NJWpitbZurFdss-3rMXMIePQRX00-9gJ?usp=sharing) and place it in `models/`.

```bash
python src/main.py               # run with the trained food model
python src/main.py --conf 0.25   # adjust confidence threshold
python src/main.py --demo        # preview the UI with a pretrained COCO model (no food weights needed)
```

| Option | Default | Description |
|--------|---------|-------------|
| `--model PATH` | `models/best.pt` | YOLOv8 weights |
| `--camera INDEX` | `0` | Webcam device index |
| `--conf THRESHOLD` | `0.20` | Detection confidence threshold |

No real food nearby? Run [`src/compose_food_images.py`](src/compose_food_images.py) to build test images with 2–3 dishes each from UEC FOOD-256 (samples are in [`data/outputs/`](data/outputs/)). Open one on a phone or tablet and hold it up to the webcam.

## 🧪 Training

| | v1 | v2 |
|---|---|---|
| Architecture | YOLOv8n (8.2M params) | YOLOv8s (11.2M params) |
| Classes | 255 | 194 |
| Hardware | Colab A100 | RTX 5070 |
| Epochs (best) | 50 (50) | 143 (98) |
| Training time | 3.25 h | 8.3 h |

```bash
python train.py        # v2, local GPU
```
v1: open [`train_v1.ipynb`](train_v1.ipynb) in Google Colab with an A100 GPU. [`train.ipynb`](train.ipynb) is the Colab version of v2.

**Dataset:** [UEC FOOD-256](http://foodcam.mobi/dataset256.html). Our filtered 194-class subset is defined by [`src/classes_v2.txt`](src/classes_v2.txt).

## 📁 Project structure

```
nutriscan/
├── assets/                      <- README demo GIF, screenshots and plots
├── data/outputs/                <- Composed multi-dish demo images
├── src/
│   ├── main.py                  <- Real-time detection app
│   ├── nutrition.py             <- Local nutrition database (194 classes)
│   ├── compose_food_images.py   <- Demo test image generator
│   └── classes_v2.txt           <- 194 class labels
├── train.py                     <- v2 training script (local GPU)
├── train.ipynb                  <- v2 training notebook (Colab)
├── train_v1.ipynb               <- v1 training notebook (Colab)
└── requirements.txt
```

## 🔭 Limitations & future work

- **Portion size:** each class uses a fixed serving size. *Next:* estimate portions from monocular depth.
- **Closed vocabulary:** foods outside the 194 classes are missed or mislabelled. *Next:* open-vocabulary detection with an API fallback.
- **Look-alike dishes** (e.g. chicken rice vs. fried rice) still get confused.
- **Mobile deployment** via INT8 quantisation, plus a user study comparing logging compliance with manual food diaries.

## 👥 Authors

**Yu Cao · Na Yin · Fan Zhang**. CS 5330 Computer Vision final project, Khoury College of Computer Sciences, Northeastern University (Spring 2026).
