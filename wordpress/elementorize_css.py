"""One-off conversion of castore-site.css so Elementor's own controls win over it.

- Design tokens read Elementor's Global Colors / Global Fonts first (Site Settings),
  falling back to the original values. Tokens are declared on `:root, body` because
  Elementor defines its globals on the body (.elementor-kit-N).
- Container layout (padding, gap, direction, wrap, alignment, sizing) is written as the
  CSS variables Elementor's containers read, at a specificity below Elementor's
  per-element rules, so a change in the Elementor panel overrides the default here.
- Font files are referenced by absolute path, because the CSS moves into
  Site Settings > Custom CSS (served from uploads/elementor/css/).

Usage: python3 elementorize_css.py castore-site.css > castore-site.css.new
"""
import re
import sys

COLORS = {
    "--color-ground": "cground", "--color-surface": "csurface", "--color-surface-alt": "csurfacealt",
    "--color-tint": "ctint", "--color-border": "cborder", "--color-ink": "cink", "--color-muted": "cmuted",
    "--color-accent": "caccent", "--color-accent-dark": "caccentdark", "--color-deep": "cdeep",
    "--color-whatsapp": "cwhatsapp",
}
SIZES = {
    "--text-hero": "chero", "--text-section": "csection", "--text-2xl": "ccard", "--text-lg": "clead",
    "--text-md": "cbody", "--text-base": "cbutton", "--text-sm": "csmall",
}
FONTS = {"--font-display": ("cheadings", '"Georgia", serif'), "--font-body": ("cbody", '"Helvetica Neue", sans-serif')}

DIRECT_TO_VAR = {
    "flex-direction": "--flex-direction", "flex-wrap": "--flex-wrap", "align-items": "--align-items",
    "justify-content": "--justify-content", "align-content": "--align-content", "align-self": "--align-self",
    "order": "--order", "flex-grow": "--flex-grow", "flex-shrink": "--flex-shrink", "flex-basis": "--flex-basis",
    "width": "--width", "height": "--height", "min-height": "--min-height", "border-radius": "--border-radius",
    "overflow": "--overflow", "padding-top": "--padding-top", "padding-right": "--padding-right",
    "padding-bottom": "--padding-bottom", "padding-left": "--padding-left", "margin-top": "--margin-top",
    "margin-right": "--margin-right", "margin-bottom": "--margin-bottom", "margin-left": "--margin-left",
}
WIDGET_VARS = {"flex-grow", "flex-shrink", "flex-basis", "align-self", "order"}


def split_top(value, sep=None):
    """Split on whitespace (or sep) outside parentheses."""
    out, depth, cur = [], 0, ""
    for ch in value:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if depth == 0 and ((sep is None and ch.isspace()) or ch == sep):
            if cur.strip():
                out.append(cur.strip())
            cur = ""
            continue
        cur += ch
    if cur.strip():
        out.append(cur.strip())
    return out


def box(values):
    v = values
    if len(v) == 1:
        return v * 4
    if len(v) == 2:
        return [v[0], v[1], v[0], v[1]]
    if len(v) == 3:
        return [v[0], v[1], v[2], v[1]]
    return v[:4]


def layout_decls(prop, value, is_container):
    """Return a list of (prop, value) replacing one declaration, or None to keep it."""
    if prop == "flex":
        parts = split_top(value)
        if len(parts) == 3:
            basis = "0px" if parts[2] == "0" else parts[2]
            return [("--flex-grow", parts[0]), ("--flex-shrink", parts[1]), ("--flex-basis", basis)]
        return None
    if not is_container:
        return [(DIRECT_TO_VAR[prop], value)] if prop in WIDGET_VARS else None
    if prop == "padding":
        t, r, b, l = box(split_top(value))
        return [("--padding-top", t), ("--padding-right", r), ("--padding-bottom", b), ("--padding-left", l)]
    if prop == "gap":
        parts = split_top(value)
        row, col = parts[0], parts[-1]
        return [("--gap", row), ("--row-gap", row), ("--column-gap", col)]
    if prop in DIRECT_TO_VAR:
        return [(DIRECT_TO_VAR[prop], value)]
    return None


def last_compound(sel):
    return re.split(r"\s+|>|\+|~", sel.strip())[-1]


def convert_rule(selectors, body):
    sels = [s.strip() for s in split_top(selectors, ",")]
    containers = all(".e-con" in last_compound(s) for s in sels)
    widgets = all(re.fullmatch(r"\.[a-z][a-z0-9-]*", last_compound(s)) and s.startswith(".elementor ") for s in sels)
    if not (containers or widgets):
        return selectors, body
    decls = [d for d in split_top(body, ";")]
    new = []
    for d in decls:
        if ":" not in d:
            continue
        prop, value = d.split(":", 1)
        prop, value = prop.strip(), value.strip()
        repl = layout_decls(prop, value, containers)
        new.extend(repl if repl else [(prop, value)])
    # Below Elementor's per-element rules (0,3,0), above its base container rules (0,2,0).
    out_sels = []
    for sel in sels:
        if containers:
            sel = re.sub(r"^\.elementor\s+", "", sel)
            if not re.search(r"[\s>+~]", sel):
                sel = "html " + sel
        out_sels.append(sel)
    return ", ".join(out_sels), " " + "; ".join(f"{p}: {v}" for p, v in new) + "; "


def convert_tokens(body):
    decls = split_top(body, ";")
    out = []
    for d in decls:
        if ":" not in d:
            continue
        prop, value = [x.strip() for x in d.split(":", 1)]
        if prop in COLORS:
            value = f"var(--e-global-color-{COLORS[prop]}, {value})"
        elif prop in SIZES:
            value = f"var(--e-global-typography-{SIZES[prop]}-font-size, {value})"
        elif prop in FONTS:
            gid, fallback = FONTS[prop]
            first = split_top(value, ",")[0]
            value = f"var(--e-global-typography-{gid}-font-family, {first}), {fallback}"
        out.append(f"{prop}: {value}")
    return "\n  " + ";\n  ".join(out) + ";\n"


def transform(css):
    css = css.replace('url("fonts/', 'url("/wp-content/uploads/castore/fonts/')
    result = []
    pattern = re.compile(r"([^{}]+)\{([^{}]*)\}")
    # Walk rules, keeping @media / @font-face wrappers intact.
    pos = 0
    for m in pattern.finditer(css):
        result.append(css[pos:m.start()])
        sel, body = m.group(1), m.group(2)
        prefix = sel[: len(sel) - len(sel.lstrip())]
        s = sel.strip()
        if s.startswith("@font-face"):
            result.append(m.group(0))
        elif s.endswith(":root") or s == ":root":
            # Font sizes and families now come from Global Fonts; drop responsive overrides for them.
            if css[:m.start()].count("{") > css[:m.start()].count("}"):
                body = ";".join(d for d in split_top(body, ";") if d.split(":", 1)[0].strip() not in SIZES) + ";"
            result.append(f"{prefix}:root, body {{{convert_tokens(body)}}}")
        else:
            lead = s.split("\n")[-1]
            head = s[: len(s) - len(lead)]
            new_sel, new_body = convert_rule(lead, body)
            result.append(f"{prefix}{head}{new_sel} {{{new_body}}}")
        pos = m.end()
    result.append(css[pos:])
    return "".join(result)


if __name__ == "__main__":
    sys.stdout.write(transform(open(sys.argv[1]).read()))
