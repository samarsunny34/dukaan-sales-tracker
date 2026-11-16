# Build the Android APK

Flet builds a real Android app from this Python code. You need Flutter
and the Android SDK on the computer that builds it — the phone itself
only needs the finished `.apk` file.

## 1. Install the tools (once, on Windows / Mac / Linux)

1. Install **Flutter SDK** — https://docs.flutter.dev/get-started/install
2. Install **Android Studio**, and in SDK Manager install the Android SDK
   + Command-line Tools. Set `ANDROID_HOME` to the SDK folder.
3. Install Python 3.10+ and this project's requirements:

```bash
pip install -r requirements.txt
```

## 2. Test on desktop first

```bash
python main.py
```

Add a product, add a sale, check the dashboard and export the CSV.
Fix anything here — it is much faster than rebuilding an APK.

## 3. Build the APK

```bash
flet build apk
```

The APK is created at:

```
build/apk/app-release.apk
```

For a debug build while you are still testing:

```bash
flet build apk --debug
```

## 4. Install on your phone

1. Copy `app-release.apk` to your Android phone (USB, WhatsApp, Google Drive).
2. On the phone, tap the file and allow **Install from unknown sources**
   when Android asks.
3. Open **Dukaan Sales Tracker**. Your data is stored on the phone in
   `dukaan.db` — it works offline, no internet needed.

## Troubleshooting

- `flutter: command not found` — Flutter is not on your PATH. Close and
  reopen the terminal after installing it, or add its `bin` folder to PATH.
- `ANDROID_HOME is not set` — set it to the Android SDK folder, e.g.
  `C:\Users\<you>\AppData\Local\Android\Sdk` on Windows.
- Build is slow the first time — Flutter downloads Android tooling once;
  later builds are much faster.
- The APK is large (~20 MB) — normal for a Flet / Flutter app.
