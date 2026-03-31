# Buildozer APK Build Guide - KingdomsApp

## Prerequisites on Linux Machine

### 1. Install system dependencies
```bash
sudo apt-get update
sudo apt-get install -y \
    build-essential \
    git \
    default-jdk \
    default-jre \
    autoconf \
    automake \
    libtool \
    pkg-config \
    cmake \
    ninja-build \
    ant \
    python3 \
    python3-dev \
    python3-pip \
    libffi-dev \
    libssl-dev \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    libharfbuzz0b \
    libharfbuzz-dev \
    imagemagick \
    libmagick++-dev
```

### 2. Download and set up Android SDK/NDK

Buildozer can auto-download these, but you may need to manually set them up:

```bash
mkdir -p ~/android-sdk
cd ~/android-sdk

# Download Android SDK Command Tools
wget https://dl.google.com/android/repository/commandlinetools-linux-10406996_latest.zip
unzip commandlinetools-linux-10406996_latest.zip
rm commandlinetools-linux-10406996_latest.zip
```

Then add to your `~/.bashrc` or `~/.zshrc`:
```bash
export ANDROID_SDK_ROOT=~/android-sdk
export PATH=$ANDROID_SDK_ROOT/cmdline-tools/latest/bin:$PATH
export PATH=$ANDROID_SDK_ROOT/platform-tools:$PATH
```

### 3. Install Buildozer and Python-for-Android

```bash
# Recommended: dedicated build virtualenv (Python 3.10 or 3.11)
python3.10 -m venv ~/.venvs/buildozer
source ~/.venvs/buildozer/bin/activate

pip install --upgrade pip wheel "setuptools<82"
pip install "Cython<3" buildozer python-for-android
```

## Building the APK

### Step 1: Navigate to your mobile_app directory
```bash
cd /path/to/KingdomsApp/code/mobile_app
```

### Step 2: Initialize buildozer (if needed)
```bash
buildozer init
```
*Note: Since you already have `buildozer.spec`, you can skip this.*

### Step 3: Build in Debug Mode (recommended first)
```bash
buildozer android debug
```

This will:
- Download Android SDK/NDK
- Compile your Python code
- Bundle all dependencies
- Create an APK file

**Expected build time:** 30-60 minutes on first build (faster on subsequent builds)

### Step 4: Build in Release Mode (after successful debug build)
```bash
buildozer android release
```

For a signed release version:
```bash
buildozer android release > buildozer_output.log 2>&1 &
```

## Troubleshooting Common Issues

### Issue 0: Missing Cython (ModuleNotFoundError: No module named 'Cython')
This happens when python-for-android tries to compile pyjnius but Cython is not installed in your host virtual environment.

Install build-time Python packages in the same virtual environment where you run buildozer:

    source /home/petar/Documents/diplomski/KingdomsApp/code/.venv/bin/activate
    pip install --upgrade pip wheel
    pip install "setuptools<82"
    pip install "Cython<3"

If you already upgraded setuptools too far, force reinstall a compatible version:

    pip install --force-reinstall "setuptools==81.0.0"

Then clean and rebuild:

    cd /home/petar/Documents/diplomski/KingdomsApp/code/mobile_app
    buildozer android clean
    rm -rf .buildozer/android/platform/build-*
    buildozer -v android debug

### Issue 1: ONNXRUNTIME Build Failures
If onnxruntime fails to compile, you have options:
- **Option A:** Remove onnxruntime from requirements and use pre-compiled wheels
- **Option B:** Switch to a lighter alternative if available
- Comment out in buildozer.spec: `requirements = python3,kivy,numpy,pyjnius,opencv`

### Issue 2: OpenCV Not Found
Python-for-android may not have a recipe for opencv4. Common solutions:
- Use `opencv` instead of `opencv-python`
- If opencv fails, try: `requirements = python3,kivy,numpy,pyjnius`

### Issue 3: Java/SDK Errors
Ensure Java is installed:
```bash
java -version
```

Accept Android SDK licenses:
```bash
sdkmanager --licenses
```

### Issue 4: Build Hangs or Times Out
The build can take 30-60 minutes. Monitor progress:
```bash
tail -f .buildozer/android/platform/build-[variant]/logs/python.log
```

Kill and retry if stuck:
```bash
buildozer android debug --no-strip
```

### Issue 5: Buildozer shows only generic failure line
If you only see `Buildozer failed to execute the last command`, extract the first real compiler error from build logs:

```bash
cd /home/petar/Documents/diplomski/KingdomsApp/code/mobile_app
grep -RInE "error:|fatal error|Traceback|Command failed" .buildozer/android/platform/build-arm64-v8a* | head -n 60
```

