# NutriScan

Real-time food detection and nutrition tracking using YOLOv8 and a webcam.

## Overview

NutriScan uses a YOLOv8 model trained on the UEC FOOD-256 dataset to detect food items in a live webcam feed. Detected items are looked up against the Nutritionix API to display per-item and aggregated nutrition totals (calories, protein, carbs, fat) as an overlay on the video stream.

## Project Structure

```
nutriscan/
├── data/                  # Training data (UEC FOOD-256 images + YOLO labels)
├── models/                # Trained model weights (best.pt)
├── src/
│   ├── nutrition.py       # Nutritionix API client with local JSON caching
│   └── main.py            # Webcam inference app
├── train.ipynb            # Google Colab training notebook
├── requirements.txt
└── README.md
```

## Setup

```bash
pip install -r requirements.txt
```

Set your Nutritionix API credentials as environment variables:

```bash
export NUTRITIONIX_APP_ID=your_app_id
export NUTRITIONIX_APP_KEY=your_app_key
```

Get free credentials at https://developer.nutritionix.com.

## Running

Place a trained `best.pt` in the `models/` directory, then:

```bash
python src/main.py
```

Press `q` to quit the webcam window.

## Training

Open `train.ipynb` in Google Colab. The notebook will:

1. Mount your Google Drive
2. Install `ultralytics`
3. Download and extract UEC FOOD-256
4. Convert Pascal VOC XML annotations to YOLO format
5. Train YOLOv8n for 50 epochs
6. Save `best.pt` back to your Drive

## Dataset

[UEC FOOD-256](http://foodcam.mobi/dataset256.html) — 256 food categories, ~31,000 images with bounding box annotations in Pascal VOC XML format.

## Dependencies

- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics)
- [OpenCV](https://opencv.org/)
- [Nutritionix API](https://developer.nutritionix.com/)
