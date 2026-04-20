# compose_food_images.py
# Authors: Yu Cao, Na Yin, Fan Zhang
# Date: April 20, 2026
# Purpose: Compose multiple single-food images from the UEC FOOD 256 dataset
#          into one image containing 2-3 food categories for visual demo use.
#          Category names are loaded from a classes_v2.txt file.
#
# Usage:
#     python compose_food_images.py --data_dir /path/to/UECFOOD256 --classes classes_v2.txt --num_images 10
#
# Dependencies: Pillow (pip install Pillow)

import random
import argparse
from pathlib import Path
from PIL import Image


def load_class_names(classes_file):
    """Load category names from a text file where each line corresponds to
    a category (line 1 = category 1, line 2 = category 2, etc.).

    Args:
        classes_file (str): Path to the classes text file.

    Returns:
        dict: Mapping from category folder name (str) to food name (str).
              e.g. {"1": "eels_on_rice", "2": "pilaf", ...}
    """
    class_map = {}
    with open(classes_file, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f, start=1):
            name = line.strip()
            if name:
                class_map[str(idx)] = name
    return class_map


def get_category_dirs(data_dir):
    """Scan the dataset root directory and return a sorted list of category
    folder paths that contain at least one image file.

    Args:
        data_dir (str): Root directory of the UEC FOOD 256 dataset.

    Returns:
        list[Path]: Sorted list of category directory paths.
    """
    dirs = []
    for d in Path(data_dir).iterdir():
        if d.is_dir() and d.name.isdigit():
            imgs = list(d.glob("*.jpg")) + list(d.glob("*.png")) + list(d.glob("*.jpeg"))
            if imgs:
                dirs.append(d)
    return sorted(dirs, key=lambda x: int(x.name))


def pick_random_image(category_dir):
    """Randomly select one image file from a given category folder.

    Args:
        category_dir (Path): Path to a category subdirectory.

    Returns:
        Path: Path to the selected image file.
    """
    # Collect all image files and filter out non-image files like bb_info.txt
    imgs = list(category_dir.glob("*.jpg")) + \
           list(category_dir.glob("*.png")) + \
           list(category_dir.glob("*.jpeg"))
    imgs = [p for p in imgs if p.suffix.lower() in (".jpg", ".jpeg", ".png")]
    return random.choice(imgs)


def compose_horizontal(images, canvas_h=400, gap=20):
    """Compose multiple images side by side horizontally on a white canvas.
    All images are scaled to the same height while preserving aspect ratio.

    Args:
        images (list[Image.Image]): List of PIL images to compose.
        canvas_h (int): Target height in pixels for all images.
        gap (int): Horizontal spacing in pixels between images.

    Returns:
        Image.Image: The composed image.
    """
    # Resize all images to the same height
    resized = []
    for img in images:
        ratio = canvas_h / img.height
        new_w = int(img.width * ratio)
        resized.append(img.resize((new_w, canvas_h), Image.LANCZOS))

    # Create a white canvas wide enough to hold all images plus gaps
    total_w = sum(r.width for r in resized) + gap * (len(resized) - 1)
    canvas = Image.new("RGB", (total_w, canvas_h), (255, 255, 255))

    # Paste each image at the correct horizontal offset
    x_offset = 0
    for r in resized:
        canvas.paste(r, (x_offset, 0))
        x_offset += r.width + gap

    return canvas


