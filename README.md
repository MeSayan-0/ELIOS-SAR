# ELIOS-SAR

**Edge-Linked Intelligent Observation System for Search and Rescue**

Phase 1 validates two independent detectors before any RGB–thermal fusion:

- RGB disaster detector: `civilian`, `rescuer`, and supported animal classes.
- Thermal human detector: `human`.

## Project layout

```text
models/rgb/rgb_disaster.pt
models/thermal/thermal_human.pt
test_images/rgb_test.jpg
test_images/thermal_test.jpg
test_videos/rgb_test.mp4
src/
results/
```

## Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Place the licensed custom checkpoints at the paths above, then run:

```powershell
python src/check_models.py
python src/test_rgb.py
python src/test_thermal.py
```

Do not proceed to fusion until both checks and image tests succeed.
