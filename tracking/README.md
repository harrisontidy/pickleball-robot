# Prototype ball tracker

`ball_tracker.py` is the current non-YOLO prototype for detecting a blue pickleball from a webcam.

It uses colour segmentation, frame-to-frame motion, a Kalman filter for short prediction, and optical flow when the colour signal briefly disappears. It does not require a trained model or Roboflow credentials.

## Run

```powershell
python -m pip install -r tracking/requirements.txt
python tracking/ball_tracker.py
```

Press `q` to quit. The script opens a camera view and a binary detection-mask window.

PyTorch with a CUDA-compatible installation is optional. If it is unavailable, the tracker runs on the CPU.
