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

# PermawebOS-Node-0.11-81cba3e7.apk as published on Arweave (tag SHA-256).
EXPECTED_APK_SHA256 = "4eafb17e2fcca3c96ae33db69433057c432f4ba0baaad9a402d684221dee196c"

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
    if actual != EXPECTED_APK_SHA256:
        print(
            f"{apk}: unexpected digest {actual}\n"
            f"expected the published PermawebOS-Node-0.11-81cba3e7.apk "
            f"({EXPECTED_APK_SHA256})",
            file=sys.stderr,
        )
        return 1

    app_dir = android / "android" / "app"
    copied_objects = 0
    with zipfile.ZipFile(apk) as archive:
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
