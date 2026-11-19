#!/usr/bin/env python3
"""Re-stage the official PermawebOS runtime into a permaweb/os checkout.

Upstream cannot rebuild its Android runtime cheaply (NDK 29, cross-compiled OTP 28.5,
Rust, WAMR). This script copies the payload out of the official release APK into exactly
the paths the repo's own `verifyGeneratedRuntime` Gradle contract asserts, so that
`make -C arch/android apk` only has to run Gradle.

usage: stage-official-runtime.py <permaweb-os-checkout> <official.apk>
"""

from __future__ import annotations

import hashlib
import sys
import zipfile
from pathlib import Path

# PermawebOS-Node-0.11-81cba3e7.apk as published on Arweave (whole-file SHA-256).
EXPECTED_APK_SHA256 = "4eafb17e2fcca3c96ae33db69433057c432f4ba0baaad9a402d684221dee196c"

# Same runtime payload, copied unmodified into the v0.11-custom.2 APK
# (whole-file SHA-256 600ecb9a4080f70d476acfc6bdad70c9c77daf685cb6a76c33d981d59b980a46).
# A later custom APK is accepted when these entries still match, so the app
# layer can be rebuilt without the original release file.
RUNTIME_ENTRY_SHA256 = {
    "assets/andee-runtime.zip": "c1bbaad6c8691c3f808ed80921507361da84314af6660a6845ed7605970394c8",
    "lib/arm64-v8a/libandee_hyperbeam.so": "4fc7747bb997ed9d2a17feb4362ae36a3a6e508150f3408b09e00e62a204c4ec",
    "lib/x86_64/libandee_hyperbeam.so": "bd850fed662bd3742551586eb49f0915825647dfd9c17f15104ec979402ba6df",
}

LAMA_NOTICE_ENTRY = "assets/llama-cpp-b10502/LICENSE"
RUNTIME_ENTRY = "assets/andee-runtime.zip"
NOTICE_RELATIVE = "build/llama-cpp-runtime/notices/llama-cpp-b10502/LICENSE"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def copy_entry(archive: zipfile.ZipFile, entry: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with archive.open(entry) as source, target.open("wb") as destination:
        while chunk := source.read(1 << 20):
            destination.write(chunk)


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__.strip().splitlines()[-1], file=sys.stderr)
        return 2
    checkout = Path(sys.argv[1]).resolve()
    apk = Path(sys.argv[2]).resolve()

    android = checkout / "arch" / "android"
    if not (android / "android" / "app").is_dir():
        print(f"{checkout}: not a permaweb/os checkout", file=sys.stderr)
        return 1
    if not apk.is_file():
        print(f"{apk}: missing", file=sys.stderr)
        return 1

    actual = sha256(apk)
    app_dir = android / "android" / "app"
    copied_objects = 0
    with zipfile.ZipFile(apk) as archive:
        if actual != EXPECTED_APK_SHA256:
            mismatches = []
            for entry, expected in RUNTIME_ENTRY_SHA256.items():
                try:
                    payload = archive.read(entry)
                except KeyError:
                    mismatches.append(f"{entry}: missing")
                    continue
                found = hashlib.sha256(payload).hexdigest()
                if found != expected:
                    mismatches.append(f"{entry}: {found}")
            if mismatches:
                print(
                    f"{apk}: unexpected digest {actual}\n"
                    f"expected the published PermawebOS-Node-0.11-81cba3e7.apk "
                    f"({EXPECTED_APK_SHA256}) or an APK carrying that runtime:\n"
                    + "\n".join(mismatches),
                    file=sys.stderr,
                )
                return 1
            print(f"{apk}: accepted by runtime payload hash (whole file {actual})")
        names = archive.namelist()
        for required in (RUNTIME_ENTRY, LAMA_NOTICE_ENTRY):
            if required not in names:
                print(f"{apk}: missing {required}", file=sys.stderr)
                return 1

        copy_entry(archive, RUNTIME_ENTRY, app_dir / "src/main/assets/andee-runtime.zip")
        copy_entry(archive, LAMA_NOTICE_ENTRY, android / NOTICE_RELATIVE)

        for name in names:
            if not (name.startswith("lib/") and name.endswith(".so")):
                continue
            abi, base = name.split("/")[1], name.rsplit("/", 1)[1]
            copy_entry(archive, name, app_dir / "src/main/jniLibs" / abi / base)
            copied_objects += 1

    for abi in ("arm64-v8a", "x86_64"):
        probe = app_dir / "src/main/jniLibs" / abi / "libandee_hyperbeam.so"
        if not probe.is_file():
            print(f"{probe}: missing native HyperBEAM runtime for {abi}", file=sys.stderr)
            return 1

    print(f"staged runtime zip + {copied_objects} native objects + llama.cpp notice into {android}")
    print("next: make -C arch/android apk (ANDROID_SDK_ROOT, JAVA_HOME)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
