#!/usr/bin/env python3
"""Build the 0x0128 profile images from brand.json.

    python3 scripts/build.py

Python 3.8+ only, nothing to install. Every image is written twice, once for
GitHub's dark theme and once for the light one.
"""
import json
import math
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
B = json.loads((ROOT / "brand.json").read_text(encoding="utf-8"))
THEMES = B["themes"]
MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"
SANS = "ui-sans-serif,-apple-system,'Segoe UI',Helvetica,Arial,sans-serif"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text(x, y, s, fill, size=13, weight=None, anchor=None, extra=""):
    a = f' text-anchor="{anchor}"' if anchor else ""
    w = f' font-weight="{weight}"' if weight else ""
    return f'<text x="{x}" y="{y}" fill="{fill}" font-size="{size}"{w}{a}{extra}>{esc(s)}</text>'


def svg_open(w, h, title, desc, font=MONO):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'role="img" aria-labelledby="t d" font-family="{font}">'
            f'<title id="t">{esc(title)}</title><desc id="d">{esc(desc)}</desc>')


# --------------------------------------------------------------------------
# The logo, read from assets/logo so there is a single source for its shape.
# Coordinates live in a 240 x 240 box (the owl spans x 40..200, y 20..222).
# --------------------------------------------------------------------------

LOGO_D = re.search(r' d="([^"]+)"', (ASSETS / "logo" / "0x0128-logo-negro.svg").read_text()).group(1)


def _polygons(d):
    polys = []
    for sub in d.strip().split("Z"):
        nums = re.findall(r"-?\d+(?:\.\d+)?", sub)
        if len(nums) >= 6:
            pts = [(float(nums[i]), float(nums[i + 1])) for i in range(0, len(nums) - 1, 2)]
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            polys.append((min(xs), min(ys), max(xs), max(ys), pts))
    return polys


LOGO_POLYS = _polygons(LOGO_D)


def in_logo(x, y):
    inside = False
    for x0, y0, x1, y1, pts in LOGO_POLYS:
        if not (x0 <= x <= x1 and y0 <= y <= y1):
            continue
        n = len(pts)
        for i in range(n):
            (ax, ay), (bx, by) = pts[i], pts[(i + 1) % n]
            if (ay > y) != (by > y) and x < (bx - ax) * (y - ay) / (by - ay) + ax:
                inside = not inside
    return inside


def _bez(p0, c1, c2, p1, n=16):
    return [((1 - t) ** 3 * p0[0] + 3 * (1 - t) ** 2 * t * c1[0] + 3 * (1 - t) * t * t * c2[0] + t ** 3 * p1[0],
             (1 - t) ** 3 * p0[1] + 3 * (1 - t) ** 2 * t * c1[1] + 3 * (1 - t) * t * t * c2[1] + t ** 3 * p1[1])
            for t in (i / n for i in range(1, n + 1))]


SHIELD = [(40, 20), (120, 72), (200, 20), (200, 140)]
SHIELD += _bez((200, 140), (200, 182), (164, 206), (120, 222))
SHIELD += _bez((120, 222), (76, 206), (40, 182), (40, 140))


def in_poly(x, y, pts):
    inside, n = False, len(pts)
    for i in range(n):
        (ax, ay), (bx, by) = pts[i], pts[(i + 1) % n]
        if (ay > y) != (by > y) and x < (bx - ax) * (y - ay) / (by - ay) + ax:
            inside = not inside
    return inside


def logo_svg(x, y, size, fill):
    """The owl drawn at (x, y), `size` px tall."""
    s = size / 204
    return (f'<path transform="translate({x} {y}) scale({s:.4f}) translate(-18 -18)" '
            f'fill="{fill}" fill-rule="evenodd" d="{LOGO_D}"/>')


# --------------------------------------------------------------------------
# Banner: a vim window. Left, a stippled picture that dissolves from the owl
# into a loupe, a neural network and a padlock. Right, profile.yml.
# --------------------------------------------------------------------------

CW, CH, STEP = 300, 340, 2