For this project, start with arm64 only (already set in [mobile_app/buildozer.spec](mobile_app/buildozer.spec#L307)).

If grep output points to many source files (configure, m4, changelog) but no real runtime error line, inspect log files only:

```bash
cd /home/petar/Documents/diplomski/KingdomsApp/code/mobile_app
find .buildozer -type f \( -name "*.log" -o -name "config.log" \) -print0 \
    | xargs -0 grep -nE "error:|fatal error|Traceback|No such file|cannot create executables|Command failed" \
    | head -n 120
```

### Issue 6: Kivy/SDL2_ttf bootstrap failure
If the build fails in an SDL2_ttf or kivy bootstrap path, install host autotools and rebuild from clean state:

```bash
sudo apt-get update
sudo apt-get install -y autoconf automake libtool pkg-config cmake ninja-build

source /home/petar/Documents/diplomski/KingdomsApp/code/.venv/bin/activate
cd /home/petar/Documents/diplomski/KingdomsApp/code/mobile_app
buildozer android clean
rm -rf .buildozer/android/platform/build-*
buildozer -v android debug
```

### Issue 7: libffi/python3 configure errors in config.log
The lines you shared (missing `ac_nonexistent.h`, many probe compile errors, etc.) are mostly normal autoconf checks. The real blocker is usually environment/toolchain contamination.

Run buildozer from a clean shell and clear custom compiler vars before build:

```bash
source ~/.venvs/buildozer/bin/activate
cd /home/petar/Documents/diplomski/KingdomsApp/code/mobile_app

unset CC CXX CPP CFLAGS CXXFLAGS CPPFLAGS LDFLAGS LDSHARED AR RANLIB STRIP PKG_CONFIG_PATH

buildozer android clean
rm -rf .buildozer/android/platform/build-*
buildozer -v android debug 2>&1 | tee buildozer_full.log
```

Then extract the real failing command from the full log:

```bash
grep -nE "\[ERROR\]|Command failed|Traceback|Exception| failed!" buildozer_full.log | tail -n 120
```

If this output only shows line numbers (without the real traceback body), print context around those lines:

```bash
cd /home/petar/Documents/diplomski/KingdomsApp/code/mobile_app
for n in 21408 21555 21961 22990 23641 23645; do
    start=$((n-30)); [ $start -lt 1 ] && start=1
    end=$((n+80))
    echo "===== buildozer_full.log:$start-$end ====="
    sed -n "${start},${end}p" buildozer_full.log
done
```

### Issue 8: hostpython3 fails before app recipes
If hostpython3 fails early, build a baseline APK first and add heavy dependencies later.

Current baseline in [mobile_app/buildozer.spec](mobile_app/buildozer.spec):
- requirements = python3==3.10.11,kivy,numpy,pyjnius,opencv

After this baseline build succeeds, re-add onnxruntime and rebuild.

## Output

After successful build:
- **Debug APK:** `bin/kingdomsapp-0.1-debug.apk`
- **Release APK:** `bin/kingdomsapp-0.1-release-unsigned.apk`

### Installing Debug APK on Device
```bash
adb install -r bin/kingdomsapp-0.1-debug.apk
```

### Signing Release APK
```bash
jarsigner -verbose -sigalg MD5withRSA -digestalg SHA1 \
    -keystore my-release-key.keystore \
    bin/kingdomsapp-0.1-release-unsigned.apk \
    alias_name
```

## Important Notes

1. **First build is slow** - Buildozer downloads and compiles the entire Android SDK/NDK
2. **RAM requirement** - Ensure your Linux machine has at least 8GB RAM available
3. **Disk space** - Need ~20GB free space for SDK/NDK extraction
4. **onnxruntime is complex** - May have compilation issues. Be prepared to remove it if build fails repeatedly
5. **OpenCV support** - python-for-android has limited OpenCV recipes; you may need to use pre-trained models instead

## Next Steps if Build Fails

1. Check buildozer log: `cat .buildozer/android/platform/build-debug_arm64-v8a/build.log`
2. Try building without problematic libraries first (test with just kivy+numpy)
3. Add each library back one at a time to identify which causes issues
4. Consider using pre-built ONNX models + embedding them as binary files instead of compiling onnxruntime from source

## CI/CD Alternative

If local build continues to fail, consider cloud builders:
- **Briefcase** (from BeeWare) - handles complex dependencies better
- **Google Play Console Cloud Build**
- **GitHub Actions** with docker-buildozer
