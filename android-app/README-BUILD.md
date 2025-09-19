# Build & APK Instructions

## Local build (Android Studio)
1. Open `android-app/` in Android Studio.
2. Let Gradle sync and ensure SDK 34 is installed.
3. Build > Make Project.
4. Run on device or Build > Build Bundle(s) / APK(s) > Build APK(s).
5. The debug APK will be in `android-app/app/build/outputs/apk/debug/app-debug.apk`.

## Local build (Gradle CLI)
From `android-app/` folder:
```
./gradlew assembleDebug
```
On Windows PowerShell:
```
./gradlew.bat assembleDebug
```
APK location:
```
android-app/app/build/outputs/apk/debug/app-debug.apk
```

## Install on device
- Enable "Install unknown apps" for your file manager or via `adb`:
```
adb install -r android-app/app/build/outputs/apk/debug/app-debug.apk
```
Enable USB debugging and authorize the PC.

## Configure the app
- Open the app, enter your backend Base URL (e.g., `http://192.168.1.50:8000`) and Save.
- Grant SMS permissions when prompted.

## What it does
- Receives SMS offline and queues to send to backend when online.
- Polls `/gateway/outbound` every ~15 minutes and sends SMS via SIM, then POSTs `/gateway/mark-sent`.

## Notes
- Android limits periodic background work to minimum 15 minutes.
- For quicker testing, we can add a manual "Sync now" button—ask and we'll wire it up.