def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def shape_owl(x, y):
    ox, oy = (x - 30) / 1.5 + 40, (y - 18) / 1.5 + 20
    if in_logo(ox, oy):
        return 0.92
    if min(math.hypot(ox - ex, oy - 106) for ex in (83.1, 156.9)) < 31:
        return 0  # keep the eyes clean
    return 0.07 if in_poly(ox, oy, SHIELD) else 0


def shape_loupe(x, y):
    cx, cy, R = 124, 136, 84
    d = math.hypot(x - cx, y - cy)
    if abs(d - R) <= 8:
        return 0.92
    if d > R and seg_dist(x, y, 190.5, 202.5, 264, 276) <= 13:
        return 0.92
    if d < R - 8:
        return 0.3 if math.hypot(x - (cx - 30), y - (cy - 30)) < 22 else 0.06
    return 0


_L = [(52, 90), (52, 170), (52, 250)]
_M = [(150, 62), (150, 134), (150, 206), (150, 278)]
_R = [(248, 130), (248, 210)]
_EDGES = [(a, b) for a in _L for b in _M] + [(a, b) for a in _M for b in _R]


def shape_graph(x, y):
    for nx, ny in _L + _M + _R:
        if math.hypot(x - nx, y - ny) <= 16:
            return 0.92
    for (ax, ay), (bx, by) in _EDGES:
        if seg_dist(x, y, ax, ay, bx, by) <= 1.5:
            return 0.42
    return 0


def shape_padlock(x, y):
    cx = 150
    # keyhole
    if math.hypot(x - cx, y - 214) <= 17 or (abs(x - cx) <= 7 + (y - 214) * 0.1 and 214 <= y <= 254):
        return 0
    if 66 <= x <= 234 and 150 <= y <= 306:
        return 0.92
    # shackle
    d = math.hypot(x - cx, y - 110)
    if y <= 110 and 46 <= d <= 64:
        return 0.92
    if 110 < y < 150 and (86 <= x <= 104 or 196 <= x <= 214):
        return 0.92
    return 0