def compose_grid(images, cell_size=400, gap=20):
    """Compose multiple images in a grid layout on a white canvas.
    Layout: 2 images -> 1x2, 3 images -> 2x2 with one cell left blank.
    Each image is scaled to fit within its cell while preserving aspect ratio.

    Args:
        images (list[Image.Image]): List of PIL images to compose.
        cell_size (int): Width and height in pixels for each grid cell.
        gap (int): Spacing in pixels between cells.

    Returns:
        Image.Image: The composed image.
    """
    # Determine grid dimensions based on image count
    n = len(images)
    if n <= 2:
        cols, rows = n, 1
    else:
        cols, rows = 2, 2

    # Create white canvas
    canvas_w = cols * cell_size + (cols - 1) * gap
    canvas_h = rows * cell_size + (rows - 1) * gap
    canvas = Image.new("RGB", (canvas_w, canvas_h), (255, 255, 255))

    # Place each image centered within its grid cell
    for i, img in enumerate(images):
        row, col = divmod(i, cols)

        # Scale image to fit inside the cell
        ratio = min(cell_size / img.width, cell_size / img.height)
        new_w, new_h = int(img.width * ratio), int(img.height * ratio)
        resized = img.resize((new_w, new_h), Image.LANCZOS)

        # Center the image in the cell
        x = col * (cell_size + gap) + (cell_size - new_w) // 2
        y = row * (cell_size + gap) + (cell_size - new_h) // 2
        canvas.paste(resized, (x, y))

    return canvas


def main():
    """Parse command-line arguments, load class names, select random food
    categories and images, compose them into multi-food images, and save
    results to disk."""

    # Set up command-line argument parser
    parser = argparse.ArgumentParser(description="Compose multi-food images from UEC FOOD 256")
    parser.add_argument("--data_dir", type=str, required=True,
                        help="Root directory of the UEC FOOD 256 dataset")
    parser.add_argument("--classes", type=str, required=True,
                        help="Path to classes_v2.txt (one class name per line)")
    parser.add_argument("--output_dir", type=str, default="./composed_images",
                        help="Output directory (default: ./composed_images)")
    parser.add_argument("--num_images", type=int, default=10,
                        help="Number of composed images to generate (default: 10)")
    parser.add_argument("--foods_per_image", type=int, default=None,
                        help="Number of food categories per image (default: random 2-3)")
    parser.add_argument("--layout", type=str, choices=["horizontal", "grid"], default="grid",
                        help="Layout style: horizontal or grid (default: grid)")
    parser.add_argument("--cell_size", type=int, default=400,
                        help="Cell size in pixels for grid layout (default: 400)")
    parser.add_argument("--seed", type=int, default=None,
                        help="Random seed for reproducibility")
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    # Load category name mapping from classes file
    class_map = load_class_names(args.classes)
    print(f"Loaded {len(class_map)} class names from {args.classes}")

    # Discover all available category folders
    category_dirs = get_category_dirs(args.data_dir)
    print(f"Found {len(category_dirs)} category folders in {args.data_dir}")

    if len(category_dirs) < 2:
        print("Error: need at least 2 category folders with images")
        return

    # Create output directory if it does not exist
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate each composed image
    for i in range(args.num_images):
        # Decide how many food categories to include
        n_foods = args.foods_per_image if args.foods_per_image else random.choice([2, 3])

        # Randomly sample distinct categories
        chosen_cats = random.sample(category_dirs, n_foods)

        # Load one random image from each chosen category
        images = []
        folder_ids = []
        food_names = []
        for cat_dir in chosen_cats:
            img_path = pick_random_image(cat_dir)
            img = Image.open(img_path).convert("RGB")
            images.append(img)
            folder_ids.append(cat_dir.name)
            # Look up the human-readable food name from classes file
            food_names.append(class_map.get(cat_dir.name, f"unknown_{cat_dir.name}"))

        # Compose images using the selected layout
        if args.layout == "horizontal":
            composed = compose_horizontal(images)
        else:
            composed = compose_grid(images, cell_size=args.cell_size)

        # Save with a descriptive filename that includes food names
        name_str = "__".join(food_names)
        filename = f"composed_{i+1:03d}__{name_str}.jpg"
        save_path = output_dir / filename
        composed.save(save_path, quality=95)
        print(f"[{i+1}/{args.num_images}] Saved: {filename}")

    print(f"\nDone! Generated {args.num_images} composed images in: {output_dir}")


if __name__ == "__main__":
    main()
