# Authors: Yu Cao, Fan Zhang, Na Yin
# Date: April 2026
# Purpose: NutriScan real-time food detection and
#          nutrition overlay using YOLOv8 and OpenCV.
#          Loads a trained model, runs inference on
#          webcam frames, draws bounding boxes with
#          food labels, and displays aggregated
#          nutrition totals.
"""
NutriScan — food detection + nutrition overlay.

  python src/main.py [--model models/best.pt] [--camera 0] [--conf 0.15]
  python src/main.py --demo

Press 'q' to quit.
"""

import argparse
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

from nutrition import get_nutrition

_NMS_IOU = 0.45
_CROSS_NMS_IOU = 0.7
_FONT = cv2.FONT_HERSHEY_DUPLEX
_BLACK = (0, 0, 0)
_WHITE = (255, 255, 255)
_GRAY = (160, 160, 160)
_GRAY_DONUT = (55, 55, 55)
_APPLE_BLUE = (255, 179, 64)
_STRIP_H = 104
_BBOX_RADIUS = 18
_LABEL_OVERLAP_MARGIN = 2
_LABEL_SHIFT_STEP = 4
# Number of frames a detection is kept alive after
# the model last saw it — prevents flickering
_SMOOTH_FRAMES = 8


class _DetectionCache:
    """
    Temporal smoothing cache using rolling frame history.

    For each box detected in the current frame, searches
    the last max_frames frames for spatially matching boxes
    (IoU > iou_thresh) and promotes the highest-confidence
    label seen at that location.

    Benefits:
    - No ghost boxes: only current-frame boxes are rendered
    - Flicker suppression: best historical label/conf shown
    - False-detection suppression: low-conf misdetections
      are overridden by high-conf historical matches
    """

    def __init__(self, max_frames: int = _SMOOTH_FRAMES,
                 iou_thresh: float = 0.3):
        """
        max_frames  : number of past frames to search.
        iou_thresh  : minimum IoU to consider two boxes
                      as the same spatial location.
        """
        self.max_frames = max_frames
        self.iou_thresh = iou_thresh
        # Each element is a list[dict] for one frame.
        # dict keys: label (str), conf (float),
        #            box (tuple x1,y1,x2,y2)
        self._history: list[list[dict]] = []

    def update(self, current_dets: list[dict]) -> None:
        """
        Push current-frame detections into history queue.
        Drops the oldest frame when queue exceeds max_frames.

        current_dets: list of dicts with keys
                      label, conf, box.
        """
        self._history.append(current_dets)
        if len(self._history) > self.max_frames:
            self._history.pop(0)

    def clear(self) -> None:
        """
        Flush all history (call when scene changes).
        """
        self._history.clear()

    def get_active(self) -> list[dict]:
        """
        Return smoothed detections based on current frame.

        For every box in the most recent frame, scans all
        historical frames for spatially overlapping boxes
        (IoU > iou_thresh). Returns the label and confidence
        of the best match found across the entire history
        window, paired with the current-frame bounding box.

        Returns list of dicts: label, conf, box.
        If the current frame has no detections, returns [].
        """
        if not self._history:
            return []

        # Only render boxes that exist in the current frame
        current_frame = self._history[-1]
        if not current_frame:
            return []

        result = []
        for det in current_frame:
            best_label = det["label"]
            best_conf  = det["conf"]

            # Search all past frames for matching location
            for frame in self._history[:-1]:
                for hist_det in frame:
                    if _iou(det["box"], hist_det["box"]) \
                            > self.iou_thresh:
                        # Same location — promote if better
                        if hist_det["conf"] > best_conf:
                            best_label = hist_det["label"]
                            best_conf  = hist_det["conf"]

            result.append({
                "label": best_label,
                "conf":  best_conf,
                "box":   det["box"],
            })

        return result


def _format_food_display_name(raw: str) -> str:
    """
    Convert an underscored model label to a human-readable display name.
    raw: raw label string from the model (e.g. 'fried_rice').
    Returns the label with underscores replaced by spaces.
    """
    return raw.replace("_", " ").strip()


def _rects_overlap(
        a: tuple[int, int, int, int],
        b: tuple[int, int, int, int],
        margin: int = 0,
) -> bool:
    """
    Check whether two axis-aligned rectangles overlap.
    a, b: (x1, y1, x2, y2) bounding boxes. margin: optional expansion in px.
    Returns True if the rectangles intersect after applying margin.
    """
    ax1, ay1, ax2, ay2 = a[0] - margin, a[1] - margin, a[2] + margin, a[3] + margin
    bx1, by1, bx2, by2 = b[0] - margin, b[1] - margin, b[2] + margin, b[3] + margin
    return not (ax2 <= bx1 or ax1 >= bx2 or ay2 <= by1 or ay1 >= by2)


