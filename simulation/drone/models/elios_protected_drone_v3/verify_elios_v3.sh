#!/usr/bin/env bash
set -euo pipefail
MODEL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODEL="$MODEL_DIR/model.sdf"

command -v xmllint >/dev/null 2>&1 || { echo "ERROR: xmllint not found. Install: sudo apt install libxml2-utils"; exit 1; }
[[ -f "$MODEL" ]] || { echo "ERROR: $MODEL not found"; exit 1; }

xmllint --noout "$MODEL"
for n in 0 1 2 3; do grep -q "<actuator_number>$n</actuator_number>" "$MODEL" || { echo "ERROR: missing actuator $n"; exit 1; }; done
! grep -q 'MotorFailurePlugin' "$MODEL"
! grep -q '<motorNumber>' "$MODEL"
for sensor in imu_sensor air_pressure_sensor magnetometer_sensor navsat_sensor; do grep -q "<sensor name=\"$sensor\"" "$MODEL" || { echo "ERROR: missing $sensor"; exit 1; }; done
grep -q '<update_rate>250</update_rate>' "$MODEL" || { echo "ERROR: IMU rate is not 250 Hz"; exit 1; }
CAGE_COUNT=$(grep -c '<visual name="cage_' "$MODEL")
[[ "$CAGE_COUNT" -ge 100 ]] || { echo "ERROR: cage geometry appears incomplete ($CAGE_COUNT visual segments)"; exit 1; }
PROP_COUNT=$(grep -c '<visual name="prop_blade_' "$MODEL")
[[ "$PROP_COUNT" -eq 8 ]] || { echo "ERROR: expected 8 propeller blade visuals, found $PROP_COUNT"; exit 1; }

echo "ELIOS Protected Drone V3.1 verification: OK"
echo "  SDF/XML: OK"
echo "  PX4 motor actuators 0-3: OK"
echo "  IMU 250 Hz / barometer / magnetometer / navsat: OK"
echo "  Protective cage geometry: $CAGE_COUNT visual segments"
echo "  Propeller blade visuals: $PROP_COUNT"
