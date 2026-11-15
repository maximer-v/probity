"""OpenRouter client: pinned, cached, priced, and incapable of overspending.

Three things this wrapper exists to guarantee, none of which the API gives you by
default:

**Pinning.** ``provider.order`` with ``allow_fallbacks: false`` means a rerun hits the
same provider. Without it, OpenRouter may route the same model to a different backend
with different numerics, and a "reproducibility" measurement becomes a measurement of
routing luck. The provider that actually served each request is read back from the
response and logged, so the claim is checked rather than assumed.

**A hard budget.** Every call is priced from the response's usage and added to a ledger
on disk. When the cap is reached the next call raises :class:`BudgetExhausted` instead of
spending. A benchmark that can run away with a credit card is not a benchmark.

**A cache keyed by content.** The key is a hash of the model, the parameters and the
exact payload, so re-running a partially finished sweep costs nothing for the work
already done, and a replay is free. The cache is what makes ``replay_hash`` meaningful.

The API key is read from the environment (``OPENROUTER_API_KEY``) or from a ``.env``
that is git-ignored. It is never written to the cache, the ledger or any log.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import time
from dataclasses import dataclass, field as dc_field
from pathlib import Path
from typing import Any

import requests

API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODELS_URL = "https://openrouter.ai/api/v1/models"
_KEY_RE = re.compile(r"sk-or-v1-[A-Za-z0-9]+")


class BudgetExhausted(RuntimeError):
    pass


class ModelCallFailed(RuntimeError):
    pass


def load_api_key(explicit: str | None = None) -> str:
    """Find the key. Never returns it to a log and never writes it anywhere."""
    if explicit:
        return explicit
    key = os.environ.get("OPENROUTER_API_KEY")
    if key:
        return key
    for candidate in (Path(".env"), Path.home() / ".config" / "probity" / ".env"):
        if candidate.exists():
            for line in candidate.read_text(encoding="utf-8").splitlines():
                if line.strip().startswith("OPENROUTER_API_KEY"):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError(
        "No OpenRouter API key. Set OPENROUTER_API_KEY in the environment or put it in "
        "a .env file (which .gitignore already excludes). The key is never committed.")


def redact(text: str) -> str:
    """Strip anything that looks like a key, for defence in depth on every log path."""
    return _KEY_RE.sub("sk-or-v1-REDACTED", text)


#: How many tokens a model may spend on one reply.
#:
#: A full transcription of a six-page, 162-row statement is around 9,500 tokens of JSON,
#: and a reply cut short is a page read in part. A ceiling is not a cost: billing is on
#: tokens actually produced, so a generous one changes nothing about the price of a run.
OUTPUT_CEILING = 32000


@dataclass
class ModelSpec:
    """One rung of the panel, with its price and its pinned provider."""

    name: str              # our label: "small" | "mid" | "frontier"
    model: str             # the OpenRouter id
    provider: str | None = None
    price_in: float = 0.0   # USD per million prompt tokens
    price_out: float = 0.0
    supports_structured: bool = True
    supports_tools: bool = True
    supports_seed: bool = True
    notes: str = ""

    def cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        return (prompt_tokens * self.price_in + completion_tokens * self.price_out) / 1e6

    def to_json(self) -> dict[str, Any]:
        return {"name": self.name, "model": self.model, "provider": self.provider,
                "price_in_per_mtok": self.price_in, "price_out_per_mtok": self.price_out,
                "supports_structured": self.supports_structured,
                "supports_tools": self.supports_tools, "supports_seed": self.supports_seed,
                "notes": self.notes}


@dataclass
class Response:
    text: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    provider: str | None
    latency_ms: float
    cached: bool
    raw: dict[str, Any] = dc_field(default_factory=dict)
    tool_calls: list[dict[str, Any]] = dc_field(default_factory=list)
    finish_reason: str | None = None


class Ledger:
    """A spend record on disk, so a crashed run cannot lose track of the money."""

    def __init__(self, path: str | Path, cap_usd: float):
        self.path = Path(path)
        self.cap_usd = cap_usd
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.spent = 0.0
        self.calls = 0
        if self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                rec = json.loads(line)
                self.spent += rec.get("cost_usd", 0.0)
                self.calls += 1

    def check(self, label: str = "") -> None:
        if self.spent >= self.cap_usd:
            raise BudgetExhausted(
                f"spend cap reached: ${self.spent:.4f} of ${self.cap_usd:.2f} "
                f"after {self.calls} calls{' at ' + label if label else ''}")

    def record(self, **rec) -> None:
        self.spent += rec.get("cost_usd", 0.0)
        self.calls += 1
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, separators=(",", ":")) + "\n")

    @property
    def remaining(self) -> float:
        return max(0.0, self.cap_usd - self.spent)


class OpenRouterClient:
    def __init__(self, *, cache_dir: str | Path = "benchmark/results/.cache",
                 ledger_path: str | Path = "benchmark/results/spend_ledger.jsonl",
                 cap_usd: float = 15.0, api_key: str | None = None,
                 timeout: float = 240.0, max_retries: int = 3,
                 allow_data_collection: bool = False, offline: bool = False):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ledger = Ledger(ledger_path, cap_usd)
        self.timeout = timeout
        self.max_retries = max_retries
        self.allow_data_collection = allow_data_collection
        self.offline = offline
        self._key = None if offline else load_api_key(api_key)
        self._session = requests.Session()

    # ------------------------------------------------------------------ caching

    def _cache_key(self, payload: dict[str, Any]) -> str:
        blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(blob.encode()).hexdigest()

    def _cache_path(self, key: str) -> Path:
        return self.cache_dir / key[:2] / f"{key}.json"

    # ------------------------------------------------------------------ the call

    def chat(self, spec: ModelSpec, messages: list[dict[str, Any]], *,
             temperature: float = 0.0, seed: int | None = 7,
             max_tokens: int = OUTPUT_CEILING, json_schema: dict[str, Any] | None = None,
             tools: list[dict[str, Any]] | None = None,
             purpose: str = "", use_cache: bool = True) -> Response:
        payload: dict[str, Any] = {
            "model": spec.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if seed is not None and spec.supports_seed:
            payload["seed"] = seed
        if json_schema is not None and spec.supports_structured:
            payload["response_format"] = {"type": "json_schema", "json_schema": json_schema}
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        provider: dict[str, Any] = {"allow_fallbacks": False}
        if spec.provider:
            provider["order"] = [spec.provider]
        if json_schema is not None and spec.supports_structured:
            provider["require_parameters"] = True
        if not self.allow_data_collection:
            # Only endpoints that do not retain or train on the payload.
            provider["data_collection"] = "deny"
        payload["provider"] = provider

        key = self._cache_key(payload)
        cache_file = self._cache_path(key)
        if use_cache and cache_file.exists():
            rec = json.loads(cache_file.read_text(encoding="utf-8"))
            return Response(text=rec["text"], prompt_tokens=rec["prompt_tokens"],
                            completion_tokens=rec["completion_tokens"],
                            cost_usd=0.0, provider=rec.get("provider"),
                            latency_ms=0.0, cached=True, raw=rec.get("raw", {}),
                            tool_calls=rec.get("tool_calls", []),
                            finish_reason=rec.get("finish_reason"))
        if self.offline:
            raise ModelCallFailed(
                f"offline and not cached: {spec.model} ({purpose}). Re-run with network "
                "access, or point --cache at a directory that has this call.")

        self.ledger.check(f"{spec.model}/{purpose}")

        last_error = ""
        for attempt in range(1, self.max_retries + 1):
            t0 = time.perf_counter()
            try:
                resp = self._session.post(
                    API_URL,
                    headers={"Authorization": f"Bearer {self._key}",
                             "Content-Type": "application/json",
                             "X-Title": "probity-benchmark"},
                    json=payload, timeout=self.timeout)
            except requests.RequestException as exc:
                last_error = f"{type(exc).__name__}: {exc}"
                time.sleep(min(2 ** attempt, 20))
                continue
            latency = (time.perf_counter() - t0) * 1000

            if resp.status_code in (429, 500, 502, 503, 520, 524):
                last_error = f"HTTP {resp.status_code}: {redact(resp.text[:300])}"
                time.sleep(min(2 ** attempt, 20))
                continue
            if resp.status_code != 200:
                raise ModelCallFailed(f"HTTP {resp.status_code}: {redact(resp.text[:600])}")

            body = resp.json()
            if "error" in body and not body.get("choices"):
                raise ModelCallFailed(redact(json.dumps(body["error"])[:600]))

            choice = (body.get("choices") or [{}])[0]
            msg = choice.get("message") or {}
            text = msg.get("content") or ""
            if isinstance(text, list):      # some providers return content parts
                text = "".join(p.get("text", "") for p in text if isinstance(p, dict))
            usage = body.get("usage") or {}
            pt = int(usage.get("prompt_tokens") or 0)
            ct = int(usage.get("completion_tokens") or 0)
            # Prefer the provider's own figure when it reports one.
            cost = float(usage.get("cost") or 0.0) or spec.cost(pt, ct)
            prov = body.get("provider")
            tool_calls = msg.get("tool_calls") or []

            self.ledger.record(model=spec.model, provider=prov, purpose=purpose,
                               prompt_tokens=pt, completion_tokens=ct, cost_usd=cost,
                               latency_ms=round(latency, 1), cache_key=key,
                               ts=time.time())
            rec = {"text": text, "prompt_tokens": pt, "completion_tokens": ct,
                   "provider": prov, "tool_calls": tool_calls,
                   "finish_reason": choice.get("finish_reason"),
                   "raw": {"id": body.get("id"), "model": body.get("model")}}
            # A reply the provider aborted is paid for and recorded, but it is not an
            # answer and must not be replayed as one: asking again may succeed.
            if (choice.get("finish_reason") or "").lower() != "error":
                cache_file.parent.mkdir(parents=True, exist_ok=True)
                cache_file.write_text(json.dumps(rec, ensure_ascii=False), encoding="utf-8")

            return Response(text=text, prompt_tokens=pt, completion_tokens=ct,
                            cost_usd=cost, provider=prov, latency_ms=latency,
                            cached=False, raw=rec["raw"], tool_calls=tool_calls,
                            finish_reason=choice.get("finish_reason"))

        raise ModelCallFailed(f"{spec.model} failed after {self.max_retries} attempts: {last_error}")


def image_message(prompt: str, image_paths: list[str], *, detail: str = "high") -> list[dict]:
    """A user message carrying page images as data URLs."""
    content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
    for path in image_paths:
        data = Path(path).read_bytes()
        b64 = base64.b64encode(data).decode()
        mime = "image/png" if str(path).lower().endswith(".png") else "image/jpeg"
        content.append({"type": "image_url",
                        "image_url": {"url": f"data:{mime};base64,{b64}", "detail": detail}})
    return [{"role": "user", "content": content}]


def fetch_catalogue() -> dict[str, dict[str, Any]]:
    """Live model list, used to price the panel and to check capabilities."""
    data = requests.get(MODELS_URL, timeout=60).json()["data"]
    return {m["id"]: m for m in data}


def build_panel(entries: list[tuple[str, str, str | None]]) -> list[ModelSpec]:
    """Price a panel from the live catalogue: (label, model id, provider)."""
    cat = fetch_catalogue()
    panel: list[ModelSpec] = []
    for label, model, provider in entries:
        meta = cat.get(model)
        if meta is None:
            raise ValueError(f"model {model!r} is not in the OpenRouter catalogue")
        pricing = meta.get("pricing", {})
        sp = meta.get("supported_parameters", [])
        mods = meta.get("architecture", {}).get("input_modalities", [])
        if "image" not in mods:
            raise ValueError(f"model {model!r} cannot take images, so it cannot read a page")
        panel.append(ModelSpec(
            name=label, model=model, provider=provider,
            price_in=float(pricing.get("prompt", 0)) * 1e6,
            price_out=float(pricing.get("completion", 0)) * 1e6,
            supports_structured="structured_outputs" in sp,
            supports_tools="tools" in sp,
            supports_seed="seed" in sp,
            notes=meta.get("name", "")))
    return panel
