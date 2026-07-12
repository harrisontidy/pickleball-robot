"""
Blue ball tracker — color + motion + prediction (no YOLO).

Tuned for moving / motion-blurred balls:
  - frame-difference motion mask
  - relaxed blue thresholds while tracking
  - morphological close to merge blur streaks
  - Kalman coast + optical-flow backup when color drops out
"""

import math
import time
from collections import deque

import cv2
import numpy as np

# --- Settings ---
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
DETECT_SCALE = 0.5
USE_GPU = True

# Normal blue range
BLUE_LOWER = np.array([100, 120, 50], dtype=np.float32)
BLUE_UPPER = np.array([130, 255, 255], dtype=np.float32)
# Wider range when tracking / motion blur kills saturation
BLUE_LOWER_TRACK = np.array([95, 70, 35], dtype=np.float32)

MIN_BALL_AREA = 15
MAX_BALL_AREA = 15000
MIN_RADIUS = 2
MAX_RADIUS = 120
MIN_CIRCULARITY = 0.38
MIN_CIRCULARITY_MOVING = 0.22  # blur smears ball into a streak

TRAIL_LENGTH = 25
SEARCH_RADIUS_PX = 200
MAX_COAST_FRAMES = 12  # keep predicting this many frames without color hit
MOTION_THRESH = 16

trail = deque(maxlen=TRAIL_LENGTH)
fps_prev_time = time.perf_counter()
display_fps = 0.0
velocity = (0.0, 0.0)
speed = 0.0
tracking_state = "search"
backend_label = "cpu"
lost_frames = 0

prev_gray_small = None
last_flow_point = None  # (x, y) in full-frame coords

_morph_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
_close_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
_torch = None
_device = None


def init_gpu():
    global _torch, _device, backend_label, USE_GPU

    if not USE_GPU:
        backend_label = "cpu (forced)"
        return False

    try:
        import torch

        _torch = torch
        if torch.cuda.is_available():
            _device = torch.device("cuda")
            backend_label = f"cuda ({torch.cuda.get_device_name(0)})"
            return True
        backend_label = "cpu (no cuda)"
        return False
    except ImportError:
        backend_label = "cpu (no torch)"
        return False


def create_kalman():
    kf = cv2.KalmanFilter(4, 2)
    kf.transitionMatrix = np.eye(4, dtype=np.float32)
    kf.measurementMatrix = np.array([[1, 0, 0, 0], [0, 1, 0, 0]], np.float32)
    kf.processNoiseCov = np.diag([2e-1, 2e-1, 2e0, 2e0]).astype(np.float32)
    kf.measurementNoiseCov = np.diag([8e-2, 8e-2]).astype(np.float32)
    kf.errorCovPost = np.eye(4, dtype=np.float32)
    return kf


kalman = create_kalman()
kalman_ready = False


def to_detect(frame):
    if DETECT_SCALE == 1.0:
        return frame
    w = int(frame.shape[1] * DETECT_SCALE)
    h = int(frame.shape[0] * DETECT_SCALE)
    return cv2.resize(frame, (w, h), interpolation=cv2.INTER_LINEAR)


def bgr_to_hsv_torch(bgr):
    t = _torch
    b = bgr[..., 0].float()
    g = bgr[..., 1].float()
    r = bgr[..., 2].float()

    mx = _torch.max(bgr.float(), dim=-1).values
    mn = _torch.min(bgr.float(), dim=-1).values
    diff = mx - mn

    h = _torch.zeros_like(mx)
    s = _torch.where(mx > 0, diff / mx, _torch.zeros_like(mx))
    v = mx / 255.0

    valid = diff > 1e-5
    rc = (((g - b) / diff) % 6.0)
    gc = ((b - r) / diff) + 2.0
    bc = ((r - g) / diff) + 4.0

    h = _torch.where((mx == r) & valid, rc, h)
    h = _torch.where((mx == g) & valid, gc, h)
    h = _torch.where((mx == b) & valid, bc, h)
    h = (h / 6.0) % 1.0

    return _torch.stack([h * 179.0, s * 255.0, v * 255.0], dim=-1)


def build_color_mask(small_bgr, relaxed=False):
    lo = BLUE_LOWER_TRACK if relaxed else BLUE_LOWER
    hi = BLUE_UPPER

    if _device is not None:
        t = _torch
        tensor = t.from_numpy(small_bgr).to(_device)
        hsv = bgr_to_hsv_torch(tensor)
        lo_t = t.from_numpy(lo).to(_device)
        hi_t = t.from_numpy(hi).to(_device)
        mask = t.all((hsv >= lo_t) & (hsv <= hi_t), dim=-1)
        mask = (mask.to(t.uint8) * 255).cpu().numpy()
    else:
        hsv = cv2.cvtColor(small_bgr, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, lo.astype(np.uint8), hi.astype(np.uint8))

    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, _morph_kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, _close_kernel, iterations=1)
    return mask