def _draw_rounded_rect(
        img: np.ndarray,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        color: tuple[int, int, int],
        thickness: int,
        radius: int,
) -> None:
    """
    Draw a rounded-corner rectangle outline on img.
    (x1,y1)-(x2,y2): bounding corners. color: BGR tuple. radius: corner arc radius.
    """
    if x2 <= x1 or y2 <= y1:
        return
    w, h = x2 - x1, y2 - y1
    r = min(radius, w // 2, h // 2)
    lt = cv2.LINE_AA
    if r < 2:
        cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness, lt)
        return
    cv2.line(img, (x1 + r, y1), (x2 - r, y1), color, thickness, lt)
    cv2.line(img, (x1 + r, y2), (x2 - r, y2), color, thickness, lt)
    cv2.line(img, (x1, y1 + r), (x1, y2 - r), color, thickness, lt)
    cv2.line(img, (x2, y1 + r), (x2, y2 - r), color, thickness, lt)
    cv2.ellipse(img, (x1 + r, y1 + r), (r, r), 180, 0, 90, color, thickness, lt)
    cv2.ellipse(img, (x2 - r, y1 + r), (r, r), 270, 0, 90, color, thickness, lt)
    cv2.ellipse(img, (x1 + r, y2 - r), (r, r), 90, 0, 90, color, thickness, lt)
    cv2.ellipse(img, (x2 - r, y2 - r), (r, r), 0, 0, 90, color, thickness, lt)


