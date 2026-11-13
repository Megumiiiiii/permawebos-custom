# permawebos-custom

Personal build of the **PermawebOS node APK** (AndEE — Android Execution Environment for
[PermawebOS](https://github.com/permaweb/os)) with three changes on top of upstream `main`
(`2d1715c5`, 2026-11-01):

1. **Node discovery no longer dead-ends when the tunnel is broken.** The screen used to sit on
   `TUNNEL UNAVAILABLE` / “Finding your node…” forever while a perfectly healthy node was listening
   on `127.0.0.1:8734`. It now falls back to the LAN origin (`http://<phone-ip>:8734`) so the QR code
   and “copy URL” keep working, and the status strip names the stage that failed.
2. **Rose theme** (Tailwind pink, matched to megumii.xyz) instead of the navy/cyan ornament.
3. **`versionName = custom`**, `versionCode = 2` — the screen reads `VERSION custom`.

Download the APK from [Releases](../../releases). Nothing here is upstream-supported.

## Status labels

| label | meaning |
| --- | --- |
| `CONNECT YOUR NODE` | tunnel verified: the public URL answers and it is this node |
| `LOCAL NETWORK NODE` | no tunnel configured, reachable on the LAN |
| `LAN NODE · TUNNEL ID` | node reports no DNS-safe committer, so the tunnel host cannot be derived |
| `LAN NODE · TUNNEL CONFIG` | a tunnel hook exists but carries no peer |
| `LAN NODE · TUNNEL URL` | reported `location-url` / peer is not a usable origin |
| `LAN NODE · TUNNEL DNS` | tunnel hostname does not resolve |
| `LAN NODE · TUNNEL DOWN` | hostname resolves, nothing answers (worker not registered) |
| `LAN NODE · OTHER NODE` | the tunnel answers, but for a different node address |
| `NETWORK UNAVAILABLE` / `TUNNEL DNS`… | no LAN address at all, so only the diagnosis is shown |

Everything prefixed `LAN NODE ·` is a **degraded but usable** state: the QR carries the LAN URL, so
the PermawebOS browser extension can connect over the same Wi-Fi (paste the URL or scan the code).

## Palette

| token | value | use |
| --- | --- | --- |
| `background` | `#150710` | page |
| `backgroundDeep` | `#0C0308` | wells, secondary buttons |
| `ink` / `inkStrong` / `inkMuted` | `#FCE7F3` | type (pink-100) |
| `accent` | `#EC4899` | primary button, rails (pink-500) |
| `accentBright` | `#F472B6` | status label, logo tint (pink-400) |
| `glow` | `#DB2777` | ASCII tunnel shadow (pink-600) |
| `qrInk` | `#1A0712` | dark QR modules on the pink-100 plate |

The logo bitmap is recoloured with a `PorterDuffColorFilter`, so no new art assets are shipped.

## Installing

- The package id is `org.permaweb.andee`, same as the official APK, but signed with a **local debug
  certificate**. Android refuses the upgrade, so **uninstall the official app first** — that deletes
  the node's app-private state (config, node key). Re-apply a setup code afterwards (extension →
  node setup → QR, or import `next.json`).
- Build type is `debug`, so Play Protect may warn about an unknown app; allow the install.
- After installing, `CONFIGURE` → scan the setup QR again, then reopen the app.

## Rebuilding

The APK is not a full Erlang rebuild. Upstream cannot rebuild its Android runtime cheaply (NDK 29 +
cross-compiled OTP 28.5 + Rust + WAMR), so the runtime payload is **re-staged from the official
release APK** and only the app layer is rebuilt with Gradle:

```bash
git clone https://github.com/permaweb/os && cd os
git apply /path/to/permawebos-custom/patches/*.patch

# Android SDK (platform 36, build-tools 36) + JDK 21, then:
python3 scripts/stage-official-runtime.py . PermawebOS-Node-0.11-81cba3e7.apk
ANDROID_SDK_ROOT=/opt/android-sdk JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64 \
  make -C arch/android apk
```

`stage-official-runtime.py` verifies the official APK digest
(`4eafb17e2fcca3c96ae33db69433057c432f4ba0baaad9a402d684221dee196c`), then copies
`assets/andee-runtime.zip`, `lib/{arm64-v8a,x86_64}/*.so` and the llama.cpp notice into the paths
the repo's own `verifyGeneratedRuntime` contract demands. `make apk` runs `assembleDebug` plus
`verify-generic-andee-artifact.py`.

Unit tests: `cd arch/android/android && ./gradlew :app:testDebugUnitTest` (62 tests, including the
new tunnel-fallback contract; upstream’s “never advertise LAN” tests are intentionally replaced).

## Provenance and licence

- App source: [permaweb/os](https://github.com/permaweb/os) `2d1715c5b4b8512368498149a82b8183be68f3f5`
  (public tree; the upstream release was built from `c07241c2`, which is not in the public repo, so
  this build is **not** byte-identical to the official 0.11 APK).
- Runtime payload, native libraries and llama.cpp/LiteRT notices: taken unmodified from the official
  release `PermawebOS-Node-0.11-81cba3e7.apk`.
- Upstream declares no licence file in the public tree. These patches are published for personal,
  experimental use only, with no warranty — same alpha terms as upstream: unaudited, not for
  production or for value you cannot afford to lose.
