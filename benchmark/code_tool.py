"""A model that may run Python: the strongest form of "the model decides".

The comparison this exists for: if a model that can compute does as well as a state
machine with rules, the state machine adds nothing. So the model here is given a real
interpreter, its own transcription as data, the page images, and an explicit brief. It
decides what to compute, reads the output, and gives the verdict itself.

The interpreter is a subprocess with a time limit, a memory limit and an empty
environment. Code is rejected before it runs if it imports anything outside a short
list of arithmetic and text modules, or names a file, process or network facility.
"""

from __future__ import annotations

import ast
import json
import subprocess
import sys
import tempfile
from typing import Any

ALLOWED_IMPORTS = {"json", "math", "decimal", "fractions", "re", "collections",
                   "itertools", "statistics", "datetime", "functools", "operator"}
FORBIDDEN_NAMES = {"open", "exec", "eval", "compile", "__import__", "input", "breakpoint",
                   "globals", "locals", "vars", "getattr", "setattr", "delattr", "sys",
                   "os", "subprocess", "builtins", "__builtins__"}
#: Attribute names that reach out of the arithmetic modules (``collections._sys``,
#: ``re.sys``, ``json.codecs.open``). Underscore-prefixed names are refused as well.
FORBIDDEN_ATTRIBUTES = {"sys", "os", "io", "builtins", "modules", "open", "codecs",
                        "subprocess", "importlib", "pathlib", "shutil", "socket",
                        "environ", "system", "popen", "loader", "spec"}
MAX_STEPS = 6
MAX_OUTPUT = 6000

TOOL = [{
    "type": "function",
    "function": {
        "name": "run_python",
        "description": ("Run Python 3 and get back what it prints. The variable `data` "
                        "holds the transcription as a Python object. Only the standard "
                        "arithmetic and text modules are available. Print what you want "
                        "to see."),
        "parameters": {"type": "object", "required": ["code"],
                       "properties": {"code": {"type": "string"}}},
    },
}]


def vet(code: str) -> str | None:
    """Why this code may not run, or None."""
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return f"SyntaxError: {exc}"
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] not in ALLOWED_IMPORTS:
                    return f"import of {alias.name!r} is not available"
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] not in ALLOWED_IMPORTS:
                return f"import from {node.module!r} is not available"
        elif isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
            return f"{node.id} is not available"
        elif isinstance(node, ast.Attribute) and (
                node.attr.startswith("_") or node.attr in FORBIDDEN_ATTRIBUTES):
            return f"attribute {node.attr!r} is not available"
    return None


_RUNNER = r'''
import json as _json, sys as _sys, builtins as _b
try:
    import resource as _r
    _r.setrlimit(_r.RLIMIT_AS, (1 << 30, 1 << 30))
    _r.setrlimit(_r.RLIMIT_CPU, (10, 10))
except Exception:
    pass
_payload = _json.loads(_sys.stdin.read())
_allowed = set(_payload["allowed"])
_real_import = _b.__import__
def _import(name, globals=None, locals=None, fromlist=(), level=0,
            _real=_real_import, _ok=_allowed):
    if level or name.split(".")[0] not in _ok:
        raise ImportError("import of %r is not available" % name)
    return _real(name, globals, locals, fromlist, level)
_names = ("abs all any bool dict divmod enumerate filter float frozenset int isinstance "
          "len list map max min pow print range repr reversed round set sorted str sum "
          "tuple zip Exception ValueError TypeError KeyError IndexError ZeroDivisionError "
          "True False None").split()
_safe = {n: getattr(_b, n) for n in _names if hasattr(_b, n)}
_safe["__import__"] = _import
_code = compile(_payload["code"], "<model>", "exec")
del _json, _sys, _b, _real_import
exec(_code, {"__builtins__": _safe, "data": _payload["data"]})
'''


def run_python(code: str, data: Any, timeout: float = 10.0) -> str:
    """Run vetted code with ``data`` bound, and return what it printed.

    Two layers. The code is vetted statically (``vet``). It is then executed in a
    separate process, with a namespace whose builtins are a short list of arithmetic
    and container functions and an import hook that admits only ``ALLOWED_IMPORTS``;
    nothing else, ``sys`` included, is in scope. The process has a time limit, a memory
    limit, an empty environment and a throwaway working directory. This is containment
    for a cooperative model, not a security boundary against a hostile one.
    """
    problem = vet(code)
    if problem:
        return f"[not run] {problem}"
    payload = json.dumps({"code": code, "data": data, "allowed": sorted(ALLOWED_IMPORTS)})
    with tempfile.TemporaryDirectory(prefix="probity-tool-") as work:
        try:
            done = subprocess.run([sys.executable, "-I", "-S", "-c", _RUNNER],
                                  input=payload, capture_output=True, text=True,
                                  timeout=timeout, cwd=work, env={})
        except subprocess.TimeoutExpired:
            return "[timed out after 10 seconds]"
    out = (done.stdout or "") + (("\n[stderr]\n" + done.stderr[-1500:]) if done.stderr else "")
    out = out.strip() or "[no output; print what you want to see]"
    return out[:MAX_OUTPUT] + ("\n[output truncated]" if len(out) > MAX_OUTPUT else "")


def converse(client, model, prompt: str, images: list[str], data: Any, *,
             answer_schema: dict[str, Any], purpose: str,
             max_tokens: int = 32000) -> tuple[str | None, float, int, str]:
    """Let the model call the interpreter until it answers.

    Returns (final text or None, cost, interpreter calls made, why there is no answer).
    The final answer is requested as JSON once the model stops calling the tool, or
    when the step limit is reached.
    """
    from probity.openrouter import image_message

    messages = image_message(prompt, images)
    cost, calls = 0.0, 0
    for step in range(MAX_STEPS):
        resp = client.chat(model, messages, tools=TOOL, max_tokens=max_tokens,
                           purpose=f"{purpose}:step{step}")
        cost += resp.cost_usd
        if (resp.finish_reason or "").lower() in {"length", "max_tokens", "error"}:
            return None, cost, calls, f"reply ended with {resp.finish_reason}"
        if not resp.tool_calls:
            messages.append({"role": "assistant", "content": resp.text or ""})
            break
        messages.append({"role": "assistant", "content": resp.text or "",
                         "tool_calls": resp.tool_calls})
        for call in resp.tool_calls:
            try:
                args = json.loads(call["function"]["arguments"])
                code = args.get("code", "") if isinstance(args, dict) else ""
            except (json.JSONDecodeError, KeyError, TypeError):
                code = ""
            if not isinstance(code, str) or not code:
                output = "[no code was supplied: pass {\"code\": \"...\"}]"
            elif calls >= MAX_STEPS:
                output = "[not run: you have used all six interpreter calls]"
            else:
                calls += 1
                output = run_python(code, data)
            messages.append({"role": "tool",
                             "tool_call_id": call.get("id", "") if isinstance(call, dict) else "",
                             "content": output})
    else:
        messages.append({"role": "user", "content": "You have used all your interpreter "
                         "calls. Give your final answer now."})
    messages.append({"role": "user", "content":
                     "Give your final answer now, as a single JSON object."})
    final = client.chat(model, messages, json_schema=answer_schema, max_tokens=max_tokens,
                        purpose=f"{purpose}:answer")
    cost += final.cost_usd
    if (final.finish_reason or "").lower() in {"length", "max_tokens", "error"}:
        return None, cost, calls, f"reply ended with {final.finish_reason}"
    return final.text, cost, calls, ""
