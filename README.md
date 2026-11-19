# permawebos-custom

Personal build of the **PermawebOS node APK** (AndEE — Android Execution Environment for
[PermawebOS](https://github.com/permaweb/os)) with four changes on top of upstream `main`
(`2d1715c5`, 2026-11-01), plus a patched Chrome extension (`0.1.4`) that can
point inference at your own OpenAI-compatible or Anthropic-compatible base URL:

1. **Custom AI provider.** The extension can save a router base URL, API key, model, and wire
   format. OpenAI-compatible routers (CommandCode, atmorouter-style gateways, OpenRouter-likes)
   are stored as provider id `custom` and called at `{base}/chat/completions` with
   `Authorization: Bearer`. Anthropic-compatible endpoints are stored as provider id `anthropic`
   (that is how `inference@1.0` selects the Messages API) and called at `{base}/v1/messages`
   with `x-api-key`. The key is encrypted to the node and kept under `priv`; it is not put in
   the base URL, in `~meta@1.0`, or in an error string.
2. **Node discovery no longer dead-ends when the tunnel is broken.** The screen used to sit on
   `TUNNEL UNAVAILABLE` / “Finding your node…” forever while a perfectly healthy node was listening
   on `127.0.0.1:8734`. It now falls back to the LAN origin (`http://<phone-ip>:8734`) so the QR code
   and “copy URL” keep working, and the status strip names the stage that failed.
3. **Rose theme** (Tailwind pink, matched to megumii.xyz) instead of the navy/cyan ornament.
4. **`versionName = custom`**, `versionCode = 4` — the screen reads `VERSION custom`.
5. **Node wallet** — AR balance of the node identity, a signed transfer to any wallet, and a
   bundler-beneficiary switch staged for the next boot.

Download the APK and the patched extension zip from [Releases](../../releases). Nothing here is upstream-supported.

## Custom AI provider

Upstream’s extension only lists OpenAI, Anthropic, OpenRouter, and APUS, and it pins each of
those to the vendor host. The node’s `inference@1.0` device already routes whatever `base-url`
is stored on the provider; this build is the missing UI.

In the extension, open the node’s **AI provider** form (setup, or “Add or change an API provider”
after the node is connected) and choose **Custom router**:

| field | what to enter |
| --- | --- |
| API format | **OpenAI-compatible** for `/chat/completions` + Bearer, or **Anthropic-compatible** for `/v1/messages` + `x-api-key` |
| Base URL | The prefix the node joins with that path. `https://router.example/v1` becomes `https://router.example/v1/chat/completions`. Do not put the key in the URL. |
| API key | Sent only as the auth header and stored under `inference-providers/<id>/priv/api-key`. |
| Model ID | Required for a custom router. The first ID is `default-model`. |

Anthropic-compatible uses provider id `anthropic`, so it replaces the built-in Anthropic slot’s
base URL. OpenAI-compatible uses a separate id, `custom`, and leaves OpenAI and OpenRouter alone.
The node review screen labels that id **Custom router**. Saving from the connected-node form
encrypts the key to the node administrator key and upserts it through `~ouroboros@1.0/provider-admin`.
The setup QR / `next.json` path writes the same private map into the next boot config. Neither path
publishes the key to Arweave.

`extension/custom-provider.js` is the request builder the patched bundles call. `node --test
extension/custom-provider.test.mjs` points it at a mock OpenAI-compatible server and checks the
path, Bearer header, model, and that a provider error cannot echo the key.

## Node wallet

The wallet button next to the gear opens `NodeWalletActivity`:

- **Balance** — `GET /wallet/<node address>/balance` from `https://arweave.net`.
- **Send AR** — recipient + amount, then a confirmation dialog that shows recipient and network fee
  *before* anything is signed. The transfer is signed with the app-private HyperBEAM key
  (`noBackupFilesDir/node-identity/hyperbeam-key.json`) and posted to `POST /tx`.
- **Bundler beneficiary** — stages `{"bundler-beneficiary": "<address>"}` as a next-boot overlay via
  `AndeeBootConfigStore`, so bundling income settles to your wallet instead of the node address.
  Takes effect on the next boot: tap **APPLY & CLOSE** on the node screen.

Signing is the risky part, so it is pinned to the network format and tested against a **mined**
transaction: `ArweaveTx` builds the v2 signing data (SHA-384 deep hash over
`format, owner, target, quantity, reward, last_tx, tags, data_size, data_root`, with the numeric
fields signed as their decimal strings) and signs it with RSASSA-PSS/SHA-256 and a 32-byte salt.
`ArweaveTxTest` replays a real mainnet transfer — the deep hash matches byte-for-byte and the
recorded signature verifies against the recorded owner, so the wire format is proven, not assumed.

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
- Upgrading **this** build keeps data: same certificate, only `versionCode` moves up.

## Rebuilding

The APK is not a full Erlang rebuild. Upstream cannot rebuild its Android runtime cheaply (NDK 29 +
cross-compiled OTP 28.5 + Rust + WAMR), so the runtime payload is **re-staged from the official
release APK** and only the app layer is rebuilt with Gradle:

```bash
git clone https://github.com/permaweb/os /tmp/permaweb-os
ANDROID_SDK_ROOT=/opt/android-sdk JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64 \
  ./scripts/build.sh /tmp/permaweb-os PermawebOS-Node-0.11-81cba3e7.apk
```

`build.sh` applies `patches/*.patch`, stages the official runtime, runs
`:app:testDebugUnitTest`, then `make -C arch/android apk` (`assembleDebug` +
`verify-generic-andee-artifact.py`).

`stage-official-runtime.py` accepts the official APK digest
(`4eafb17e2fcca3c96ae33db69433057c432f4ba0baaad9a402d684221dee196c`) or any APK
that still carries that runtime (`assets/andee-runtime.zip`
`c1bbaad6c8691c3f808ed80921507361da84314af6660a6845ed7605970394c8`, which is what
`v0.11-custom.2` contains). It then copies
`assets/andee-runtime.zip`, `lib/{arm64-v8a,x86_64}/*.so` and the llama.cpp notice into the paths
the repo's own `verifyGeneratedRuntime` contract demands.

68 unit tests run, 6 of them proving the Arweave transfer format against a mined transaction.
Upstream’s “never advertise LAN” tests are intentionally replaced by the LAN-fallback contract.
The setup review labels provider id `custom` as **Custom router**.

The extension is patched from an unpacked upstream build (v0.1.3), not rebuilt from
source — that source is not in `permaweb/os`:

```bash
unzip PermawebOS-extension-0.1.3.zip -d /tmp/permawebos-ext
python3 scripts/patch-extension.py /tmp/permawebos-ext/chrome
( cd /tmp/permawebos-ext && zip -r -X PermawebOS-extension-custom-0.1.4.zip chrome )
node --test extension/custom-provider.test.mjs
```

## Provenance and licence

- App source: [permaweb/os](https://github.com/permaweb/os) `2d1715c5b4b8512368498149a82b8183be68f3f5`
  (public tree; the upstream release was built from `c07241c2`, which is not in the public repo, so
  this build is **not** byte-identical to the official 0.11 APK).
- Runtime payload, native libraries and llama.cpp/LiteRT notices: taken unmodified from the official
  release `PermawebOS-Node-0.11-81cba3e7.apk`.
- Upstream declares no licence file in the public tree. These patches are published for personal,
  experimental use only, with no warranty — same alpha terms as upstream: unaudited, not for
  production or for value you cannot afford to lose.