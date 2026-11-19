Personal build of the PermawebOS node APK (AndEE) and Chrome extension, upstream `permaweb/os` @ `2d1715c5`. Extension base is PermawebOS v0.1.3, patched to v0.1.4.

The first extension zip on this tag had a service-worker syntax error (`Unexpected token '}'`) and would not register. The zip attached now loads: Chromium registers `core.js`, and the popup and side panel open.

**Added in this build — Custom AI provider**
- Extension: **Custom router** on node setup, on the connected-node provider form, and on the local provider form. Enter a base URL, API key, model, and **OpenAI-compatible** or **Anthropic-compatible**.
- OpenAI-compatible (CommandCode, atmorouter-style routers, OpenRouter-likes) is stored as provider id `custom`. The node calls `{base}/chat/completions` with `Authorization: Bearer`.
- Anthropic-compatible is stored as provider id `anthropic`, which is how `inference@1.0` selects the Messages API. The node calls `{base}/v1/messages` with `x-api-key` and `anthropic-version: 2023-06-01`. That replaces the built-in Anthropic base URL.
- The API key is encrypted to the node and stored only under `inference-providers/<id>/priv/api-key`. It is not placed in the base URL, published to Arweave, or copied into error text.
- `node --test extension/custom-provider.test.mjs` sends a chat completion to a mock OpenAI-compatible server and checks the path, Bearer header, model, and redaction.

**Still included**
- Node wallet: AR balance, signed transfer with a confirmation that shows recipient and fee, bundler-beneficiary overlay. Signing format proven against a mined mainnet transfer (`ArweaveTxTest`).
- Broken tunnel falls back to the LAN origin, with a diagnosis label (`TUNNEL ID`, `TUNNEL CONFIG`, `TUNNEL URL`, `TUNNEL DNS`, `TUNNEL DOWN`, `OTHER NODE`).
- Rose theme (Tailwind pink): `#150710` page, `#FCE7F3` type, `#EC4899` accent, `#DB2777` glow.
- `versionName = custom`, `versionCode = 4` → screen reads `VERSION custom`.

**Install**
- Load the extension unpacked (chrome://extensions → Developer mode → Load unpacked → the `chrome` folder inside the zip).
- Uninstall the official app first (same package id `org.permaweb.andee`, different signing key); that wipes the node's app-private state, so re-apply a setup code (extension QR or `next.json`).
- Upgrading over an earlier build from this repo keeps data (same certificate, higher versionCode).
- Play Protect may warn about an unknown app; allow it.

**Not a full rebuild.** The Erlang/native runtime, `lib/*.so` payload and llama.cpp/LiteRT notices are re-staged unmodified from the official runtime carried by `PermawebOS-Node-0.11-81cba3e7.apk` (`assets/andee-runtime.zip` sha256 `c1bbaad6c8691c3f808ed80921507361da84314af6660a6845ed7605970394c8`). Only the app layer is rebuilt with Gradle. Upstream's release came from `c07241c2`, absent from the public tree, so this is not byte-identical to official 0.11.

The extension source is not in the public `permaweb/os` tree, so v0.1.4 is a patch of the v0.1.3 build. On-device inference against a phone was not run here; routing was checked against the decompiled `inference@1.0` device and a local mock server.

68 unit tests pass. Upstream's alpha terms apply: unaudited, experimental, no warranty.
