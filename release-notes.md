Personal build of the PermawebOS node APK (AndEE), upstream `permaweb/os` @ `2d1715c5`.

**Added in this build — Node wallet**
- AR balance of the node identity, read from `https://arweave.net`.
- **Send AR** to any wallet: recipient + amount, confirmation dialog shows recipient and network fee
  before signing. Signed with the app-private HyperBEAM key, posted to `POST /tx`.
- **Bundler beneficiary** switch: stages `{"bundler-beneficiary": "<address>"}` as a next-boot
  overlay so bundling income settles to your wallet, not the node address. Applies on the next boot
  (tap APPLY & CLOSE on the node screen).
- The Arweave signing format is proven against a **mined mainnet transfer**: the unit test rebuilds
  its SHA-384 deep hash byte-for-byte and verifies the recorded signature (`ArweaveTxTest`).

**Still included**
- Broken tunnel no longer dead-ends the node screen: LAN fallback plus a diagnosis label
  (`TUNNEL ID`, `TUNNEL CONFIG`, `TUNNEL URL`, `TUNNEL DNS`, `TUNNEL DOWN`, `OTHER NODE`).
- Rose theme (Tailwind pink): `#150710` page, `#FCE7F3` type, `#EC4899` accent, `#DB2777` glow.
- `versionName = custom`, `versionCode = 3` → screen reads `VERSION custom`.

**Install**
- Uninstall the official app first (same package id `org.permaweb.andee`, different signing key);
  that wipes the node's app-private state, so re-apply a setup code (extension QR or `next.json`).
- Upgrading over an earlier build from this repo keeps data (same certificate, higher versionCode).
- Play Protect may warn about an unknown app; allow it.

**Not a full rebuild.** The Erlang/native runtime, `lib/*.so` payload and llama.cpp/LiteRT notices are
re-staged unmodified from the official `PermawebOS-Node-0.11-81cba3e7.apk`
(sha256 `4eafb17e2fcca3c96ae33db69433057c432f4ba0baaad9a402d684221dee196c`); only the app layer is
rebuilt with Gradle. Upstream's release came from `c07241c2`, absent from the public tree, so this is
not byte-identical to official 0.11.

68 unit tests pass. Upstream's alpha terms apply: unaudited, experimental, no warranty.
