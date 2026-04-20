# Authors: Yu Cao, Fan Zhang, Na Yin
# Date: April 2026
# Purpose: Training script for NutriScan YOLOv8s model
#          on the UEC FOOD-256 dataset with class
#          filtering. Extracts and converts the dataset
#          to YOLO format, filters low-performing and
#          low-sample classes, then trains and saves
#          the best model weights.
import os
import zipfile
import pathlib
import argparse
import yaml
import shutil
import random
from PIL import Image
from ultralytics import YOLO

# Classes to exclude from training
SKIP_CLASSES = {
    # Excluded: too few training samples (< 100)
    'xiao_long_bao', 'yellow_curry', 'Fried_spring_rolls',
    'coconut_milk_soup', 'gulai', 'minced_pork_rice',
    'Crispy_Noodles', 'Chicken_Rice_Curry_With_Coconut',
    'sushi_bowl', 'shrimp_with_chill_source', 'laulau',
    'Egg_Noodle_In_Chicken_Yellow_Curry', 'pho',
    'ball_shaped_bun_with_pork', 'mie_ayam',

    # Excluded: mAP50 < 0.55 in previous training run
    'meat_loaf', 'grilled_eggplant', 'tanmen',
    'pork_belly', 'fried_fish', 'beef_in_oyster_sauce',
    'pork_miso_soup', 'ayam_goreng', 'cold_tofu',
    'chip_butty', 'noodles_with_fish_curry', 'rice',
    'green_salad', 'Rice_crispy_pork', 'french_fries',
    'sauteed_vegetables', 'sausage', 'nasi_campur',
    'chicken_cutlet', 'boiled_fish', 'teriyaki_grilled_fish',
    'fried_chicken', 'tempura', 'grilled_salmon',
    'salmon_meuniere', 'sirloin_cutlet', 'omelet',
    'ganmodoki', 'miso_soup', 'simmered_pork',
    'nanbanzuke', 'stewed_pork_leg', 'Pork_with_lemon',
    'laksa', 'chow_mein', 'oxtail_soup', 'waffle',
    'roast_duck', 'rice_ball', 'pork_loin_cutlet',
    'pork_fillet_cutlet', 'ham_cutlet', 'minced_meat_cutlet',
    'egg_sunny-side_up', 'sukiyaki', 'fried_noodle',
}


def extract_dataset(archive_path, extract_to):
    """
    Extract the dataset zip archive to a directory.
    archive_path: Path to the .zip file.
    extract_to: Path to the extraction destination directory.
    Returns True on success, False if the archive is missing.
    """
    if not archive_path.exists():
        print(f"Archive not found: {archive_path}")
        return False

    print(f"Extracting {archive_path} to {extract_to} ...")
    with zipfile.ZipFile(archive_path, 'r') as zf:
        zf.extractall(extract_to)
    print("Extraction complete.")
    return True


