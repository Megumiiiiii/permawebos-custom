import assert from "node:assert/strict";
import http from "node:http";
import test from "node:test";

import {
  bootConfigFragment,
  buildInferenceRequest,
  completeChat,
  prepareCustomProvider,
  publicProviderRecord,
  redactSecrets,
} from "./custom-provider.js";

const KEY = "sk-test-custom-provider-key";

test("openai-compatible custom provider keeps the key private and hits /chat/completions", async () => {
  const prepared = prepareCustomProvider({
    baseUrl: "https://router.example/v1/",
    apiKey: KEY,
    model: "command/code",
    format: "openai",
  });
  assert.equal(prepared.id, "custom");
  assert.equal(prepared.baseUrl, "https://router.example/v1");
  const request = buildInferenceRequest(prepared, {
    messages: [{ role: "user", content: "ping" }],
  });
  assert.equal(request.url, "https://router.example/v1/chat/completions");
  assert.equal(request.headers.authorization, `Bearer ${KEY}`);
  assert.equal(request.headers["x-api-key"], undefined);
  const body = JSON.parse(request.body);
  assert.equal(body.model, "command/code");
  assert.deepEqual(body.messages, [{ role: "user", content: "ping" }]);
  assert.equal(JSON.stringify(publicProviderRecord(prepared)).includes(KEY), false);
  const boot = bootConfigFragment(prepared);
  assert.equal(boot["inference-provider"], "custom");
  assert.equal(boot["inference-providers"].custom.priv["api-key"], KEY);
  const published = JSON.parse(JSON.stringify(boot));
  delete published["inference-providers"].custom.priv;
  assert.equal(JSON.stringify(published).includes(KEY), false);
});

test("anthropic-compatible provider uses the anthropic id, path, and x-api-key", () => {
  const prepared = prepareCustomProvider({
    baseUrl: "https://anthropic-router.example/v1/messages",
    apiKey: KEY,
    model: "claude-sonnet",
    format: "anthropic",
  });
  assert.equal(prepared.id, "anthropic");
  assert.equal(prepared.baseUrl, "https://anthropic-router.example");
  const request = buildInferenceRequest(prepared, {
    messages: [
      { role: "system", content: "be brief" },
      { role: "user", content: "ping" },
    ],
  });
  assert.equal(request.url, "https://anthropic-router.example/v1/messages");
  assert.equal(request.headers["x-api-key"], KEY);
  assert.equal(request.headers.authorization, undefined);
  assert.equal(request.headers["anthropic-version"], "2023-06-01");
  const body = JSON.parse(request.body);
  assert.equal(body.system, "be brief");
  assert.equal(body.messages.length, 1);
  assert.equal(body.max_tokens, 1024);
});

test("rejects keys hidden in the base URL and does not echo them", () => {
  assert.throws(
    () => prepareCustomProvider({
      baseUrl: `https://user:${KEY}@router.example/v1`,
      apiKey: KEY,
      model: "m",
      format: "openai",
    }),
    (error) => {
      assert.equal(error.message.includes(KEY), false);
      return true;
    },
  );
  assert.throws(
    () => prepareCustomProvider({
      baseUrl: `https://router.example/v1?key=${KEY}`,
      apiKey: KEY,
      model: "m",
      format: "openai",
    }),
    (error) => {
      assert.equal(error.message.includes(KEY), false);
      return true;
    },
  );
});

test("a mock OpenAI-compatible server receives the routed request and errors stay redacted", async () => {
  const seen = [];
  const server = http.createServer((req, res) => {
    const chunks = [];
    req.on("data", (chunk) => chunks.push(chunk));
    req.on("end", () => {
      const raw = Buffer.concat(chunks).toString("utf8");
      seen.push({ method: req.method, url: req.url, authorization: req.headers.authorization, body: raw });
      const parsed = raw ? JSON.parse(raw) : {};
      if (parsed.model === "fail-model") {
        res.writeHead(401, { "content-type": "application/json" });
        res.end(JSON.stringify({ error: `bad ${req.headers.authorization}` }));
        return;
      }
      res.writeHead(200, { "content-type": "application/json" });
      res.end(JSON.stringify({
        id: "chatcmpl-test",
        choices: [{ message: { role: "assistant", content: "pong" } }],
      }));
    });
  });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  const { port } = server.address();
  try {
    const prepared = prepareCustomProvider({
      baseUrl: `http://127.0.0.1:${port}/v1`,
      apiKey: KEY,
      model: "router-model",
      format: "openai",
    });
    const result = await completeChat(prepared, {
      messages: [{ role: "user", content: "ping" }],
    });
    assert.equal(result.choices[0].message.content, "pong");
    assert.equal(seen[0].method, "POST");
    assert.equal(seen[0].url, "/v1/chat/completions");
    assert.equal(seen[0].authorization, `Bearer ${KEY}`);
    assert.equal(JSON.parse(seen[0].body).model, "router-model");
    assert.equal(seen[0].body.includes(KEY), false);

    const failing = prepareCustomProvider({
      baseUrl: `http://127.0.0.1:${port}/v1`,
      apiKey: KEY,
      model: "fail-model",
      format: "openai",
    });
    await assert.rejects(completeChat(failing, { messages: [{ role: "user", content: "ping" }] }), (error) => {
      assert.equal(String(error.message).includes(KEY), false);
      assert.match(error.message, /\[redacted\]/);
      return true;
    });
  } finally {
    await new Promise((resolve, reject) => server.close((error) => error ? reject(error) : resolve()));
  }
});

test("redactSecrets removes the key even when the provider echoes it", () => {
  assert.equal(redactSecrets(`token ${KEY} leaked`, [KEY]).includes(KEY), false);
});