def _rounded_rect_mask(w: int, h: int, radius: int) -> np.ndarray:
    """
    Create a filled rounded-rectangle binary mask of size (h, w).
    radius: corner rounding in pixels.
    Returns uint8 array with 255 inside the shape and 0 outside.
    """
    m = np.zeros((h, w), dtype=np.uint8)
    if w < 1 or h < 1:
        return m
    r = min(radius, w // 2, h // 2)
    if r < 2:
        m[:, :] = 255
        return m
    lt = cv2.LINE_AA
    cv2.rectangle(m, (r, 0), (w - 1 - r, h - 1), 255, -1, lt)
    cv2.rectangle(m, (0, r), (w - 1, h - 1 - r), 255, -1, lt)
    cv2.ellipse(m, (r, r), (r, r), 180, 0, 90, 255, -1, lt)
    cv2.ellipse(m, (w - 1 - r, r), (r, r), 270, 0, 90, 255, -1, lt)
    cv2.ellipse(m, (r, h - 1 - r), (r, r), 90, 0, 90, 255, -1, lt)
    cv2.ellipse(m, (w - 1 - r, h - 1 - r), (r, r), 0, 0, 90, 255, -1, lt)
    return m


def _blend_dark_capsule(
        frame: np.ndarray, x1: int, y1: int, x2: int, y2: int, radius: int, alpha: float
) -> None:
    """
    Darken a rounded rectangle region on frame in-place (semi-transparent overlay).
    alpha: blend strength in [0, 1]; 1.0 makes the region fully black.
    """
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(frame.shape[1], x2), min(frame.shape[0], y2)
    if x2 <= x1 or y2 <= y1:
        return
    w, h = x2 - x1, y2 - y1
    mask = _rounded_rect_mask(w, h, radius).astype(np.float32) / 255.0
    roi = frame[y1:y2, x1:x2].astype(np.float32)
    m3 = np.stack([mask, mask, mask], axis=-1)
    blended = roi * (1.0 - alpha * m3)
    frame[y1:y2, x1:x2] = blended.astype(np.uint8)


def _draw_food_label_capsule(
        frame: np.ndarray,
        x1: int,
        y1: int,
        y2: int,
        display_name: str,
        conf_pct: int,
        occupied: list[tuple[int, int, int, int]],
) -> None:
    """
    Draw a dark pill showing the food name and confidence above (or below) a box.
    Avoids overlapping previously placed labels by shifting down; clamps to frame.
    occupied: list of already-placed (x1,y1,x2,y2) rects; updated in-place.
    """
    # Measure text sizes to determine capsule dimensions
    # (using a dot glyph instead of U+00B7; Hershey fonts render it as '?')
    scale, thick = 0.55, 1
    name_show = display_name[:32]
    conf_text = f"{conf_pct}%"
    (tw_n, th_n), bl_n = cv2.getTextSize(name_show, _FONT, scale, thick)
    (tw_c, th_c), bl_c = cv2.getTextSize(conf_text, _FONT, scale, thick)
    dot_r = 2
    gbd, gad = 5, 5
    pad_x, pad_y = 14, 9
    r_cap = 16
    bar_w = tw_n + gbd + 2 * dot_r + gad + tw_c + pad_x * 2
    bar_h = max(th_n + bl_n, th_c + bl_c) + pad_y * 2
    fh, fw = frame.shape[0], frame.shape[1]
    gap = 8

    # Horizontal position: left-align with the box, clamped to frame width
    bx1 = max(0, min(int(x1), max(0, fw - bar_w)))
    bx2 = min(fw, bx1 + bar_w)
    if bx2 > fw:
        bx1 = max(0, fw - bar_w)
        bx2 = fw

    # Prefer placing above the box; fall back to below if no room
    if y1 - bar_h >= gap:
        by1, by2 = y1 - bar_h, y1
    else:
        by1, by2 = y2 + gap, y2 + gap + bar_h

    # Shift down to avoid overlapping other labels
    rect = (bx1, by1, bx2, by2)
    mar = _LABEL_OVERLAP_MARGIN
    for _ in range(400):
        if not any(_rects_overlap(rect, o, mar) for o in occupied):
            break
        by1 += _LABEL_SHIFT_STEP
        by2 += _LABEL_SHIFT_STEP
        rect = (bx1, by1, bx2, by2)
        if by2 > fh - 1:
            by2 = fh - 1
            by1 = max(0, by2 - bar_h)
            rect = (bx1, by1, bx2, by2)
            break

    # Clamp final position to stay within frame bounds
    by1 = max(2, min(by1, fh - bar_h - 2))
    by2 = by1 + bar_h

    occupied.append((bx1, by1, bx2, by2))
    _blend_dark_capsule(frame, bx1, by1, bx2, by2, radius=r_cap, alpha=0.85)

    # Draw food name, separator dot, and confidence percentage
    ty = by1 + pad_y + th_n
    tx = bx1 + pad_x
    cv2.putText(frame, name_show, (tx, ty), _FONT, scale, _WHITE, thick, cv2.LINE_AA)
    cx_dot = tx + tw_n + gbd + dot_r
    cy_dot = ty - th_n // 2 + 1
    cv2.circle(frame, (cx_dot, cy_dot), dot_r, _GRAY, -1, cv2.LINE_AA)
    cv2.putText(
        frame, conf_text, (cx_dot + dot_r + gad, ty), _FONT, scale, _GRAY, thick, cv2.LINE_AA
    )


def _draw_kcal_capsule(frame: np.ndarray, x2: int, y2: int, kcal: float) -> None:
    """
    Draw a small calorie badge anchored near the bottom-right corner of a box.
    (x2, y2): bottom-right corner of the detection box. kcal: calorie value.
    """
    scale, thick = 0.34, 1
    text = f"{kcal:.0f} kcal"
    (tw, th), bl = cv2.getTextSize(text, _FONT, scale, thick)
    pad_x, pad_y = 8, 6
    r_cap = 10
    box_w, box_h = tw + pad_x * 2, th + bl + pad_y * 2
    fh, fw = frame.shape[0], frame.shape[1]
    m = 8
    bx2 = min(fw - m, max(m + box_w, x2 - m))
    bx1 = max(0, bx2 - box_w)
    by2 = min(fh - m, max(m + box_h, y2 - m))
    by1 = max(0, by2 - box_h)
    bx2, by2 = min(fw, bx1 + box_w), min(fh, by1 + box_h)
    _blend_dark_capsule(frame, bx1, by1, bx2, by2, radius=r_cap, alpha=0.82)
    cv2.putText(
        frame, text, (bx1 + pad_x, by1 + pad_y + th), _FONT, scale, _WHITE, thick, cv2.LINE_AA
    )


def _ring_segment_mask(
        shape: tuple[int, int],
        cx: int,
        cy: int,
        r_out: int,
        r_in: int,
        ang0: float,
        ang1: float,
) -> np.ndarray:
    """
    Create a donut-segment binary mask for one slice of the macro ring chart.
    ang0, ang1: start/end angles in degrees. Returns uint8 mask of size shape.
    """
    m = np.zeros(shape, dtype=np.uint8)
    cv2.ellipse(m, (cx, cy), (r_out, r_out), 0, ang0, ang1, 255, -1, cv2.LINE_AA)
    cv2.ellipse(m, (cx, cy), (r_in, r_in), 0, 0, 360, 0, -1, cv2.LINE_AA)
    return m


def _draw_macro_donut_on(
        canvas: np.ndarray,
        cx: int,
        cy: int,
        r_out: int,
        r_in: int,
        totals: dict,
) -> None:
    """
    Paint a protein/carbs/fat donut chart directly onto canvas at (cx, cy).
    totals: dict with protein_g, carbs_g, fat_g used to compute arc fractions.
    """
    h, w = canvas.shape[:2]
    pad = r_out + 4
    rx1, ry1 = max(0, cx - pad), max(0, cy - pad)
    rx2, ry2 = min(w, cx + pad), min(h, cy + pad)
    if rx2 <= rx1 or ry2 <= ry1:
        return
    roi = canvas[ry1:ry2, rx1:rx2]
    rcx, rcy = cx - rx1, cy - ry1
    sh = roi.shape[:2]

    # Convert grams to calories to compute proportional arc lengths
    p_cal = totals["protein_g"] * 4.0
    c_cal = totals["carbs_g"] * 4.0
    f_cal = totals["fat_g"] * 9.0
    t = p_cal + c_cal + f_cal
    colors_bgr = [_WHITE, _GRAY_DONUT, _APPLE_BLUE]
    base = np.zeros(sh, dtype=np.uint8)
    cv2.circle(base, (rcx, rcy), r_out, 255, -1, cv2.LINE_AA)
    cv2.circle(base, (rcx, rcy), r_in, 0, -1, cv2.LINE_AA)

    # Draw grey placeholder if no macro data; otherwise paint each segment
    if t < 1.0:
        roi[base > 0] = _GRAY_DONUT
        cv2.circle(roi, (rcx, rcy), r_out, _WHITE, 1, cv2.LINE_AA)
    else:
        angle = 270.0
        for frac, col in zip([p_cal / t, c_cal / t, f_cal / t], colors_bgr):
            sweep = frac * 360.0
            if sweep < 0.5:
                continue
            seg = _ring_segment_mask(sh, rcx, rcy, r_out, r_in, angle, angle + sweep)
            angle += sweep
            roi[seg > 0] = col
        cv2.circle(roi, (rcx, rcy), r_out, _WHITE, 1, cv2.LINE_AA)

    # Punch the centre hole to create the donut shape
    hole = np.zeros(sh, dtype=np.uint8)
    cv2.circle(hole, (rcx, rcy), r_in, 255, -1, cv2.LINE_AA)
    roi[hole > 0] = _BLACK


def _render_nutrition_strip(width: int, totals: dict) -> np.ndarray:
    """
    Build a black footer strip of size (_STRIP_H × width) with calorie and macro info.
    totals: dict with calories, protein_g, carbs_g, fat_g.
    Returns a uint8 BGR array ready to vstack onto the camera frame.
    """
    strip = np.zeros((_STRIP_H, width, 3), dtype=np.uint8)
    strip[:] = _BLACK
    cv2.line(strip, (0, 0), (width - 1, 0), _WHITE, 1, cv2.LINE_AA)

    # Large calorie number on the left
    kcal_str = f"{totals['calories']:.0f}"
    sc_b, th_b = 1.65, 2
    (kw, kh), _ = cv2.getTextSize(kcal_str, _FONT, sc_b, th_b)
    y_num = 28 + kh
    cv2.putText(strip, kcal_str, (28, y_num), _FONT, sc_b, _WHITE, th_b, cv2.LINE_AA)

    sc_s, th_s = 0.48, 1
    cv2.putText(strip, "kcal", (28 + kw + 12, y_num - 4), _FONT, sc_s, _GRAY, th_s, cv2.LINE_AA)

    # Donut chart position (right side) and macro legend column
    r_out, r_in = 34, 20
    cx = width - 56
    cy = _STRIP_H // 2 + 4
    donut_left = cx - r_out

    sc_row, th_row = 0.48, 1
    rows = [
        ("Protein", totals["protein_g"], _WHITE),
        ("Carbs", totals["carbs_g"], _GRAY_DONUT),
        ("Fat", totals["fat_g"], _APPLE_BLUE),
    ]
    max_name_w = max(cv2.getTextSize(n, _FONT, sc_row, th_row)[0][0] for n, _, _ in rows)
    gram_strs = [f"{v:.1f} g" for _, v, _ in rows]
    max_gram_w = max(cv2.getTextSize(g, _FONT, sc_row, th_row)[0][0] for g in gram_strs)

    dot_r = 5
    gap_dot = 9
    gap_name_gram = 12
    col_w = dot_r * 2 + gap_dot + max_name_w + gap_name_gram + max_gram_w
    col_x0 = max(8, donut_left - 12 - col_w)

    # Draw coloured dot, macro name, and gram value for each macronutrient
    line_step = 20
    y0 = cy - line_step
    for i, ((name, val, dcol), grams) in enumerate(zip(rows, gram_strs)):
        yb = y0 + i * line_step
        cxy = (col_x0 + dot_r, yb - 4)
        cv2.circle(strip, cxy, dot_r, dcol, -1, cv2.LINE_AA)
        tx_n = col_x0 + dot_r * 2 + gap_dot
        cv2.putText(strip, name, (tx_n, yb), _FONT, sc_row, _GRAY, th_row, cv2.LINE_AA)
        tx_g = tx_n + max_name_w + gap_name_gram
        cv2.putText(strip, grams, (tx_g, yb), _FONT, sc_row, _WHITE, th_row, cv2.LINE_AA)

    _draw_macro_donut_on(strip, cx, cy, r_out, r_in, totals)
    return strip


def _compose_display(camera_bgr: np.ndarray, totals: dict) -> np.ndarray:
    """
    Stack the camera frame above the nutrition strip to form the final display image.
    totals: aggregated nutrition dict. Returns the combined BGR array.
    """
    return np.vstack([camera_bgr, _render_nutrition_strip(camera_bgr.shape[1], totals)])


def _apply_nms(boxes, iou_threshold: float = _NMS_IOU) -> list[int]:
    """
    Per-class NMS on top of YOLO's built-in suppression to remove stacked duplicates.
    boxes: YOLO Boxes object. iou_threshold: overlap threshold for suppression.
    Returns list of surviving box indices.
    """
    if len(boxes) == 0:
        return []

    # Group box indices by class so NMS runs independently per category
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

        # cv2.dnn.NMSBoxes handles the actual suppression within each class
        survivors = cv2.dnn.NMSBoxes(
            bboxes_xywh, scores, score_threshold=0.0, nms_threshold=iou_threshold,
        )
        for idx in np.array(survivors).flatten():
            kept.append(indices[int(idx)])

    return kept


def _iou(a: list, b: list) -> float:
    """
    Compute Intersection-over-Union for two xyxy boxes.
    a, b: [x1, y1, x2, y2] pixel coordinates.
    Returns float in [0, 1].
    """
    ix1 = max(a[0], b[0])
    iy1 = max(a[1], b[1])
    ix2 = min(a[2], b[2])
    iy2 = min(a[3], b[3])

    inter_w = max(0.0, ix2 - ix1)
    inter_h = max(0.0, iy2 - iy1)
    intersection = inter_w * inter_h

    area_a = (a[2] - a[0]) * (a[3] - a[1])
    area_b = (b[2] - b[0]) * (b[3] - b[1])
    union = area_a + area_b - intersection

    return intersection / union if union > 0.0 else 0.0


def _apply_cross_class_nms(
    boxes,
    indices: list[int],
    iou_threshold: float = _CROSS_NMS_IOU,
) -> list[int]:
    """
    Greedy cross-class NMS: suppresses lower-confidence boxes that overlap a keeper.
    boxes: YOLO Boxes object. indices: candidate indices (output of _apply_nms).
    Returns filtered list of indices with cross-class overlaps removed.
    """
    if len(indices) <= 1:
        return indices

    # Sort descending by confidence so the strongest detection wins ties
    order = sorted(indices, key=lambda i: float(boxes[i].conf[0]), reverse=True)

    suppressed = set()
    kept: list[int] = []

    for pos, idx in enumerate(order):
        if idx in suppressed:
            continue

        kept.append(idx)
        box_i = boxes[idx].xyxy[0].tolist()

        # Suppress every remaining lower-confidence box that overlaps this one
        for idx_j in order[pos + 1 :]:
            if idx_j in suppressed:
                continue
            box_j = boxes[idx_j].xyxy[0].tolist()
            if _iou(box_i, box_j) > iou_threshold:
                suppressed.add(idx_j)

    return kept


def _resolve_model_weights(model_path: str) -> str:
    """
    Resolve model_path to an absolute file path or a YOLO hub name for auto-download.
    Searches relative to cwd and the repo root before raising FileNotFoundError.
    Returns a resolved string path or hub name.
    """
    raw = model_path.strip()
    p = Path(raw)
    repo_root = Path(__file__).resolve().parent.parent
    for c in (p, Path.cwd() / p, repo_root / p):
        try:
            if c.is_file():
                return str(c.resolve())
        except OSError:
            continue
    base = raw.replace("\\", "/").split("/")[-1]
    if "/" not in raw.replace("\\", "/") and base.endswith(".pt"):
        if base.startswith("yolov8") or base.startswith("yolo11"):
            return base
    raise FileNotFoundError(
        f"Model not found: {model_path}\n"
        "Train on UEC FOOD-256 (see README / train_v2.ipynb), save weights as models/best.pt, "
        "or preview the overlay UI with a pretrained COCO model (not food-specific):\n"
        "  python src/main.py --demo\n"
        "  python src/main.py --model yolov8n.pt"
    )


def run(model_path: str, camera_index: int, conf_threshold: float) -> None:
    """
    Load the model and run the real-time detection loop on the given camera.
    model_path: path to .pt weights. camera_index: cv2 device index.
    conf_threshold: minimum detection confidence. Blocks until 'q' is pressed.
    """
    model = YOLO(_resolve_model_weights(model_path))
    class_names = model.names

    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open camera index {camera_index}.")

    print("NutriScan running — press 'q' to quit.")

    # Initialise temporal smoothing cache
    cache = _DetectionCache()

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame.")
            break

        # Run inference and apply two-pass NMS
        results = model(frame, conf=conf_threshold, verbose=False)[0]
        kept = _apply_nms(results.boxes)
        kept = _apply_cross_class_nms(results.boxes, kept)

        # Discard detections that cover more than 70% of the frame (likely false positives)
        fh, fw = frame.shape[:2]
        frame_area = fh * fw
        filtered = []
        for i in kept:
            x1, y1, x2, y2 = map(int, results.boxes[i].xyxy[0].tolist())
            box_area = (x2 - x1) * (y2 - y1)
            if box_area / frame_area <= 0.70:
                filtered.append(i)
        kept = filtered

        # Build detection list from NMS results this frame
        current_dets = []
        for i in kept:
            box    = results.boxes[i]
            cls_id = int(box.cls[0])
            conf   = float(box.conf[0])
            label  = class_names.get(cls_id, str(cls_id))
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            current_dets.append({
                "label": label,
                "conf":  conf,
                "box":   (x1, y1, x2, y2),
            })

        # Update temporal smoothing cache
        cache.update(current_dets)

        # Draw all active detections (current + smoothed)
        totals = {"calories": 0.0, "protein_g": 0.0,
                  "carbs_g": 0.0, "fat_g": 0.0}
        label_placed: list[tuple[int, int, int, int]] = []
        seen_labels: set[str] = set()

        for det in cache.get_active():
            label = det["label"]
            conf  = det["conf"]
            x1, y1, x2, y2 = det["box"]

            # Draw bounding box and nutrition label
            _draw_rounded_rect(frame, x1, y1, x2, y2,
                               _WHITE, 1, _BBOX_RADIUS)
            nutrients  = get_nutrition(label)
            conf_pct   = int(round(conf * 100))
            _draw_food_label_capsule(
                frame, x1, y1, y2,
                _format_food_display_name(label),
                conf_pct, label_placed,
            )
            _draw_kcal_capsule(frame, x2, y2,
                               float(nutrients.get("calories", 0.0)))

            # Accumulate nutrition totals (deduplicated)
            if label not in seen_labels:
                seen_labels.add(label)
                print(f"[detect] {label} ({conf:.0%})")
                for k in totals:
                    totals[k] += nutrients.get(k, 0.0)

        cv2.imshow("NutriScan", _compose_display(frame, totals))
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NutriScan real-time food detector")
    parser.add_argument("--model", default="models/best.pt", help="Path to YOLOv8 weights")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Use yolov8n.pt (COCO) to preview the UI; first run downloads weights",
    )
    parser.add_argument("--camera", type=int, default=0, help="Camera device index")
    parser.add_argument("--conf", type=float, default=0.20, help="Detection confidence threshold")
    args = parser.parse_args()
    run("yolov8n.pt" if args.demo else args.model, args.camera, args.conf)
