# Kivy App Testing Checklist (Windows + Android)

Use this checklist each time you test your app.

## 1) Pre-test system checks (Windows)

- [ ] Rebooted after any driver/graphics registry change.
- [ ] Laptop is on AC power (not battery saver mode).
- [ ] Windows Graphics settings: `python.exe` is set to **High performance**.
- [ ] NVIDIA Control Panel Program Settings (if available): `python.exe` uses **High-performance NVIDIA processor**.
- [ ] HDR is OFF (temporarily) during troubleshooting.

## 2) Python environment checks

From workspace root:

```powershell
.\.venv\Scripts\activate
python --version
pip show kivy
```

- [ ] Virtual environment is active.
- [ ] Python version is expected.
- [ ] Kivy version is known (log it for test notes).

## 3) Desktop smoke test (Windows)

Run app:

```powershell
python -u mobile_app\demo2.py
```

Check startup log lines:

- [ ] `Window` provider is `sdl2`.
- [ ] `GL` backend is shown (`angle_sdl2` or `sdl2`).
- [ ] `OpenGL renderer` line is printed.
- [ ] No shader compile errors.

Visual behavior:

- [ ] Window content is visible (not all black).
- [ ] Button text is visible.
- [ ] Button click prints expected output.
- [ ] Resize/minimize/restore still keeps content visible.

If still black:

- [ ] Test once with `angle_sdl2`.
- [ ] Test once with `sdl2`.
- [ ] Save first 40-80 startup log lines for comparison.

## 4) Android-focused workflow (recommended if Windows rendering is unstable)

- [ ] Keep coding in Windows VS Code.
- [ ] Build APK in WSL2 Ubuntu (Buildozer).
- [ ] Install APK on physical Android phone.
- [ ] Validate UI and touch behavior on device.

## 5) Device test checklist (Android phone)

- [ ] App starts without crash.
- [ ] Main screen renders correctly.
- [ ] Button/touch input works.
- [ ] Orientation changes do not break layout.
- [ ] Performance is acceptable (no major stutter).
- [ ] App can background/foreground without rendering issues.

## 6) Test log template (copy per run)

- Date/time:
- OS build:
- GPU driver versions (AMD/NVIDIA):
- Python:
- Kivy:
- Backend (`angle_sdl2`/`sdl2`/other):
- Result (visible/black/crash):
- Notes:

## 7) Optional rollback/cleanup checks

- [ ] Removed temporary debug env vars (for clean runs).
- [ ] If MPO tweak was applied, note current state.
- [ ] If needed, document exact command used to revert tweaks.
