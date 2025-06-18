# Magnetometer GUI System — Initial Release

## Overview
This document outlines the features and behavior of the initial release of the **Magnetometer GUI System** running on a Raspberry Pi 5 with a 10-inch HDMI capacitive touchscreen. The system uses an LIS2MDL 3-axis magnetometer to track magnetic field vector changes and detect motion events.

---

## Key Features

### ✅ Real-Time Magnetic Field Visualization
- **Live plotting** of magnetic field components (X, Y, Z) on a scrolling line graph
- **Live magnitude tracking**: Displays |B| (the overall magnetic field strength)
- Color-coded graph:
  - Red = X
  - Green = Y
  - Blue = Z
  - Yellow = |B|
- Optimized for readability and performance on a 1280x720 touchscreen

### ✅ Adaptive Smoothing
- Each axis and magnitude value is filtered using a configurable **low-pass filter**
- Smooths rapid jitter for better visual interpretation

### ✅ Motion Detection Engine
- Two detection modes:
  1. **Vector Delta Mode** (default): Detects large directional changes in X, Y, or Z
  2. **Magnitude Only Mode**: Detects sudden changes in overall |B| strength
- User can switch modes via a GUI checkbox
- Sensitivity tuned for:
  - Vector spike threshold: **25.0 µT**
  - Magnitude spike threshold: **10.0 µT**

### ✅ Spike Event Logging and Feedback
- Tracks **spike count** for the current session
- Shows a large "⚡ Motion Detected!" overlay for each spike
- Displays current |B| value in µT alongside the live readings

### ✅ GPIO 16 Output Control (Relay/Buzzer)
- GPIO **BCM 16** (physical pin 36) is used as a **motion detection output**
- Behavior:
  - LOW at startup (safe state)
  - Set HIGH (3.3V) for 5 seconds on spike detection
  - Returns to LOW after the hold duration
- GPIO logic is managed using the **gpiozero** library (works in virtual environments)

---

## System Safety
- At startup, GPIO 16 is explicitly set LOW to prevent false relay activation
- All spike detection logic is filtered and validated to reduce false positives

---

## Hardware Requirements
- Raspberry Pi 5
- LIS2MDL Magnetometer via I²C
- 10-inch HDMI capacitive touch display
- Optional relay, LED, or buzzer connected to GPIO 16 (3.3V logic)

---

## Software Stack
- Python 3.11 with virtual environment
- Libraries:
  - PyQt5 (GUI framework)
  - PyQtGraph (live plotting)
  - gpiozero (GPIO handling)
  - adafruit-blinka + adafruit-circuitpython-lis2mdl (sensor)

---

## File Name
`mag_vector_gui.py`

---

## Author & Maintainer
Developed and maintained by [User: mr collins]

---

## Next Feature Candidates
- Reset spike count button
- Fullscreen auto-launch
- Web-based remote monitoring (/status endpoint)
- CSV or JSON export of spike events
- Optional GPIO 16 state indicator in GUI