def sample(shape, seed, groups=14):
    rng = random.Random(seed)
    out = {}
    for j in range(CH // STEP):
        for i in range(CW // STEP):
            p = shape(i * STEP + 1, j * STEP + 1)
            if p and rng.random() < p:
                main = p >= 0.8 and rng.random() > 0.12
                out.setdefault(("dot" if main else "dot2", rng.randrange(groups)), []).append((i * STEP, j * STEP))
    return out


_SAMPLES = {}


def cloud(T, ox, oy, cycle=22.0):
    shapes = [(shape_owl, 0.0, 8.0), (shape_loupe, 9.2, 12.6), (shape_graph, 13.8, 17.2), (shape_padlock, 18.4, 20.8)]
    tau, css, body, total = 1.2, [], [], 0
    pc = lambda t: f"{100 * t / cycle:.2f}%"
    for k, (fn, a, b) in enumerate(shapes):
        away_in = "transform:translate(var(--ax),var(--ay));opacity:0"
        away_out = "transform:translate(var(--bx),var(--by));opacity:0"
        here = "transform:translate(0,0);opacity:.95"
        if k == 0:
            css.append(f"@keyframes s0{{0%,{pc(b)}{{{here}}}{pc(b + tau)}{{{away_out}}}"
                       f"{pc(b + tau + 0.01)},{pc(cycle - tau)}{{{away_in}}}100%{{{here}}}}}")
        else:
            css.append(f"@keyframes s{k}{{0%,{pc(a - tau)}{{{away_in}}}{pc(a)},{pc(b)}{{{here}}}"
                       f"{pc(b + tau)},100%{{{away_out}}}}}")
        css.append(f".s{k}{{animation:s{k} {cycle}s linear infinite}}")
        rng = random.Random(100 + k)
        if fn not in _SAMPLES:
            _SAMPLES[fn] = sample(fn, seed=k + 1)
        for (color, _), pts in sorted(_SAMPLES[fn].items()):
            total += len(pts)
            d = "".join(f"M{x} {y}h2" for x, y in pts)
            ax, ay, bx, by = (round(rng.uniform(-9, 9), 1) for _ in range(4))
            body.append(f'<path class="s{k}" style="--ax:{ax}px;--ay:{ay}px;--bx:{bx}px;--by:{by}px" '
                        f'opacity="{0.95 if k == 0 else 0}" stroke="{T[color]}" d="{d}"/>')
    g = f'<g transform="translate({ox},{oy + 1})" fill="none" stroke-width="2">{"".join(body)}</g>'
    return "".join(css), g, total


def yaml_line(T, line, y, n):
    num = text(506, y, f"{n:>2}", T["muted"], 13, anchor="end", extra=' opacity=".45"')
    if not line.startswith(" "):
        return num + text(525, y, line, T["key"], 13, weight=700)
    key, _, val = line.strip().partition(":")
    return num + (f'<text x="542" y="{y}" font-size="13" xml:space="preserve">'
                  f'<tspan fill="{T["sub"]}">{esc(key)}:</tspan><tspan fill="{T["text"]}">{esc(val)}</tspan></text>')


def build_banner(mode):
    T = THEMES[mode]
    W, H, cycle = 1180, 610, 22.0
    lines = B["banner"]["yaml"]
    css, cloud_g, npts = cloud(T, 94, 154, cycle)
    nbytes = len("\n".join(lines).encode()) + 1
    css += ("@keyframes rise{from{opacity:0}to{opacity:1}}.ln{animation:rise .4s both}"
            "@media (prefers-reduced-motion:reduce){*{animation:none!important}}")
    o = [svg_open(W, H, f"{B['handle']}: {B['name']}, {B['role']}",
                  "A vim window. On the left the 0x0128 owl-shield drawn as a point cloud that turns into a "
                  "loupe, a neural network and a padlock; on the right profile.yml."),
         f"<style>{css}</style>",
         f'<rect width="{W}" height="{H}" rx="18" fill="{T["bg"]}"/>',
         f'<rect x="13" y="13" width="1154" height="584" rx="13" fill="{T["win"]}" stroke="{T["rule"]}"/>',
         f'<path d="M13 62H1167" stroke="{T["rule"]}"/>',
         f'<circle cx="38" cy="38" r="6" fill="{T["muted"]}"/><circle cx="59" cy="38" r="6" fill="{T["muted"]}" opacity=".6"/>'
         f'<circle cx="80" cy="38" r="6" fill="{T["muted"]}" opacity=".3"/>',
         text(590, 43, "vim profile.yml", T["muted"], 13, anchor="middle", extra=' letter-spacing=".4"'),
         # left panel
         f'<rect x="35" y="88" width="418" height="472" rx="6" fill="{T["panel"]}" stroke="{T["rule"]}"/>',
         f'<path d="M35 124H453" stroke="{T["rule"]}"/>',
         text(49, 111, "VISUAL.MAP", T["key"], 13, weight=700, extra=' letter-spacing="1.2"'),
         text(438, 111, "300×340 / 1-BIT", T["muted"], 11, anchor="end"),
         f'<path d="M49 141h12M49 141v12M439 141h-12M439 141v12M49 539h12M49 539v-12M439 539h-12M439 539v-12" '
         f'fill="none" stroke="{T["muted"]}" opacity=".55"/>',
         cloud_g,
         text(58, 551, f"PTS {npts} · OWL/SHIELD", T["muted"], 10),
         # right panel
         f'<rect x="474" y="88" width="672" height="472" rx="6" fill="{T["panel"]}" stroke="{T["rule"]}"/>',
         f'<path d="M474 124H1146" stroke="{T["rule"]}"/>',
         text(490, 111, "profile.yml", T["key"], 13, weight=700, extra=' letter-spacing=".5"'),
         text(592, 111, "[YAML]", T["muted"], 11),
         f'<rect x="995" y="96" width="133" height="24" rx="12" fill="{T["rule"]}"/>',
         text(1062, 112, f"@{B['handle']}", T["key"], 13, weight=700, anchor="middle")]
    for i, line in enumerate(lines):
        o.append(f'<g class="ln" style="animation-delay:{0.25 + i * 0.07:.2f}s">'
                 + yaml_line(T, line, round(148 + i * 21.5, 1), i + 1) + "</g>")
    o += [f'<path d="M474 526H1146" stroke="{T["rule"]}"/>',
          f'<rect x="485" y="533" width="72" height="20" rx="3" fill="{T["badge"]}"/>',
          text(521, 547, "NORMAL", T["badge_text"], 11, weight=700, anchor="middle"),
          text(569, 547, "profile.yml", T["text"], 12, weight=600),
          text(740, 547, "[utf-8]", T["muted"], 11),
          text(1134, 547, f"{len(lines)}L, {nbytes}B  100%  {len(lines)}:1", T["muted"], 11, anchor="end"),
          "</svg>"]
    (ASSETS / f"banner-{mode}.svg").write_text("".join(o), encoding="utf-8")
    return npts


# --------------------------------------------------------------------------
# whoami card
# --------------------------------------------------------------------------

def build_whoami(mode):
    T = THEMES[mode]
    w = B["whoami"]
    W, H = 960, 390
    o = [svg_open(W, H, f"{B['name']}: {w['role']}",
                  f"Terminal card: {w['role']}, based in {w['context']}. "
                  + " ".join(f"{k.strip('/')}: {v}." for k, v in w["expertise"])),
         f'<rect width="{W}" height="{H}" rx="18" fill="{T["win"]}"/>',
         f'<rect x="9" y="9" width="942" height="372" rx="13" fill="none" stroke="{T["rule"]}" stroke-width="2"/>',
         f'<circle cx="35" cy="35" r="5" fill="{T["muted"]}"/><circle cx="54" cy="35" r="5" fill="{T["muted"]}" opacity=".6"/>'
         f'<circle cx="73" cy="35" r="5" fill="{T["muted"]}" opacity=".3"/>',
         text(98, 41, f"{B['handle']}  ·  profile shell  ·  online", T["muted"], 15),
         f'<path d="M29 58H931" stroke="{T["rule"]}"/>',
         f'<rect x="29" y="78" width="594" height="271" rx="9" fill="{T["panel"]}" stroke="{T["rule"]}" stroke-width="1.5"/>',
         text(48, 111, "❯ whoami", T["key"], 20, weight=700),
         text(48, 143, w["who"], T["text"], 18, weight=700),
         text(48 + len(w["who"]) * 10.8 + 12, 143, "—", T["muted"], 18),
         text(48 + len(w["who"]) * 10.8 + 37, 143, w["role"], T["sub"], 18),
         f'<path d="M48 166H604" stroke="{T["rule"]}"/>',
         text(48, 196, "context:", T["muted"], 17), text(166, 196, w["context"], T["text"], 17)]
    if w.get("mission"):
        o += [text(48, 225, "mission:", T["muted"], 17), text(166, 225, w["mission"], T["text"], 17)]
    top = 267 if w.get("mission") else 245
    o.append(text(48, top, "❯ ls focus/", T["key"], 20, weight=700))
    y = top + 34
    vx = 48 + (max(len(k) for k, _ in w["expertise"]) + 2) * 9.7
    for k, v in w["expertise"]:
        o += [text(48, y, k, T["sub"], 16, weight=700), text(round(vx), y, v, T["text"], 16)]
        y += 29
    o += [f'<rect x="651" y="78" width="280" height="271" rx="9" fill="{T["panel"]}" stroke="{T["rule"]}" stroke-width="1.5"/>',
          text(674, 111, w["art_title"], T["key"], 17, weight=700),
          logo_svg(791 - 80, 132, 160, T["key"]),
          text(674, 330, w["art_status"], T["muted"], 14),
          "</svg>"]
    (ASSETS / f"whoami-{mode}.svg").write_text("".join(o), encoding="utf-8")


# --------------------------------------------------------------------------
# Skill radar
# --------------------------------------------------------------------------

def build_radar(mode):
    """Radar whose values drift inside each axis's [low, high] range, so no score is fixed."""
    T = THEMES[mode]
    R = B["radar"]
    axes = R["axes"]
    W, H, cx, cy, rad = 760, 526, 380.0, 289.0, 212
    n = len(axes)
    pt = lambda i, r: (r * math.sin(2 * math.pi * i / n), -r * math.cos(2 * math.pi * i / n))
    rng = random.Random(128)
    states = [[(lo + hi) / 2 for _, lo, hi in axes]]
    for _ in range(4):
        states.append([rng.uniform(lo, hi) for _, lo, hi in axes])
    states.append(states[0])
    frames = [[pt(i, rad * v / 100) for i, v in enumerate(st)] for st in states]
    dur, segs = 16, len(frames) - 1
    timing = (f'dur="{dur}s" repeatCount="indefinite" calcMode="spline" '
              f'keyTimes="{";".join(f"{k / segs:.3f}" for k in range(segs + 1))}" '
              f'keySplines="{";".join([".45 0 .55 1"] * segs)}"')
    o = [svg_open(W, H, R["title"], "Self-rated skill radar with values that move within a range: "
                  + "; ".join(f"{a}: {lo}-{hi}" for a, lo, hi in axes), font=SANS),
         "<style>@keyframes grow{from{transform:scale(.04)}to{transform:scale(1)}}"
         ".poly{animation:grow 1.1s cubic-bezier(.22,1,.36,1) both}"
         "@media (prefers-reduced-motion:reduce){.poly{animation:none}}</style>",
         text(W / 2, 25, R["title"], T["text"], 15, weight=700, anchor="middle"),
         f'<g transform="translate({cx},{cy})">']
    for k, op in ((1, .85), (.75, .72), (.5, .6), (.25, .47)):
        ring = " ".join(f"{x:.1f},{y:.1f}" for x, y in (pt(i, rad * k) for i in range(n)))
        o.append(f'<polygon points="{ring}" fill="none" stroke="{T["grid"]}" opacity="{op}"/>')
    for i in range(n):
        x, y = pt(i, rad)
        o.append(f'<line x1="0" y1="0" x2="{x:.1f}" y2="{y:.1f}" stroke="{T["grid"]}"/>')
    pts = lambda fr: " ".join(f"{x:.1f},{y:.1f}" for x, y in fr)
    o.append(f'<g class="poly"><polygon points="{pts(frames[0])}" fill="{T["key"]}" fill-opacity=".16" '
             f'stroke="{T["key"]}" stroke-width="2.5" stroke-linejoin="round">'
             f'<animate attributeName="points" values="{";".join(pts(fr) for fr in frames)}" {timing}/></polygon>')
    for i in range(n):
        xs = ";".join(f"{fr[i][0]:.1f}" for fr in frames)
        ys = ";".join(f"{fr[i][1]:.1f}" for fr in frames)
        x0, y0 = frames[0][i]
        o.append(f'<circle cx="{x0:.1f}" cy="{y0:.1f}" r="4" fill="{T["key"]}">'
                 f'<animate attributeName="cx" values="{xs}" {timing}/><animate attributeName="cy" values="{ys}" {timing}/></circle>')
    o.append("</g>")
    for i, (label, _, _) in enumerate(axes):
        x, y = pt(i, rad + 24)
        anchor = "middle" if abs(x) < 2 else ("start" if x > 0 else "end")
        dy = 4 if y > -2 else 0
        o.append(text(round(x, 1), round(y + dy, 1), label, T["sub"], 13, weight=600, anchor=anchor))
    o.append("</g></svg>")
    (ASSETS / f"radar-{mode}.svg").write_text("".join(o), encoding="utf-8")


# --------------------------------------------------------------------------
# Chips: labelled tiles for the things that have no logo.
# --------------------------------------------------------------------------

def build_chips(mode):
    T = THEMES[mode]
    out = ASSETS / "chips"
    out.mkdir(exist_ok=True)
    fs, cw, h, padx, gap, maxw = 13, 7.8, 30, 12, 8, 380
    for name, labels in B["chips"].items():
        x = y = 0
        placed = []
        for lab in labels:
            w = round(padx * 2 + 14 + len(lab) * cw)
            if x and x + w > maxw:
                x, y = 0, y + h + gap
            placed.append((x, y, w, lab))
            x += w + gap
        W = max(px + w for px, _, w, _ in placed)
        o = [svg_open(W, y + h, ", ".join(labels), "Skill chips.")]
        for px, py, w, lab in placed:
            o.append(f'<rect x="{px}" y="{py}" width="{w}" height="{h}" rx="6" fill="{T["chip"]}" stroke="{T["rule"]}"/>'
                     f'<rect x="{px + padx}" y="{py + 11}" width="8" height="8" fill="{T["key"]}"/>'
                     + text(px + padx + 14, py + 20, lab, T["chip_text"], fs, extra=f' textLength="{len(lab) * cw:.1f}"'))
        o.append("</svg>")
        (out / f"{name}-{mode}.svg").write_text("".join(o), encoding="utf-8")


# --------------------------------------------------------------------------
# Skills as bit rows: sixteen cells per row, one lit per point.
# --------------------------------------------------------------------------

def build_skills(mode):
    T = THEMES[mode]
    rows = B["skills"]["rows"]
    W, pad, rh, cell, gap = 960, 36, 34, 18, 6
    H = pad * 2 + len(rows) * rh + 22
    gx = 372
    o = [svg_open(W, H, "Skills, self-rated out of 16", "; ".join(f"{n}: {v} of 16" for n, v in rows)),
         f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="14" fill="{T["win"]}" stroke="{T["rule"]}"/>']
    y = pad
    for name, v in rows:
        o.append(text(gx - 28, y + 15, name, T["text"], 15, anchor="end"))
        cells = "".join(f"M{gx + i * (cell + gap)} {y}h{cell}v{cell}h-{cell}z" for i in range(v))
        off = "".join(f"M{gx + i * (cell + gap)} {y}h{cell}v{cell}h-{cell}z" for i in range(v, 16))
        o.append(f'<path fill="{T["key"]}" d="{cells}"/><path fill="{T["off"]}" d="{off}"/>')
        o.append(text(gx + 16 * (cell + gap) + 16, y + 15, f"{v:>2}/16", T["muted"], 14, extra=' xml:space="preserve"'))
        y += rh
    o.append(text(gx, y + 22, "self-rated, one bit per point", T["muted"], 13))
    o.append("</svg>")
    (ASSETS / f"skills-{mode}.svg").write_text("".join(o), encoding="utf-8")


# --------------------------------------------------------------------------
# Project header cards: the owl, the project name and one line.
# --------------------------------------------------------------------------

def build_cards(mode):
    T = THEMES[mode]
    out = ASSETS / "cards"
    out.mkdir(exist_ok=True)
    W, H = 1280, 320
    for p in B.get("projects", []):
        fs = min(104, int((W - 304 - 56) / (len(p["name"]) * 0.6)))
        o = [svg_open(W, H, f"{p['name']}: {p['tagline']}", f"Project header for {p['name']}, by {B['handle']}.", font=SANS),
             f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="14" fill="{T["win"]}" stroke="{T["rule"]}"/>',
             logo_svg(56, 55, 210, T["key"]),
             f'<path d="M262 72V248" stroke="{T["rule"]}" stroke-width="2"/>',
             text(304, 178, p["name"], T["key"], fs, weight=700, extra=' letter-spacing="-2"'),
             text(308, 232, p["tagline"], T["muted"], 30),
             "</svg>"]
        (out / f"{p['repo']}-header-{mode}.svg").write_text("".join(o), encoding="utf-8")


def main():
    n = 0
    for mode in THEMES:
        n = build_banner(mode)
        build_whoami(mode)
        if "radar" in B:
            build_radar(mode)
        build_chips(mode)
        if "skills" in B:
            build_skills(mode)
        build_cards(mode)
    print(f"built assets/ for {', '.join(THEMES)} ({n} points in the banner cloud)")


if __name__ == "__main__":
    main()
