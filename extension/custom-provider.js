/**
 * Custom inference provider for PermawebOS.
 *
 * The node's inference@1.0 device (lib_ouroboros_provider) picks the wire
 * format from the provider id, then joins the configured base URL with a
 * fixed path:
 *
 *   openai-compatible  id "custom"     {base}/chat/completions   Authorization: Bearer
 *   anthropic-compatible id "anthropic" {base}/v1/messages        x-api-key
 *
 * The API key is returned only to the caller that encrypts it into the node's
 * private config (`inference-providers/<id>/priv/api-key`). It is never placed
 * in the base URL, a public provider record, or an error string.
 */

const OPENAI_PATH = "/chat/completions";
const ANTHROPIC_PATH = "/v1/messages";
const ANTHROPIC_VERSION = "2023-06-01";
const MODEL_PATTERN = /^[A-Za-z0-9._:/-]{1,200}$/;

export function prepareCustomProvider({ baseUrl, apiKey, model, format } = {}) {
  const wireFormat = format === "anthropic" ? "anthropic" : format === "openai" ? "openai" : "";
  if (!wireFormat) {
    throw new Error("Choose OpenAI-compatible or Anthropic-compatible format.");
  }
  const key = String(apiKey ?? "");
  if (!/^[\x21-\x7e]{1,4096}$/.test(key)) {
    throw new Error("Enter an API key without whitespace.");
  }
  const modelId = String(model ?? "").trim();
  if (!MODEL_PATTERN.test(modelId)) {
    throw new Error("Enter a model ID without spaces.");
  }
  const normalized = normalizeBaseUrl(String(baseUrl ?? ""), wireFormat, key);
  const anthropic = wireFormat === "anthropic";
  return {
    id: anthropic ? "anthropic" : "custom",
    name: anthropic ? "Custom Anthropic" : "Custom router",
    format: wireFormat,
    baseUrl: normalized,
    model: modelId,
    apiKey: key,
  };
}

/** Provider fields safe to store outside the private key envelope. */
export function publicProviderRecord(prepared) {
  return {
    id: prepared.id,
    name: prepared.name,
    format: prepared.format,
    enabled: true,
    "base-url": prepared.baseUrl,
    "default-model": prepared.model,
    models: [{ id: prepared.model }],
  };
}

/**
 * Fragment merged into the node's next-boot config. The key lives only under
 * `priv`, which HyperBEAM keeps out of ~meta@1.0 and the public measurement.
 */
export function bootConfigFragment(prepared) {
  return {
    "inference-provider": prepared.id,
    "inference-provider-priority": [prepared.id],
    "inference-providers": {
      [prepared.id]: {
        "base-url": prepared.baseUrl,
        "default-model": prepared.model,
        models: [{ id: prepared.model }],
        priv: { "api-key": prepared.apiKey },
      },
    },
  };
}

/** Same request the inference device builds: path, auth header, and JSON body. */
export function buildInferenceRequest(prepared, payload = {}) {
  const messages = Array.isArray(payload.messages) ? payload.messages : null;
  if (!messages || messages.length === 0) {
    throw new Error("An inference message is required.");
  }
  const url = joinProviderUrl(prepared.baseUrl, prepared.format === "anthropic" ? ANTHROPIC_PATH : OPENAI_PATH);
  const headers = { "content-type": "application/json" };
  let body;
  if (prepared.format === "anthropic") {
    headers["x-api-key"] = prepared.apiKey;
    headers["anthropic-version"] = ANTHROPIC_VERSION;
    body = anthropicBody(prepared.model, messages, payload);
  } else {
    headers.authorization = `Bearer ${prepared.apiKey}`;
    body = {
      model: payload.model || prepared.model,
      messages,
    };
    if (payload.max_tokens != null) body.max_tokens = payload.max_tokens;
    if (payload.temperature != null) body.temperature = payload.temperature;
  }
  return { url, method: "POST", headers, body: JSON.stringify(body) };
}

export async function completeChat(prepared, payload, fetchImpl = globalThis.fetch) {
  const request = buildInferenceRequest(prepared, payload);
  let response;
  try {
    response = await fetchImpl(request.url, {
      method: request.method,
      headers: request.headers,
      body: request.body,
    });
  } catch (error) {
    throw new Error(redactSecrets(error && error.message ? error.message : "The provider did not respond.", [prepared.apiKey]));
  }
  const text = await response.text();
  if (!response.ok) {
    const detail = redactSecrets(text, [prepared.apiKey]).slice(0, 300);
    throw new Error(`Provider request failed (${response.status}). ${detail}`.trim());
  }
  try {
    return JSON.parse(text);
  } catch {
    throw new Error("The provider returned a response that was not JSON.");
  }
}

export function redactSecrets(text, secrets) {
  let out = String(text ?? "");
  for (const secret of secrets) {
    if (typeof secret === "string" && secret.length >= 4) {
      out = out.split(secret).join("[redacted]");
    }
  }
  return out;
}

function normalizeBaseUrl(value, format, apiKey) {
  const trimmed = value.trim();
  if (!trimmed || /[\s\u0000-\u001f\u007f]/.test(trimmed) || trimmed.length > 2048) {
    throw new Error("Enter an http(s) base URL without spaces.");
  }
  if (apiKey && trimmed.includes(apiKey)) {
    throw new Error("Put the API key in the key field, not the base URL.");
  }
  let url;
  try {
    url = new URL(trimmed);
  } catch {
    throw new Error("Enter an http(s) base URL without spaces.");
  }
  if (url.protocol !== "http:" && url.protocol !== "https:") {
    throw new Error("Enter an http(s) base URL without spaces.");
  }
  if (url.username || url.password || url.search || url.hash) {
    throw new Error("The base URL cannot include a username, password, query, or fragment.");
  }
  let path = url.pathname.replace(/\/+$/, "");
  const suffix = format === "anthropic" ? ANTHROPIC_PATH : OPENAI_PATH;
  if (path.endsWith(suffix)) path = path.slice(0, -suffix.length).replace(/\/+$/, "");
  if (path === "/") path = "";
  url.pathname = path || "/";
  return url.toString().replace(/\/+$/, "");
}

function joinProviderUrl(baseUrl, route) {
  const url = new URL(baseUrl);
  let path = url.pathname.replace(/\/+$/, "");
  if (path === "/") path = "";
  url.pathname = `${path}${route}`;
  return url.toString();
}

function anthropicBody(model, messages, payload) {
  const system = [];
  const chat = [];
  for (const message of messages) {
    if (message && message.role === "system") system.push(String(message.content ?? ""));
    else chat.push(message);
  }
  const body = {
    model: payload.model || model,
    max_tokens: payload.max_tokens ?? 1024,
    messages: chat,
  };
  if (system.length) body.system = system.join("\n");
  if (payload.temperature != null) body.temperature = payload.temperature;
  return body;
}
