#!/usr/bin/env bash
# Сборка APK одной командой.
# Требования: JDK 11+, Android SDK build-tools 34, platform 33.
set -euo pipefail

cd "$(dirname "$0")/../app"

SDK="${SDK:-${ANDROID_HOME:-$HOME/android-sdk}/build-tools/34.0.0}"
AJ="${AJ:-${ANDROID_HOME:-$HOME/android-sdk}/platforms/android-33/android.jar}"

if [ ! -x "$SDK/aapt2" ]; then echo "Не найден aapt2 в $SDK"; exit 1; fi
if [ ! -f "$AJ" ]; then echo "Не найден android.jar: $AJ"; exit 1; fi

KEYSTORE="${KEYSTORE:-$HOME/.doodlejump-debug.keystore}"
if [ ! -f "$KEYSTORE" ]; then
  echo "== создаю debug-ключ =="
  keytool -genkeypair -v -keystore "$KEYSTORE" -storepass android -keypass android \
    -alias androiddebugkey -keyalg RSA -keysize 2048 -validity 10000 \
    -dname "CN=DoodleJump, O=OpenSource, C=RU" >/dev/null 2>&1
fi

rm -rf obj dex && mkdir -p obj/classes dex

echo "== aapt2 compile/link =="
"$SDK/aapt2" compile --dir res -o obj/res.zip
"$SDK/aapt2" link -o obj/base.apk -I "$AJ" --manifest AndroidManifest.xml \
  obj/res.zip --java gen --auto-add-overlay --min-sdk-version 21 --target-sdk-version 33

echo "== javac =="
javac -encoding UTF-8 -source 8 -target 8 -bootclasspath "$AJ" -classpath "$AJ" \
  -d obj/classes gen/com/arena/dudlejump/R.java src/com/arena/dudlejump/GameActivity.java

echo "== d8 =="
"$SDK/d8" --min-api 21 --lib "$AJ" --output dex $(find obj/classes -name '*.class')

echo "== package/sign =="
cp obj/base.apk out.apk
(cd dex && zip -q -j ../out.apk classes.dex)
"$SDK/zipalign" -f 4 out.apk aligned.apk
mkdir -p ../dist
"$SDK/apksigner" sign --ks "$KEYSTORE" --ks-pass pass:android --key-pass pass:android \
  --ks-key-alias androiddebugkey --out ../dist/DudleJump_Mellstroy.apk aligned.apk
"$SDK/apksigner" verify ../dist/DudleJump_Mellstroy.apk

echo "ГОТОВО: dist/DudleJump_Mellstroy.apk"
