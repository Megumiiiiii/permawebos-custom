#!/usr/bin/env bash
# Build the custom APK from a permaweb/os checkout.
#
#   ./scripts/build.sh <permaweb-os-checkout> <official-PermawebOS-APK>
#
# Env: ANDROID_SDK_ROOT, JAVA_HOME, ANDROID_BUILD_TOOLS_VERSION (default 36.0.0).
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
checkout="${1:?usage: build.sh <permaweb-os-checkout> <official.apk>}"
apk="${2:?usage: build.sh <permaweb-os-checkout> <official.apk>}"
: "${ANDROID_SDK_ROOT:?set ANDROID_SDK_ROOT to an Android SDK with platform 36 + build-tools 36}"
: "${JAVA_HOME:?set JAVA_HOME to a JDK 17+ (21 works)}"

cd "$checkout"
for patch_file in "$here"/patches/*.patch; do
    echo "applying $(basename "$patch_file")"
    git apply --check "$patch_file"
    git apply "$patch_file"
done

python3 "$here/scripts/stage-official-runtime.py" "$checkout" "$apk"

export ANDROID_HOME="$ANDROID_SDK_ROOT"
export ANDROID_BUILD_TOOLS_VERSION="${ANDROID_BUILD_TOOLS_VERSION:-36.0.0}"
export PATH="$ANDROID_SDK_ROOT/cmdline-tools/latest/bin:$ANDROID_SDK_ROOT/platform-tools:$JAVA_HOME/bin:$PATH"

( cd arch/android/android && ./gradlew --console=plain :app:testDebugUnitTest )
make -C arch/android apk

built="arch/android/android/app/build/outputs/apk/debug/app-debug.apk"
"$ANDROID_SDK_ROOT/build-tools/$ANDROID_BUILD_TOOLS_VERSION/aapt2" dump badging "$built" |
    grep -E "^package:|^native-code:" || true
sha256sum "$built"
