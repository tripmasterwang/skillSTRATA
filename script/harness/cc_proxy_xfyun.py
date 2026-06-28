"""Anthropic Messages API -> xf-yun (OpenAI chat) adapter, so Claude Code can be driven
by the xf-yun qwen3.6 gateway. Derived from RevDu's mimu_cc_proxy.py, with three changes:
  1. creds come from XFYUN_BASE_URL / XFYUN_API_KEY / XFYUN_MODEL env (no RevDu key file),
  2. the outgoing OpenAI body carries enable_thinking + reasoning_effort (xf-yun reasoning
     mode, same wire format the SkillStrata curate run used),
  3. the global single-concurrency upstream lock is REMOVED -- xf-yun handles concurrent
     calls, and Claude Code at --workers 40 must not be serialised through one mutex.

Run:  XFYUN_API_KEY=... PORT=8790 python cc_proxy_xfyun.py
Point Claude Code at it:  ANTHROPIC_BASE_URL=http://127.0.0.1:8790  ANTHROPIC_AUTH_TOKEN=dummy
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


# ---------- Anthropic request -> OpenAI chat request ----------
def _text_of(content):
    if isinstance(content, str):
        return content
    return "".join(b.get("text", "") for b in content
                   if isinstance(b, dict) and b.get("type") == "text")


def to_openai(body):
    msgs = []
    sys = body.get("system")
    if sys:
        msgs.append({"role": "system", "content": _text_of(sys)})
    for m in body.get("messages", []):
        role, content = m.get("role"), m.get("content")
        if isinstance(content, str):
            msgs.append({"role": role, "content": content})
            continue
        text_parts, tool_calls, tool_results = [], [], []
        for b in content:
            t = b.get("type")
            if t == "text":
                text_parts.append(b.get("text", ""))
            elif t == "tool_use":
                tool_calls.append({"id": b.get("id"), "type": "function",
                                   "function": {"name": b.get("name"),
                                                "arguments": json.dumps(b.get("input", {}))}})
            elif t == "tool_result":
                tc = b.get("content")
                tool_results.append({"role": "tool", "tool_call_id": b.get("tool_use_id"),
                                     "content": _text_of(tc) if not isinstance(tc, str) else tc})
        if role == "assistant":
            a = {"role": "assistant", "content": "".join(text_parts) or None}
            if tool_calls:
                a["tool_calls"] = tool_calls
            msgs.append(a)
        else:
            if text_parts:
                msgs.append({"role": "user", "content": "".join(text_parts)})
            msgs.extend(tool_results)
    out = {"model": MODEL, "messages": msgs,
           "max_tokens": body.get("max_tokens", 8192),
           "temperature": body.get("temperature", 0.0)}
    if THINKING:
        out["enable_thinking"] = True
        out["reasoning_effort"] = EFFORT
    if body.get("stop_sequences"):
        out["stop"] = body["stop_sequences"]
    tools = body.get("tools")
    if tools:
        out["tools"] = [{"type": "function",
                         "function": {"name": t["name"], "description": t.get("description", ""),
                                      "parameters": t.get("input_schema", {"type": "object"})}}
                        for t in tools]
        tc = body.get("tool_choice", {})
        if tc.get("type") == "tool":
            out["tool_choice"] = {"type": "function", "function": {"name": tc.get("name")}}
        elif tc.get("type") == "any":
            out["tool_choice"] = "required"
        else:
            out["tool_choice"] = "auto"
    return out


# ---------- OpenAI response -> Anthropic blocks ----------
_STOP = {"stop": "end_turn", "length": "max_tokens", "tool_calls": "tool_use",
         "content_filter": "end_turn", None: "end_turn"}


def to_anthropic_blocks(choice):
    msg = choice.get("message", {})
    blocks = []
    if msg.get("content"):
        blocks.append({"type": "text", "text": msg["content"]})
    for tc in msg.get("tool_calls") or []:
        fn = tc.get("function", {})
        try:
            inp = json.loads(fn.get("arguments") or "{}")
        except Exception:
            inp = {}
        blocks.append({"type": "tool_use", "id": tc.get("id") or f"toolu_{uuid.uuid4().hex[:20]}",
                       "name": fn.get("name"), "input": inp})
    stop = _STOP.get(choice.get("finish_reason"), "end_turn")
    if msg.get("tool_calls"):
        stop = "tool_use"
    return blocks, stop


async def call_xfyun(payload):
    last = None
    async with httpx.AsyncClient(timeout=300) as c:
        for attempt in range(6):
            try:
                r = await c.post(f"{BASE}/chat/completions",
                                 headers={"Authorization": f"Bearer {KEY}"}, json=payload)
                if r.status_code == 429:
                    last = httpx.HTTPStatusError("429", request=r.request, response=r)
                    await asyncio.sleep(min(20, 3 * (attempt + 1)))
                    continue
                if r.status_code >= 500:
                    last = httpx.HTTPStatusError(f"{r.status_code}", request=r.request, response=r)
                    await asyncio.sleep(3 * (attempt + 1))
                    continue
                r.raise_for_status()
                return r.json()
            except (httpx.TimeoutException, httpx.ConnectError, httpx.ReadError) as e:
                last = e
                await asyncio.sleep(3 * (attempt + 1))
        raise last if last else RuntimeError("call_xfyun failed")


def sse(event, data):
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@app.post("/v1/messages")
async def messages(req: Request):
    body = await req.json()
    stream = bool(body.get("stream"))
    payload = to_openai(body)
    mid = f"msg_{uuid.uuid4().hex[:24]}"

    if not stream:
        try:
            resp = await call_xfyun(payload)
        except Exception as e:
            return JSONResponse(status_code=529, content={"type": "error",
                "error": {"type": "overloaded_error", "message": type(e).__name__}})
        choice = (resp.get("choices") or [{}])[0]
        blocks, stop = to_anthropic_blocks(choice)
        u = resp.get("usage", {})
        return JSONResponse({"id": mid, "type": "message", "role": "assistant",
                             "model": body.get("model", MODEL), "content": blocks,
                             "stop_reason": stop, "stop_sequence": None,
                             "usage": {"input_tokens": u.get("prompt_tokens", 0),
                                       "output_tokens": u.get("completion_tokens", 0)}})

    async def gen():
        yield sse("message_start", {"type": "message_start", "message": {
            "id": mid, "type": "message", "role": "assistant", "model": body.get("model", MODEL),
            "content": [], "stop_reason": None, "stop_sequence": None,
            "usage": {"input_tokens": 0, "output_tokens": 0}}})
        task = asyncio.create_task(call_xfyun(payload))
        while True:
            done, _ = await asyncio.wait({task}, timeout=10)
            if done:
                break
            yield sse("ping", {"type": "ping"})
        try:
            resp = task.result()
        except Exception as e:
            yield sse("error", {"type": "error", "error": {"type": "overloaded_error",
                      "message": type(e).__name__}})
            return
        choice = (resp.get("choices") or [{}])[0]
        blocks, stop = to_anthropic_blocks(choice)
        out_tok = resp.get("usage", {}).get("completion_tokens", 0)
        for i, blk in enumerate(blocks):
            if blk["type"] == "text":
                yield sse("content_block_start", {"type": "content_block_start", "index": i,
                          "content_block": {"type": "text", "text": ""}})
                yield sse("content_block_delta", {"type": "content_block_delta", "index": i,
                          "delta": {"type": "text_delta", "text": blk["text"]}})
            else:
                yield sse("content_block_start", {"type": "content_block_start", "index": i,
                          "content_block": {"type": "tool_use", "id": blk["id"],
                                            "name": blk["name"], "input": {}}})
                yield sse("content_block_delta", {"type": "content_block_delta", "index": i,
                          "delta": {"type": "input_json_delta",
                                    "partial_json": json.dumps(blk["input"])}})
            yield sse("content_block_stop", {"type": "content_block_stop", "index": i})
        yield sse("message_delta", {"type": "message_delta",
                  "delta": {"stop_reason": stop, "stop_sequence": None},
                  "usage": {"output_tokens": out_tok}})
        yield sse("message_stop", {"type": "message_stop"})

    return StreamingResponse(gen(), media_type="text/event-stream")


@app.post("/v1/messages/count_tokens")
async def count_tokens(req: Request):
    body = await req.json()
    n = len(_text_of(body.get("system", "")))
    for m in body.get("messages", []):
        n += len(_text_of(m.get("content", "")))
    return JSONResponse({"input_tokens": max(1, n // 4)})


if __name__ == "__main__":
    import uvicorn
    if not KEY:
        raise SystemExit("XFYUN_API_KEY is required")
    print(f"cc_proxy_xfyun -> {BASE} model={MODEL} thinking={THINKING} effort={EFFORT}", flush=True)
    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("PORT", "8790")), log_level="warning")