def build_motion_mask(small_gray):
    global prev_gray_small

    if prev_gray_small is None:
        prev_gray_small = small_gray.copy()
        return np.zeros_like(small_gray)

    diff = cv2.absdiff(small_gray, prev_gray_small)
    _, motion = cv2.threshold(diff, MOTION_THRESH, 255, cv2.THRESH_BINARY)
    prev_gray_small = small_gray.copy()

    motion = cv2.dilate(motion, _morph_kernel, iterations=1)
    return motion


def fuse_masks(color_mask, motion_mask, tracking):
    if not tracking:
        return color_mask

    # Moving ball: accept blue OR (moving blob that touches blue — blur streak case)
    color_dilated = cv2.dilate(color_mask, _close_kernel, iterations=1)
    motion_near_color = cv2.bitwise_and(motion_mask, color_dilated)
    return cv2.bitwise_or(color_mask, motion_near_color)


def circularity(contour):
    area = cv2.contourArea(contour)
    if area <= 0:
        return 0.0
    perimeter = cv2.arcLength(contour, True)
    if perimeter <= 0:
        return 0.0
    return 4.0 * math.pi * area / (perimeter * perimeter)


def motion_overlap(contour, motion_mask):
    blob = np.zeros_like(motion_mask)
    cv2.drawContours(blob, [contour], -1, 255, -1)
    moving = cv2.countNonZero(cv2.bitwise_and(blob, motion_mask))
    total = cv2.countNonZero(blob)
    if total == 0:
        return 0.0
    return moving / total


def _state_xy(state):
    return float(state[0, 0]), float(state[1, 0])


def _state_xyv(state):
    return float(state[0, 0]), float(state[1, 0]), float(state[2, 0]), float(state[3, 0])


def kalman_predict(dt):
    kalman.transitionMatrix = np.array(
        [[1, 0, dt, 0], [0, 1, 0, dt], [0, 0, 1, 0], [0, 0, 0, 1]], dtype=np.float32
    )
    state = kalman.predict()
    return _state_xyv(state)


def kalman_correct(x, y):
    global kalman_ready, velocity, speed, lost_frames, last_flow_point
    lost_frames = 0
    last_flow_point = (x, y)

    if not kalman_ready:
        kalman.statePre = np.array([[x], [y], [0], [0]], dtype=np.float32)
        kalman.statePost = kalman.statePre.copy()
        kalman_ready = True
        velocity = (0.0, 0.0)
        speed = 0.0
        return x, y

    state = kalman.correct(np.array([[x], [y]], dtype=np.float32))
    px, py, vx, vy = _state_xyv(state)
    velocity = (vx, vy)
    speed = math.hypot(vx, vy)
    return px, py


def optical_flow_backup(prev_gray, curr_gray, scale):
    """Track last position through blur when color mask fails."""
    global last_flow_point

    if last_flow_point is None or prev_gray is None:
        return None

    px = int(last_flow_point[0] * scale)
    py = int(last_flow_point[1] * scale)
    h, w = curr_gray.shape[:2]
    pad = 48
    x1, y1 = max(0, px - pad), max(0, py - pad)
    x2, y2 = min(w, px + pad), min(h, py + pad)
    if x2 <= x1 or y2 <= y1:
        return None

    local_x, local_y = px - x1, py - y1
    pts = np.array([[[local_x, local_y]]], dtype=np.float32)
    next_pts, status, _ = cv2.calcOpticalFlowPyrLK(
        prev_gray[y1:y2, x1:x2], curr_gray[y1:y2, x1:x2], pts, None
    )

    if status is None or status[0][0] != 1:
        return None

    nx = float(next_pts[0, 0, 0] + x1) / scale
    ny = float(next_pts[0, 0, 1] + y1) / scale
    last_flow_point = (nx, ny)
    return nx, ny, 12.0


