from pathlib import Path


RGB_MODEL = Path("models/rgb/rgb_disaster.pt")
THERMAL_MODEL = Path("models/thermal/thermal_human.pt")


print("ELIOS-SAR model check")
print("---------------------")

print("RGB model:")
print(f"  {RGB_MODEL}")
print(f"  Exists: {RGB_MODEL.exists()}")

print()

print("Thermal model:")
print(f"  {THERMAL_MODEL}")
print(f"  Exists: {THERMAL_MODEL.exists()}")

if not RGB_MODEL.exists():
    print("\nERROR: RGB model is missing.")

if not THERMAL_MODEL.exists():
    print("\nERROR: Thermal model is missing.")

if RGB_MODEL.exists() and THERMAL_MODEL.exists():
    print("\nAll model files found.")
