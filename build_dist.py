#!/usr/bin/env python3
"""Build dist/caffeine-tracker-v<version>.zip under SP's 100k ceiling.

Super Productivity enforces the ~100KB plugin size limit on the
*uncompressed* files, so the zip must contain a minified index.html.
The repo source stays readable; only the packaged copy is minified.

Minification is whitespace-only outside of JS strings/template literals
and comments (tracked with a small tokenizer), so semantics can't change:
  - HTML/CSS: strip each line, drop blank lines.
  - JS: drop leading/trailing whitespace per line and blank lines,
    emitting JS strings, template literals and comments verbatim.

Usage: python3 build_dist.py
"""
import json
import re
import zipfile

SRC_FILES = ["icon.svg", "index.html", "manifest.json", "plugin.js", "README.md"]
SIZE_CEILING = 100_000


def minify_html_css(segment):
    out = []
    for line in segment.split("\n"):
        s = line.strip()
        if s:
            out.append(s)
    return "\n".join(out)


def minify_js(js):
    out = []
    # stack frames: ('code', interp, braces) | ('sq',) | ('dq',) | ('tpl',) | ('lc',) | ('bc',)
    stack = [("code", False, 0)]
    pending_space = []
    line_has_content = True  # BOS counts as already-started (keeps doctype-adjacent logic simple)
    first_char = True

    def state():
        return stack[-1][0]

    i, n = 0, len(js)
    while i < n:
        c = js[i]
        nxt = js[i + 1] if i + 1 < n else ""
        st = state()

        if st == "code":
            if c == "/" and nxt == "/":
                stack.append(("lc",))
                out.append("//")
                i += 2
                line_has_content = True
                continue
            if c == "/" and nxt == "*":
                stack.append(("bc",))
                out.append("/*")
                i += 2
                line_has_content = True
                continue
            if c == "/" and nxt not in ("/", "*"):
                # regex literal vs division: a '/' starts a regex only after
                # these tokens (covers every regex site in this codebase,
                # which all follow '(' or '!'; divisions follow ')', names
                # or numbers).
                prev = next((ch for ch in reversed(out) if ch not in " \t\n"), "")
                if prev in "(,=:[!&|?{};":
                    j = i + 1
                    in_class = False
                    while j < n:
                        d = js[j]
                        if d == "\\":
                            j += 2
                            continue
                        if d == "[":
                            in_class = True
                        elif d == "]":
                            in_class = False
                        elif d == "/" and not in_class:
                            break
                        elif d == "\n":
                            break
                        j += 1
                    k = j + 1
                    while k < n and js[k] in "abcdefghijklmnopqrstuvwxyz":
                        k += 1
                    assert j < n and js[j] == "/", f"unterminated regex near line {js.count(chr(10), 0, i) + 1}"
                    out.append(js[i:k])
                    line_has_content = True
                    i = k
                    continue
            if c in ("'", '"', "`"):
                stack.append(({"'": "sq", '"': "dq", "`": "tpl"}[c],))
                out.append(c)
                line_has_content = True
                i += 1
                continue
            if c == "{":
                frame = stack[-1]
                if frame[1]:  # inside ${...}: track brace depth
                    stack[-1] = ("code", True, frame[2] + 1)
                else:
                    stack.append(("code", False, 0))
                out.append(c)
                line_has_content = True
                i += 1
                continue
            if c == "}":
                frame = stack[-1]
                if frame[1]:
                    if frame[2] == 0:
                        stack.pop()  # closes ${...}, back to tpl
                    else:
                        stack[-1] = ("code", True, frame[2] - 1)
                elif len(stack) > 1:
                    stack.pop()
                out.append(c)
                line_has_content = True
                i += 1
                continue
            if c in (" ", "\t"):
                pending_space.append(c)
                i += 1
                continue
            if c == "\n":
                pending_space = []
                if line_has_content:
                    out.append("\n")
                line_has_content = False
                i += 1
                continue
            if pending_space:
                if line_has_content:
                    out.extend(pending_space)
                pending_space = []
            out.append(c)
            line_has_content = True
            i += 1
        elif st == "lc":
            out.append(c)
            if c == "\n":
                stack.pop()
                line_has_content = False
            i += 1
        elif st == "bc":
            out.append(c)
            if c == "*" and nxt == "/":
                out.append("/")
                stack.pop()
                i += 2
            else:
                i += 1
        else:  # sq, dq, tpl: verbatim, honour escapes and ${...} nesting
            out.append(c)
            if c == "\\":
                if nxt:
                    out.append(nxt)
                    i += 1
            elif st == "sq" and c == "'":
                stack.pop()
            elif st == "dq" and c == '"':
                stack.pop()
            elif st == "tpl" and c == "`":
                stack.pop()
            elif st == "tpl" and c == "$" and nxt == "{":
                out.append("{")
                stack.append(("code", True, 0))
                i += 1
            i += 1

    result = "".join(out)
    assert stack == [("code", False, 0)], f"unbalanced tokenizer state: {stack}"
    return result


def main():
    html = open("index.html").read()
    assert html.count("<style>") == 1 and html.count("<script>") == 1
    head, rest = html.split("<style>")
    css, rest = rest.split("</style>", 1)
    mid, js_and_tail = rest.split("<script>", 1)
    js, tail = js_and_tail.split("</script>", 1)

    min_html = (
        minify_html_css(head)
        + "<style>"
        + minify_html_css(css)
        + "</style>"
        + minify_html_css(mid)
        + "<script>"
        + minify_js(js)
        + "</script>"
        + minify_html_css(tail)
    )
    print(f"index.html {len(html)} -> {len(min_html)} bytes")

    with open("manifest.json") as f:
        version = json.load(f)["version"]
    zip_path = f"dist/caffeine-tracker-v{version}.zip"
    payload = {
        "icon.svg": open("icon.svg").read(),
        "index.html": min_html,
        "manifest.json": open("manifest.json").read(),
        "plugin.js": open("plugin.js").read(),
        "README.md": open("README.md").read(),
    }
    total = sum(len(v.encode("utf-8")) for v in payload.values())
    print(f"uncompressed total: {total} bytes (ceiling {SIZE_CEILING})")
    assert total < SIZE_CEILING, "still over the size ceiling!"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in payload.items():
            z.writestr(name, data)
    print(f"wrote {zip_path}")


if __name__ == "__main__":
    main()
