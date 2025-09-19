# Android Offline SMS Gateway (Minimal)

Purpose: A lightweight Android app (Kotlin) that:
- Receives incoming SMS (works offline), stores locally.
- When Wi‑Fi/data is available, forwards to your backend `/receive-sms-smssync`-compatible endpoint.
- Polls backend `/gateway/outbound` to fetch alerts and sends via SIM SMS.
- Marks sent via `/gateway/mark-sent`.

This is a minimal starter that you can open in Android Studio and build an APK.

## Build
- Install Android Studio (latest stable)
- Open folder `android-app/`
- Let Gradle sync and build
- Plug in your phone with USB debugging enabled
- Run 'app' configuration to deploy

## Configure
Inside the app (Settings screen to be added), set:
- Backend Base URL: `http://<HOST_PC_LAN_IP>:8000`
- Optional secret (future)

## Permissions
- RECEIVE_SMS, READ_SMS, SEND_SMS
- RECEIVE_BOOT_COMPLETED (to start worker)
- INTERNET, ACCESS_NETWORK_STATE

## Notes
This app uses WorkManager to periodically sync outbound/inbound when connectivity is available. Incoming SMS are captured by a BroadcastReceiver and buffered in Room DB.