def convert_to_yolo(dataset_root, yolo_root, val_split=0.15):
    """
    Convert UEC FOOD-256 bounding-box annotations to YOLO format.
    dataset_root: Path to the extracted UECFOOD256 folder.
    yolo_root: Path where the converted images/ and labels/ will be written.
    val_split: Fraction of images assigned to the validation split (default 0.15).
    Returns the Path to the generated data.yaml config file.
    """
    print(f"Converting dataset from {dataset_root} to YOLO format at {yolo_root} ...")

    # Create output directory structure for train and val splits
    for split in ('train', 'val'):
        (yolo_root / 'images' / split).mkdir(parents=True, exist_ok=True)
        (yolo_root / 'labels' / split).mkdir(parents=True, exist_ok=True)

    # Build class name map from category.txt, ignoring SKIP_CLASSES
    root_cat_file = dataset_root / 'category.txt'
    name_by_folder = {}
    if root_cat_file.exists():
        for line in root_cat_file.read_text(encoding='utf-8', errors='replace').splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split(None, 1)
            if len(parts) == 2:
                folder_num, food_name = parts[0], parts[1].strip().replace(' ', '_')
                name_by_folder[folder_num] = food_name

    sorted_cat_dirs = sorted(
        [d for d in dataset_root.iterdir() if d.is_dir() and d.name.isdigit()],
        key=lambda p: int(p.name)
    )

    # Assign a contiguous YOLO class index to each kept category
    class_names = []
    cat_id_map = {}  # folder name -> new YOLO class index

    for cat_dir in sorted_cat_dirs:
        name = name_by_folder.get(cat_dir.name, cat_dir.name)
        if name in SKIP_CLASSES:
            continue
        cat_id_map[cat_dir.name] = len(class_names)
        class_names.append(name)

    print(f"Total classes after filtering: {len(class_names)}")

    # Convert bb_info.txt bounding boxes to normalised YOLO label files
    random.seed(42)
    stats = {"train": 0, "val": 0, "skipped": 0}

    for cat_dir in sorted_cat_dirs:
        if cat_dir.name not in cat_id_map:
            continue

        cls_idx = cat_id_map[cat_dir.name]
        bb_file = cat_dir / 'bb_info.txt'
        if not bb_file.exists():
            continue

        # Parse all bounding boxes for each image in this category folder
        lines = bb_file.read_text(encoding='utf-8', errors='replace').splitlines()
        boxes_by_img = {}
        for line in lines[1:]:
            parts = line.split()
            if len(parts) < 5:
                continue
            img_id = parts[0]
            try:
                x1, y1, x2, y2 = map(int, parts[1:5])
            except ValueError:
                continue
            if x2 <= x1 or y2 <= y1:
                continue
            boxes_by_img.setdefault(img_id, []).append((x1, y1, x2, y2))

        for img_id, boxes in boxes_by_img.items():
            img_path = cat_dir / f'{img_id}.jpg'
            if not img_path.exists():
                continue

            try:
                with Image.open(img_path) as im:
                    W, H = im.size
            except Exception:
                continue
            if W == 0 or H == 0:
                continue

            # Randomly assign each image to train or val split
            split = 'val' if random.random() < val_split else 'train'
            unique_stem = f'{cat_dir.name}_{img_id}'
            dst_img = yolo_root / 'images' / split / f'{unique_stem}.jpg'
            dst_lbl = yolo_root / 'labels' / split / f'{unique_stem}.txt'

            shutil.copy2(img_path, dst_img)

            # Normalise pixel coordinates to YOLO cx/cy/w/h format
            yolo_lines = []
            for (x1, y1, x2, y2) in boxes:
                cx, cy = ((x1 + x2) / 2.0) / W, ((y1 + y2) / 2.0) / H
                w, h = (x2 - x1) / W, (y2 - y1) / H
                cx, cy, w, h = [max(0.0, min(1.0, v)) for v in (cx, cy, w, h)]
                if w > 0 and h > 0:
                    yolo_lines.append(f'{cls_idx} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}')

            if yolo_lines:
                dst_lbl.write_text('\n'.join(yolo_lines) + '\n')
                stats[split] += 1
            else:
                dst_img.unlink(missing_ok=True)
                stats["skipped"] += 1

    print(f"Conversion complete: {stats['train']} train, {stats['val']} val images. Skipped {stats['skipped']}.")

    # Write data.yaml config referencing the converted dataset
    data_yaml = {
        'path': str(yolo_root.absolute()),
        'train': 'images/train',
        'val': 'images/val',
        'nc': len(class_names),
        'names': class_names
    }
    with open(yolo_root / 'data.yaml', 'w') as f:
        yaml.dump(data_yaml, f, allow_unicode=True)

    return yolo_root / 'data.yaml'


def main():
    """
    Parse arguments, prepare the dataset, and launch YOLOv8s training.
    Skips extraction and conversion if the YOLO-formatted dataset already exists.
    Trains with early stopping and saves weights under runs/nutriscan_v1/.
    """
    parser = argparse.ArgumentParser(description="Train YOLOv8 on UECFOOD256 with Class Filtering")
    parser.add_argument("--yolo_dir", type=str, default="uec_yolo_filtered", help="Directory for YOLO formatted data")
    parser.add_argument("--zip_file", type=str, default="data/dataset256.zip", help="Path to the dataset zip")
    parser.add_argument("--epochs", type=int, default=400, help="Number of training epochs")
    parser.add_argument("--batch", type=int, default=8, help="Batch size")
    parser.add_argument("--imgsz", type=int, default=640, help="Image size")
    parser.add_argument("--model", type=str, default="yolov8s.pt", help="Pretrained model")

    args = parser.parse_args()

    # Resolve all paths relative to the project root
    project_root = pathlib.Path(__file__).parent.resolve()
    yolo_root = project_root / args.yolo_dir
    zip_path = project_root / args.zip_file

    # Extract and convert only if the YOLO dataset does not already exist
    extract_root = project_root / "UECFOOD256_extracted"

    if not yolo_root.exists():
        if not extract_root.exists():
            if not extract_dataset(zip_path, project_root):
                print(f"Error: Could not find or extract {zip_path}")
                return

            # Locate the UECFOOD256 root folder, renaming if the zip used a different name
            if not (project_root / "UECFOOD256").exists():
                candidates = list(project_root.rglob('bb_info.txt'))
                if candidates:
                    actual_dataset_root = candidates[0].parent.parent
                    actual_dataset_root.rename(project_root / "UECFOOD256")
                else:
                    print("Error: Could not find UECFOOD256 folder after extraction.")
                    return

        # Convert the raw dataset to YOLO format with class filtering applied
        dataset_root = project_root / "UECFOOD256"
        yaml_path = convert_to_yolo(dataset_root, yolo_root)
    else:
        yaml_path = yolo_root / 'data.yaml'

    print(f"Using data.yaml at {yaml_path}")

    # Launch training with the resolved config and CLI arguments
    print(f"Starting training with model {args.model} for {args.epochs} epochs...")
    model = YOLO(args.model)
    model.train(
        data=str(yaml_path.absolute()),
        epochs=args.epochs,
        batch=args.batch,
        imgsz=args.imgsz,
        name="nutriscan_v1",
        project=str(project_root / "runs"),
        exist_ok=True,
        patience=40,
        cache=True,
        device=0,
    )


if __name__ == "__main__":
    main()
