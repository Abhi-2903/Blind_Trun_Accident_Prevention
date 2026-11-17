# Blind Turn / U-Turn Accident Prevention System

A computer-vision based system for detecting vehicles near blind turns and estimating the risk of a possible collision.

## Features

- Vehicle detection using YOLO
- Vehicle tracking using ByteTrack
- Vehicle speed estimation
- Vehicle direction estimation
- Blind-turn ROI detection
- Collision-risk analysis
- Time To Collision (TTC)
- SAFE / CAUTION / DANGER warning
- Processed video output

## Tech Stack

- Python
- OpenCV
- YOLO / Ultralytics
- ByteTrack
- NumPy
- JSON

## Project Structure

```text
BlindTurnProject/
│
├── main.py
├── config.py
├── detector.py
├── tracker.py
├── speed_estimator.py
├── roi.py
├── collision_detector.py
├── calibration.py
├── select_roi.py
│
├── input/
│   └── road_video.mp4
│
├── output/
│   └── processed_video.mp4
│
├── calibration.json
├── roi.json
├── homography.json
├── requirements.txt
├── README.md
└── .gitignore
```

## Installation

### 1. Create virtual environment

```powershell
python -m venv venv
```

### 2. Activate it

```powershell
venv\Scripts\activate
```

### 3. Install dependencies

```powershell
python -m pip install ultralytics opencv-python numpy
```

## Setup

Before running `main.py`, configure the road video and calibration/ROI.

### 1. Add input video

Put your road video here:

```text
input/road_video.mp4
```

### 2. Run calibration

Run the calibration script:

```powershell
python calibration.py
```

This creates/updates the calibration information used for approximate real-world distance and speed estimation.

### 3. Select Blind Turn ROI

Run:

```powershell
python select_roi.py
```

Select the blind-turn region in the video.

This creates/updates:

```text
roi.json
```

### 4. Run the main system

After calibration and ROI selection:

```powershell
python main.py
```

The processed video will be saved to:

```text
output/processed_video.mp4
```

## Working

```text
Road Video
     ↓
OpenCV
     ↓
YOLO Vehicle Detection
     ↓
ByteTrack Tracking
     ↓
Vehicle ID + Position
     ↓
Speed + Direction
     ↓
Blind Turn ROI
     ↓
Collision Risk Analysis
     ↓
TTC Calculation
     ↓
SAFE / CAUTION / DANGER
     ↓
Processed Video
```

## Risk Levels

### SAFE

No significant collision risk is detected.

### CAUTION

Vehicles are approaching a potentially risky situation or the estimated TTC enters the caution range.

### DANGER

The estimated collision risk is high and the TTC is below the configured danger threshold.

The system uses multiple consecutive frames before confirming DANGER to reduce false warnings.

## Important Configuration

Main settings are available in:

```text
config.py
```

Examples:

```python
CONFIDENCE_THRESHOLD = 0.4
METERS_PER_PIXEL = 0.03

TTC_DANGER = 2.0
TTC_CAUTION = 5.0

MIN_CLOSING_SPEED_MPS = 0.5
MAX_PAIR_DISTANCE_M = 80
DANGER_CONFIRM_FRAMES = 3
```

Calibration values can be loaded automatically from:

```text
calibration.json
```

and the blind-turn polygon from:

```text
roi.json
```

## Output

The processed video can show:

- Vehicle bounding boxes
- Vehicle IDs
- Speed
- Direction
- Blind-turn zone
- Vehicle risk information
- TTC
- `STATUS: SAFE`
- `STATUS: CAUTION`
- `STATUS: DANGER`

## Troubleshooting

### `pip` is blocked

Use:

```powershell
python -m pip install ultralytics opencv-python numpy
```

instead of:

```powershell
pip install ...
```

### ROI is not showing

Run:

```powershell
python select_roi.py
```

and make sure `roi.json` is generated correctly.

### Calibration is not available

Run:

```powershell
python calibration.py
```

before running `main.py`.

### DANGER is not appearing

Check:

- Both vehicles are being tracked.
- Vehicle directions are correct.
- Vehicles are actually approaching each other.
- ROI is correctly selected.
- Calibration is reasonable.
- TTC thresholds in `config.py` are appropriate.

## GitHub

Do not upload the virtual environment.

Recommended `.gitignore`:

```gitignore
venv/
.venv/
__pycache__/
*.pyc
input/*.mp4
output/*.mp4
.env
```

Create `requirements.txt` with:

```powershell
python -m pip freeze > requirements.txt
```

## Project Status

- [x] YOLO vehicle detection
- [x] ByteTrack tracking
- [x] Speed estimation
- [x] Direction estimation
- [x] Blind-turn ROI
- [x] Collision detection
- [x] TTC calculation
- [x] SAFE / CAUTION / DANGER warning
- [x] Processed video generation

## Future Work

- Live camera input
- Real-time buzzer/LED warning
- Improved road calibration
- Better collision prediction
- Hardware implementation
- Real-world mountain-road testing
- Edge-device deployment
