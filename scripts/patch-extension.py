#!/usr/bin/env python3
"""Patch a PermawebOS Chrome extension build so a custom AI router can be saved.

The upstream bundles only offer OpenAI, Anthropic, OpenRouter, and APUS, and
they pin those providers to their vendor base URLs. This rewrites the built
assets in place and copies extension/custom-provider.js next to them. The API
key stays in the encrypted provider credential and in the node's private
`priv` map; it is not written into the base URL.

usage: patch-extension.py <unpacked-chrome-dir>
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "extension" / "custom-provider.js"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected 1 match, found {count}")
    return text.replace(old, new, 1)


def patch_inference(text: str) -> str:
    text = replace_once(
        text,
        'import{t as e}from"./copy-DoL0gc1A.js";',
        'import{bootConfigFragment as __bootFragment,prepareCustomProvider as __prepareCustom}from"./custom-provider.js";import{t as e}from"./copy-DoL0gc1A.js";',
        "inference import",
    )
    text = replace_once(
        text,
        ",apus:{label:`APUS (free)`,baseUrl:`https://hb.apus.network/~inference@1.0/v1`,requiresKey:!1}}",
        ",apus:{label:`APUS (free)`,baseUrl:`https://hb.apus.network/~inference@1.0/v1`,requiresKey:!1},custom:{label:`Custom router`,baseUrl:``,requiresKey:!0,custom:!0}}",
        "provider catalogue",
    )
    text = replace_once(
        text,
        "apiKey:`API key`,",
        "apiKey:`API key`,baseUrl:`Base URL`,format:`API format`,customHint:`OpenAI-compatible requests use /chat/completions and a Bearer token. Anthropic-compatible requests use /v1/messages and x-api-key. The key stays in the node's private config.`,",
        "provider copy",
    )
    text = replace_once(
        text,
        "function $r(e){if(e===null)return null;if(!e||",
        "function $r(e){if(e===null)return null;if(e&&typeof e==`object`&&e.provider===`custom`){let t=__prepareCustom({baseUrl:e.baseUrl,apiKey:e.apiKey,model:e.model,format:e.format});return{provider:t.id,apiKey:t.apiKey,model:t.model,baseUrl:t.baseUrl,format:t.format}}if(!e||",
        "local provider validator",
    )
    text = replace_once(
        text,
        "function ll({provider:e,apiKey:t,model:n}={}){if(!e)return{};let r=sl[e];",
        "function ll({provider:e,apiKey:t,model:n,baseUrl:o,format:s}={}){if(!e)return{};if(e===`custom`)return __bootFragment(__prepareCustom({baseUrl:o,apiKey:t,model:String(n||``).split(/[\\r\\n,]+/).map(e=>e.trim()).find(Boolean)||``,format:s}));let r=sl[e];",
        "boot config builder",
    )
    return text


def patch_background(text: str) -> str:
    text = replace_once(
        text,
        'import{n as e}from"./rolldown-runtime-hePW80VL.js";',
        'import{prepareCustomProvider as __prepareCustom}from"./custom-provider.js";import{n as e}from"./rolldown-runtime-hePW80VL.js";',
        "background import",
    )
    # Insert a balanced early return. Do not rewrite the original tail: an extra
    # closing brace there parses in Node and is a SyntaxError in current Chrome.
    needle = "n.admin||Z(`unauthorized`,k.admin),[`openrouter`,`openai`,`anthropic`].includes(t.provider)"
    insert = (
        "if(t.provider===`custom`){let __c=__prepareCustom({baseUrl:t.baseUrl,apiKey:t.apiKey,"
        "model:Array.isArray(t.models)?t.models[0]:\"\",format:t.format});"
        "let __f={id:__c.id,name:__c.name,format:__c.format,enabled:!0,\"base-url\":__c.baseUrl,"
        "models:[{id:__c.model}],\"default-model\":__c.model};"
        "let __u=await ld(JSON.stringify({key:__c.apiKey}),n.publicKey);"
        "let __d={mode:`replace`,envelope:{\"encrypted-key\":__u.encryptedKey,"
        "\"encrypted-iv\":__u.encryptedIv,\"encrypted-tag\":__u.encryptedTag,ciphertext:__u.ciphertext}};"
        "let __saved=await s(n,__f,__d);"
        "return{inventory:Md(__saved),models:[{id:__c.id+\"/\"+__c.model,label:__c.model,"
        "providerName:__c.name,isRecommended:!0}]};}"
    )
    return replace_once(text, needle, insert + needle, "background custom branch")


def patch_ui(text: str) -> str:
    text = replace_once(
        text,
        "aiKey:`Include an API key now`,",
        "aiKey:`Include an API key now`,baseUrl:`Base URL`,format:`API format`,customHint:`OpenAI-compatible requests use /chat/completions and a Bearer token. Anthropic-compatible requests use /v1/messages and x-api-key. The key stays in the node's private config.`,",
        "setup copy",
    )
    text = replace_once(
        text,
        "[k,A]=G.useState(`choose`),[j,N]=G.useState(`openrouter`),[P,F]=G.useState(``),[ee,te]=G.useState(``)",
        "[k,A]=G.useState(`choose`),[j,N]=G.useState(`openrouter`),[__base,setBase]=G.useState(``),[__fmt,setFmt]=G.useState(`openai`),[P,F]=G.useState(``),[ee,te]=G.useState(``)",
        "chat provider state",
    )
    text = replace_once(
        text,
        "request:{action:`save`,provider:j,apiKey:n,...ee.trim()?{models:ee.split(/[,\\n]/).map(e=>e.trim()).filter(Boolean)}:{}}",
        "request:{action:`save`,provider:j,apiKey:n,...j===`custom`?{baseUrl:__base.trim(),format:__fmt}:{},...ee.trim()?{models:ee.split(/[,\\n]/).map(e=>e.trim()).filter(Boolean)}:{}}",
        "chat save payload",
    )
    text = replace_once(
        text,
        "provider:j,setProvider:Ye,apiKey:P,setApiKey:F,providerModels:ee,setProviderModels:te,",
        "provider:j,setProvider:Ye,baseUrl:__base,setBaseUrl:setBase,format:__fmt,setFormat:setFmt,apiKey:P,setApiKey:F,providerModels:ee,setProviderModels:te,",
        "chat provider fields",
    )
    text = replace_once(
        text,
        "options:[{value:`openrouter`,label:`OpenRouter`},{value:`openai`,label:`OpenAI`},{value:`anthropic`,label:`Anthropic`}]}),(0,K.jsx)(RC,{label:V.apiKey",
        "options:[{value:`openrouter`,label:`OpenRouter`},{value:`openai`,label:`OpenAI`},{value:`anthropic`,label:`Anthropic`},{value:`custom`,label:`Custom router`}]}),t.provider===`custom`&&(0,K.jsx)(jl,{label:V.format,value:t.format,onChange:t.setFormat,disabled:t.busy,options:[{value:`openai`,label:`OpenAI-compatible`},{value:`anthropic`,label:`Anthropic-compatible`}]}),t.provider===`custom`&&(0,K.jsx)(RC,{label:V.baseUrl,value:t.baseUrl,onChange:e=>t.setBaseUrl(e.target.value),autoComplete:`off`,disabled:t.busy,hint:V.customHint}),(0,K.jsx)(RC,{label:V.apiKey",
        "chat provider fields jsx",
    )
    text = replace_once(
        text,
        "disabled:!t.apiKey.trim(),onClick:()=>void t.saveProvider()",
        "disabled:!t.apiKey.trim()||t.provider===`custom`&&(!String(t.baseUrl||``).trim()||!String(t.providerModels||``).trim()),onClick:()=>void t.saveProvider()",
        "chat save button",
    )
    text = replace_once(
        text,
        "[v,y]=G.useState(`chatgpt`),b=v===`key`,[x,S]=G.useState(`openrouter`),[C,w]=G.useState(``),[T,E]=G.useState(``)",
        "[v,y]=G.useState(`chatgpt`),b=v===`key`,[x,S]=G.useState(`openrouter`),[__b,setB]=G.useState(``),[__f,setF]=G.useState(`openai`),[C,w]=G.useState(``),[T,E]=G.useState(``)",
        "setup provider state",
    )
    text = replace_once(
        text,
        "inference:P&&b?{provider:x,apiKey:C.trim(),model:T.trim()}:P&&v===`apus`?{provider:`apus`,apiKey:``,model:``}:void 0",
        "inference:P&&b?{provider:x,apiKey:C.trim(),model:T.trim(),...x===`custom`?{baseUrl:__b.trim(),format:__f}:{}}:P&&v===`apus`?{provider:`apus`,apiKey:``,model:``}:void 0",
        "setup inference payload",
    )
    text = replace_once(
        text,
        "provider:x,setProvider:S,apiKey:C,setApiKey:w,model:T,setModel:E,",
        "provider:x,setProvider:S,baseUrl:__b,setBaseUrl:setB,format:__f,setFormat:setF,apiKey:C,setApiKey:w,model:T,setModel:E,",
        "setup returned fields",
    )
    text = replace_once(
        text,
        '"inference-provider":e.inference?.provider||`intelligence-pool`',
        '"inference-provider":a[`inference-provider`]||e.inference?.provider||`intelligence-pool`',
        "boot provider id",
    )
    text = replace_once(
        text,
        "options:mc.map(e=>({value:e.id,label:e.label,iconName:Nc(e.id)}))}),(0,K.jsx)(RC,{label:`API key`,type:`password`,autoComplete:`off`,value:t.apiKey,onChange:e=>t.setApiKey(e.target.value)}),(0,K.jsx)(fw,{id:`node-provider-models`",
        "options:mc.map(e=>({value:e.id,label:e.label,iconName:Nc(e.id)}))}),t.provider===`custom`&&(0,K.jsx)(jl,{label:Y.format,value:t.format,onChange:t.setFormat,options:[{value:`openai`,label:`OpenAI-compatible`},{value:`anthropic`,label:`Anthropic-compatible`}]}),t.provider===`custom`&&(0,K.jsx)(RC,{label:Y.baseUrl,value:t.baseUrl,onChange:e=>t.setBaseUrl(e.target.value),autoComplete:`off`,hint:Y.customHint}),(0,K.jsx)(RC,{label:`API key`,type:`password`,autoComplete:`off`,value:t.apiKey,onChange:e=>t.setApiKey(e.target.value)}),(0,K.jsx)(fw,{id:`node-provider-models`",
        "setup provider fields jsx",
    )
    text = replace_once(
        text,
        "inferenceModel:`Model ID (optional except OpenRouter)`,",
        "inferenceModel:`Model ID (optional except OpenRouter)`,inferenceBase:`Base URL`,inferenceFormat:`API format`,inferenceCustom:`OpenAI-compatible requests use /chat/completions and a Bearer token. Anthropic-compatible requests use /v1/messages and x-api-key. The key stays in the node's private config.`,",
        "local provider copy",
    )
    text = replace_once(
        text,
        "var OC=[{value:`anthropic`,label:`Anthropic`},{value:`openai`,label:`OpenAI`},{value:`openrouter`,label:`OpenRouter`}];",
        "var OC=[{value:`anthropic`,label:`Anthropic`},{value:`openai`,label:`OpenAI`},{value:`openrouter`,label:`OpenRouter`},{value:`custom`,label:`Custom router`}];",
        "local provider options",
    )
    text = replace_once(
        text,
        "function Ec(e,t){let n=e.runtime?.inferenceSettings,[r,i]=G.useState(n?.provider??`anthropic`),[a,o]=G.useState(n?.model??``),[s,c]=G.useState(``),[l,u]=G.useState(``);G.useEffect(()=>{i(n?.provider??`anthropic`),o(n?.model??``),c(``)},[n?.provider,n?.model]);function d(e){i(e),o(e===n?.provider?n.model:``),c(``),u(``)}async function f(e=!1){u(``);try{let n=Le(e?null:{provider:r,model:a.trim(),apiKey:s.trim()});c(``),await t({action:`configureInference`,settings:n})}catch(e){u(M(e,`Could not update the AI provider.`))}}return{provider:r,model:a,apiKey:s,error:l,changeProvider:d,setModel:o,setApiKey:c,save:f}}",
        "function Ec(e,t){let n=e.runtime?.inferenceSettings,[r,i]=G.useState(n?.provider??`anthropic`),[a,o]=G.useState(n?.model??``),[s,c]=G.useState(``),[__lb,__sb]=G.useState(n?.baseUrl??``),[__lf,__sf]=G.useState(n?.format??`openai`),[l,u]=G.useState(``);G.useEffect(()=>{i(n?.provider??`anthropic`),o(n?.model??``),c(``),__sb(n?.baseUrl??``),__sf(n?.format??`openai`)},[n?.provider,n?.model,n?.baseUrl,n?.format]);function d(e){i(e),o(e===n?.provider?n.model:``),c(``),__sb(``),__sf(`openai`),u(``)}async function f(e=!1){u(``);try{let n=Le(e?null:{provider:r,model:a.trim(),apiKey:s.trim(),...r===`custom`?{baseUrl:__lb.trim(),format:__lf}:{}});c(``),await t({action:`configureInference`,settings:n})}catch(e){u(M(e,`Could not update the AI provider.`))}}return{provider:r,model:a,apiKey:s,baseUrl:__lb,format:__lf,error:l,changeProvider:d,setModel:o,setApiKey:c,setBaseUrl:__sb,setFormat:__sf,save:f}}",
        "local provider state",
    )
    text = replace_once(
        text,
        "(0,K.jsx)(jl,{label:AC.inferenceTitle,value:t.provider,options:OC,onChange:t.changeProvider,disabled:e.busy}),(0,K.jsx)(RC,{label:AC.inferenceModel",
        "(0,K.jsx)(jl,{label:AC.inferenceTitle,value:t.provider,options:OC,onChange:t.changeProvider,disabled:e.busy}),t.provider===`custom`&&(0,K.jsx)(jl,{label:AC.inferenceFormat,value:t.format,onChange:t.setFormat,disabled:e.busy,options:[{value:`openai`,label:`OpenAI-compatible`},{value:`anthropic`,label:`Anthropic-compatible`}]}),t.provider===`custom`&&(0,K.jsx)(RC,{label:AC.inferenceBase,value:t.baseUrl,onChange:e=>t.setBaseUrl(e.target.value),autoComplete:`off`,disabled:e.busy,hint:AC.inferenceCustom}),(0,K.jsx)(RC,{label:AC.inferenceModel",
        "local provider fields jsx",
    )
    text = replace_once(
        text,
        'Tw={openrouter:`deepseek/deepseek-chat`,openai:`gpt-4.1-mini`,anthropic:`claude-sonnet-5-5`}',
        'Tw={openrouter:`deepseek/deepseek-chat`,openai:`gpt-4.1-mini`,anthropic:`claude-sonnet-5-5`,custom:`your-model-id`}',
        "model placeholder",
    )
    return text


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__.strip().splitlines()[-1], file=sys.stderr)
        return 2
    chrome = Path(sys.argv[1]).resolve()
    assets = chrome / "assets"
    if not (assets / "inferenceProviders-Bh8L1C2S.js").is_file():
        print(f"{chrome}: not an unpacked PermawebOS extension", file=sys.stderr)
        return 1
    shutil.copyfile(MODULE, assets / "custom-provider.js")
    targets = {
        "inferenceProviders-Bh8L1C2S.js": patch_inference,
        "backgroundRuntimeAdapter-CAgnwlYo.js": patch_background,
        "build-DFedidco.js": patch_ui,
    }
    for name, patch in targets.items():
        path = assets / name
        path.write_text(patch(path.read_text(encoding="utf-8")), encoding="utf-8")
        print(f"patched {name}")
    manifest = chrome / "manifest.json"
    original = manifest.read_text(encoding="utf-8")
    updated = replace_once(original, '"version": "0.1.3"', '"version": "0.1.4"', "manifest version")
    manifest.write_text(updated, encoding="utf-8")
    version_files = {
        "assets/clientCopy-DA2faWDs.js": ("var e=`0.1.3`", "var e=`0.1.4`"),
        "injected.js": ("n=`0.1.3`", "n=`0.1.4`"),
        "content.js": ("badge:`v0.1.3`", "badge:`v0.1.4`"),
    }
    for name, (old, new) in version_files.items():
        path = chrome / name
        path.write_text(replace_once(path.read_text(encoding="utf-8"), old, new, name), encoding="utf-8")
        print(f"patched {name} -> 0.1.4")
    print("patched manifest.json -> 0.1.4")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