def pick_contour(contours, motion_mask, predicted, search_r, min_circ, scale):
    min_area = MIN_BALL_AREA * scale * scale
    max_area = MAX_BALL_AREA * scale * scale
    min_r = MIN_RADIUS * scale
    max_r = MAX_RADIUS * scale
    use_prediction = predicted is not None

    best = None
    best_score = -1.0

    for contour in contours:
        area = cv2.contourArea(contour)
        if area < min_area or area > max_area:
            continue

        circ = circularity(contour)
        if circ < min_circ:
            continue

        (x, y), radius = cv2.minEnclosingCircle(contour)
        if radius < min_r or radius > max_r:
            continue

        m_frac = motion_overlap(contour, motion_mask)
        score = circ * math.sqrt(area) + m_frac * 30.0

        if use_prediction:
            dist = math.hypot(x - predicted[0], y - predicted[1])
            if dist > search_r:
                continue
            score += (1.0 - dist / search_r) * 60.0
            if m_frac > 0.15:
                score += 20.0

        if score > best_score:
            best_score = score
            best = (x, y, radius)

    return best


def find_ball(frame, dt):
    global tracking_state, lost_frames, prev_gray_small

    scale = DETECT_SCALE
    small = to_detect(frame)
    small_gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    old_gray = prev_gray_small.copy() if prev_gray_small is not None else None

    tracking = tracking_state in ("track", "predict")
    relaxed = tracking or speed > 80.0

    color_mask = build_color_mask(small, relaxed=relaxed)
    motion_mask = build_motion_mask(small_gray)
    mask = fuse_masks(color_mask, motion_mask, tracking)

    pred_x = pred_y = None
    predicted = None
    if kalman_ready:
        pred_x, pred_y, _, _ = kalman_predict(dt)
        predicted = (pred_x * scale, pred_y * scale)

    search_r = (SEARCH_RADIUS_PX + speed * 0.12) * scale
    min_circ = MIN_CIRCULARITY_MOVING if (speed > 60 or tracking) else MIN_CIRCULARITY

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    best = pick_contour(contours, motion_mask, predicted, search_r, min_circ, scale)

    if best is None and kalman_ready and lost_frames < MAX_COAST_FRAMES:
        flow_hit = optical_flow_backup(old_gray, small_gray, scale)
        if flow_hit is not None:
            x, y, radius = flow_hit
            kalman_correct(x, y)
            tracking_state = "track"
            return (x, y, radius), mask, "flow"

    if best is None:
        lost_frames += 1
        if kalman_ready and lost_frames <= MAX_COAST_FRAMES:
            tracking_state = "predict"
            return (pred_x, pred_y, max(4.0, speed / 35.0)), mask, "predict"
        tracking_state = "search"
        lost_frames = 0
        prev_gray_small = None
        return None, mask, "search"

    x, y, radius = best
    x /= scale
    y /= scale
    radius /= scale

    kalman_correct(x, y)
    tracking_state = "track"
    return (x, y, radius), mask, "track"


def draw_overlay(frame, x, y, radius, method):
    center = (int(x), int(y))
    trail.appendleft(center)

    colors = {"track": (0, 255, 0), "predict": (0, 200, 255), "flow": (255, 200, 0)}
    color = colors.get(method, (0, 255, 0))
    cv2.circle(frame, center, max(2, int(radius)), color, 2)
    cv2.circle(frame, center, 3, (0, 0, 255), -1)

    if kalman_ready and method == "predict":
        cv2.circle(frame, center, 8, (255, 255, 0), 1)

    for i in range(1, len(trail)):
        cv2.line(frame, trail[i - 1], trail[i], (255, 0, 0), 1)

    vx, vy = velocity
    lines = [
        f"x: {int(x)} px",
        f"y: {int(y)} px",
        f"vx: {vx:+.0f}  vy: {vy:+.0f} px/s",
        f"speed: {speed:.0f} px/s",
        f"fps: {display_fps:.1f}",
        f"mode: {method}  |  {backend_label}",
    ]
    for i, text in enumerate(lines):
        cv2.putText(frame, text, (10, 26 + i * 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)


def main():
    global fps_prev_time, display_fps

    gpu_ok = init_gpu()
    print(f"Blue ball color tracker  |  backend: {backend_label}")
    if USE_GPU and not gpu_ok:
        print("Tip: pip install torch with CUDA if you want GPU acceleration.")

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    cap.set(cv2.CAP_PROP_FPS, 60)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)

        now = time.perf_counter()
        dt = now - fps_prev_time
        fps_prev_time = now
        if dt > 0:
            display_fps = 0.9 * display_fps + 0.1 * (1.0 / dt)

        result, mask, method = find_ball(frame, dt)

        if result is not None:
            draw_overlay(frame, *result, method)
        else:
            cv2.putText(
                frame,
                f"blue ball not found  |  fps: {display_fps:.1f}",
                (10, 28),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 0, 255),
                2,
            )

        cv2.imshow("Blue Ball Tracker (color)", frame)
        cv2.imshow("Mask", mask)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
