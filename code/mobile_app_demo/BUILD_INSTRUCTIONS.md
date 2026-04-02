# Building Hello World Kivy App with Buildozer

## Files Created
- `main.py` - Python entry point
- `helloworld.kv` - Kivy UI definition

## Prerequisites

1. **Install Buildozer** (if not already installed):
```bash
pip install buildozer
```

2. **Install Android SDK/NDK dependencies** (one-time setup):
   - On Windows, install Java JDK
   - Create a `buildozer.spec` file in this directory with Android configuration

## Quick Start

### Step 1: Create buildozer.spec
Run this command in the `mobile_app_demo` directory:
```bash
buildozer android debug init
```
This generates a `buildozer.spec` file with default Android settings.

### Step 2: Configure buildozer.spec
Edit `buildozer.spec` and modify these key sections:

**[app] section:**
```ini
[app]
title = Hello World
package.name = helloworld
package.domain = org.example
```

**[buildozer] section (optional but recommended for speed):**
```ini
[buildozer]
log_level = 2
warn_on_root = 1
```

### Step 3: Build APK (Debug)
```bash
buildozer android debug
```

This will:
- Download Android SDK, NDK, and dependencies (first time is slow - ~5-10GB)
- Compile your Python code
- Create APK in `bin/` directory

The APK will be: `bin/helloworld-0.1-debug.apk`

### Step 4: Install on Device/Emulator
```bash
buildozer android debug deploy run
```

Or manually:
```bash
adb install -r bin/helloworld-0.1-debug.apk
adb shell am start -n org.example.helloworld/.HelloWorldApp
```

### Step 5: Build for Release (Optional)
For production:
```bash
buildozer android release
```

This creates an unsigned APK. You'll need to sign it for Google Play Store.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `java` command not found | Install Java JDK, add to PATH |
| Permission denied | Use `sudo buildozer ...` on Linux/Mac |
| Out of disk space | Clean old builds: `buildozer android clean` |
| Build fails midway | Check internet, try again (downloads can timeout) |
| .so files error | Install 32-bit libraries: `sudo apt-get install lib32z1` |

## Testing Locally (without APK)
To test on your PC before building APK:
```bash
python main.py
```

Make sure you have Kivy installed: `pip install kivy`

## File Structure
```
mobile_app_demo/
├── main.py                  # Entry point
├── helloworld.kv           # UI definition
├── buildozer.spec          # Build configuration
├── bin/                    # Output APK (created after build)
└── .buildozer/             # Build cache (created after build)
```

## Next Steps
- Customize the UI in `helloworld.kv`
- Add more Python logic in `main.py`
- Adjust permissions in `buildozer.spec` as needed
- Use `buildozer android debug` for iterations
