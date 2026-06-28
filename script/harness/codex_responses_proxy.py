"""OpenAI *Responses* API -> xf-yun (OpenAI *Chat Completions*) shim, so the Codex CLI
(>=0.142, which dropped `wire_api = "chat"` for custom providers and now speaks only the
Responses API) can be driven by the xf-yun qwen3.6-35b-a3b chat gateway.

Codex POSTs {base_url}/responses with a flat Responses request (instructions + input items +
flat function tools) and consumes an SSE event stream. This shim translates the request down
to a single non-streaming /chat/completions call against xf-yun (with enable_thinking +
reasoning_effort, the same wire format the SkillStrata curate run used), then re-emits the
minimal Responses SSE event sequence Codex needs (created -> per output item -> completed).

Run:  XFYUN_API_KEY=... PORT=8796 python codex_responses_proxy.py
Codex provider: base_url=http://127.0.0.1:8796/v1  wire_api="responses"  env_key=...
"""
import asyncio
import json
import os
import uuid

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse

BASE = os.environ.get("XFYUN_BASE_URL", "https://maas-api.cn-huabei-1.xf-yun.com/v2").rstrip("/")
KEY = os.environ.get("XFYUN_API_KEY", "")
MODEL = os.environ.get("XFYUN_MODEL", "xopqwen36v35b")
EFFORT = os.environ.get("XFYUN_EFFORT", "medium")
THINKING = os.environ.get("XFYUN_THINKING", "true").lower() in ("1", "true", "yes")

app = FastAPI()


def _text_of_parts(content):
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    out = []
    for p in content:
        if isinstance(p, dict) and p.get("type") in ("input_text", "output_text", "text", "summary_text"):
            out.append(p.get("text", ""))
        elif isinstance(p, str):
            out.append(p)
    return "".join(out)


def responses_to_chat(body):
    """Flat Responses request -> OpenAI chat request for xf-yun."""
    msgs = []
    instr = body.get("instructions")
    if instr:
        msgs.append({"role": "system", "content": instr if isinstance(instr, str) else _text_of_parts(instr)})

    inp = body.get("input", [])
    if isinstance(inp, str):
        msgs.append({"role": "user", "content": inp})
        inp = []
    for item in inp or []:
        if not isinstance(item, dict):
            continue
        t = item.get("type", "message")
        if t == "message":
            role = item.get("role", "user")
            text = _text_of_parts(item.get("content", ""))
            if role == "assistant":
                msgs.append({"role": "assistant", "content": text or None})
            elif role in ("system", "developer"):
                msgs.append({"role": "system", "content": text})
            else:
                msgs.append({"role": "user", "content": text})
        elif t == "function_call":
            msgs.append({"role": "assistant", "content": None,
                         "tool_calls": [{"id": item.get("call_id") or item.get("id"),
                                         "type": "function",
                                         "function": {"name": item.get("name", ""),
                                                      "arguments": item.get("arguments", "") or "{}"}}]})
        elif t == "function_call_output":
            out = item.get("output", "")
            msgs.append({"role": "tool", "tool_call_id": item.get("call_id"),
                         "content": out if isinstance(out, str) else json.dumps(out)})
        # reasoning / other item types are dropped

    out = {"model": MODEL, "messages": msgs,
           "temperature": body.get("temperature", 0.0),
           "max_tokens": body.get("max_output_tokens", 8192)}
    if THINKING:
        out["enable_thinking"] = True
        out["reasoning_effort"] = (body.get("reasoning") or {}).get("effort", EFFORT) if isinstance(body.get("reasoning"), dict) else EFFORT

    tools = body.get("tools")
    chat_tools = []
    for tdef in tools or []:
        if tdef.get("type") == "function":
            # Responses flat function tool: {type, name, description, parameters}
            name = tdef.get("name") or (tdef.get("function") or {}).get("name")
            desc = tdef.get("description") or (tdef.get("function") or {}).get("description", "")
            params = tdef.get("parameters") or (tdef.get("function") or {}).get("parameters") or {"type": "object"}
            if name:
                chat_tools.append({"type": "function",
                                   "function": {"name": name, "description": desc, "parameters": params}})
    if chat_tools:
        out["tools"] = chat_tools
        tc = body.get("tool_choice")
        if isinstance(tc, dict) and tc.get("type") == "function":
            out["tool_choice"] = {"type": "function", "function": {"name": tc.get("name")}}
        elif tc in ("required", "auto", "none"):
            out["tool_choice"] = tc
        else:
            out["tool_choice"] = "auto"
    return out


async def call_xfyun(payload):
    last = None
    async with httpx.AsyncClient(timeout=300) as c:
        for attempt in range(6):
            try:
                r = await c.post(f"{BASE}/chat/completions",
                                 headers={"Authorization": f"Bearer {KEY}"}, json=payload)
                if r.status_code == 429 or r.status_code >= 500:
                    last = httpx.HTTPStatusError(str(r.status_code), request=r.request, response=r)
                    await asyncio.sleep(min(20, 3 * (attempt + 1)))
                    continue
                r.raise_for_status()
                return r.json()
            except (httpx.TimeoutException, httpx.ConnectError, httpx.ReadError) as e:
                last = e
                await asyncio.sleep(3 * (attempt + 1))
        raise last if last else RuntimeError("call_xfyun failed")


