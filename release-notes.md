Personal build of the PermawebOS node APK (AndEE), upstream `permaweb/os` @ `2d1715c5`.

**Changed**
- Broken tunnel no longer dead-ends the node screen: falls back to the LAN origin
  (`http://<phone-ip>:8734`) so the QR/copy URL keep working, and the status strip names the
  failing stage (`TUNNEL ID`, `TUNNEL CONFIG`, `TUNNEL URL`, `TUNNEL DNS`, `TUNNEL DOWN`,
  `OTHER NODE`).
- Rose theme (Tailwind pink, megumii.xyz): `#150710` page, `#FCE7F3` type, `#EC4899` accent,
  `#DB2777` glow, logo recoloured via colour filter; QR keeps a pink-100 plate with dark modules.
- `versionName = custom`, `versionCode = 2` → screen reads `VERSION custom`.

**Install**
- Uninstall the official app first: same package id (`org.permaweb.andee`), different signing key
  (local debug cert) → the upgrade is refused, and uninstalling wipes the node's app-private
  state (config + node key). Re-apply a setup code after installing (extension QR or `next.json`).
- Play Protect may warn about an unknown app; allow it.

**Not a full rebuild.** The Erlang/native runtime, `lib/*.so` payload and llama.cpp/LiteRT notices
are re-staged unmodified from the official `PermawebOS-Node-0.11-81cba3e7.apk`
(sha256 `4eafb17e2fcca3c96ae33db69433057c432f4ba0baaad9a402d684221dee196c`); only the app layer is
rebuilt with Gradle. Upstream's release was built from `c07241c2`, which is absent from the public
tree, so this is not byte-identical to official 0.11.

62 unit tests pass, including the new tunnel-fallback contract. Upstream's alpha terms apply:
unaudited, experimental, no warranty.