def build_output_items(choice):
    """Chat choice -> Responses output items list."""
    msg = choice.get("message", {}) or {}
    items = []
    text = msg.get("content")
    if text:
        items.append({"type": "message", "id": f"msg_{uuid.uuid4().hex[:24]}", "status": "completed",
                      "role": "assistant", "content": [{"type": "output_text", "text": text, "annotations": []}]})
    for tc in msg.get("tool_calls") or []:
        fn = tc.get("function", {}) or {}
        items.append({"type": "function_call", "id": f"fc_{uuid.uuid4().hex[:24]}",
                      "call_id": tc.get("id") or f"call_{uuid.uuid4().hex[:20]}",
                      "name": fn.get("name", ""), "arguments": fn.get("arguments", "") or "{}",
                      "status": "completed"})
    if not items:
        items.append({"type": "message", "id": f"msg_{uuid.uuid4().hex[:24]}", "status": "completed",
                      "role": "assistant", "content": [{"type": "output_text", "text": "", "annotations": []}]})
    return items


def sse(event, data):
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@app.post("/v1/responses")
@app.post("/responses")
async def responses(req: Request):
    body = await req.json()
    stream = body.get("stream", True)
    payload = responses_to_chat(body)
    rid = f"resp_{uuid.uuid4().hex[:24]}"

    try:
        resp = await call_xfyun(payload)
    except Exception as e:
        err = {"type": "error", "code": "upstream_error", "message": type(e).__name__}
        if not stream:
            return JSONResponse(status_code=502, content={"error": err})

        async def egen():
            yield sse("response.failed", {"type": "response.failed",
                      "response": {"id": rid, "status": "failed", "error": err}})
        return StreamingResponse(egen(), media_type="text/event-stream")

    choice = (resp.get("choices") or [{}])[0]
    items = build_output_items(choice)
    u = resp.get("usage", {}) or {}
    usage = {"input_tokens": u.get("prompt_tokens", 0), "output_tokens": u.get("completion_tokens", 0),
             "total_tokens": u.get("total_tokens", 0)}
    base_resp = {"id": rid, "object": "response", "status": "completed", "model": MODEL,
                 "output": items, "usage": usage, "error": None, "incomplete_details": None,
                 "instructions": None, "metadata": {}}

    if not stream:
        return JSONResponse(base_resp)

    async def gen():
        created = {"id": rid, "object": "response", "status": "in_progress", "model": MODEL,
                   "output": [], "usage": None, "error": None}
        yield sse("response.created", {"type": "response.created", "response": created})
        yield sse("response.in_progress", {"type": "response.in_progress", "response": created})
        for idx, item in enumerate(items):
            yield sse("response.output_item.added",
                      {"type": "response.output_item.added", "output_index": idx,
                       "item": {k: v for k, v in item.items() if k != "content"} if item["type"] == "function_call" else
                               {"type": "message", "id": item["id"], "status": "in_progress",
                                "role": "assistant", "content": []}})
            if item["type"] == "message":
                text = item["content"][0]["text"]
                yield sse("response.content_part.added",
                          {"type": "response.content_part.added", "item_id": item["id"],
                           "output_index": idx, "content_index": 0,
                           "part": {"type": "output_text", "text": "", "annotations": []}})
                yield sse("response.output_text.delta",
                          {"type": "response.output_text.delta", "item_id": item["id"],
                           "output_index": idx, "content_index": 0, "delta": text})
                yield sse("response.output_text.done",
                          {"type": "response.output_text.done", "item_id": item["id"],
                           "output_index": idx, "content_index": 0, "text": text})
                yield sse("response.content_part.done",
                          {"type": "response.content_part.done", "item_id": item["id"],
                           "output_index": idx, "content_index": 0,
                           "part": {"type": "output_text", "text": text, "annotations": []}})
            else:  # function_call
                yield sse("response.function_call_arguments.delta",
                          {"type": "response.function_call_arguments.delta", "item_id": item["id"],
                           "output_index": idx, "delta": item["arguments"]})
                yield sse("response.function_call_arguments.done",
                          {"type": "response.function_call_arguments.done", "item_id": item["id"],
                           "output_index": idx, "arguments": item["arguments"]})
            yield sse("response.output_item.done",
                      {"type": "response.output_item.done", "output_index": idx, "item": item})
        yield sse("response.completed", {"type": "response.completed", "response": base_resp})

    return StreamingResponse(gen(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn
    if not KEY:
        raise SystemExit("XFYUN_API_KEY is required")
    print(f"codex_responses_proxy -> {BASE} model={MODEL} thinking={THINKING} effort={EFFORT}", flush=True)
    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("PORT", "8796")), log_level="warning")
