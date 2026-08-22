#!/usr/bin/env python3
"""
generate_profile.py -- data layer for the ValiantZippu terminal profile.

Fetches live public GitHub data and renders AMOLED-black (#000000) SVG assets
into assets/generated/. Stdlib only; deterministic output: running it twice
without upstream data changes produces byte-identical files.

Usage:
    GH_TOKEN=<token> python scripts/generate_profile.py

Data sources
    REST   v3  /users/{u}, /users/{u}/repos, /repos/{o}/{r}/languages
    GraphQL    contributionsCollection (commits, PRs, issues, calendar)
    Fallback   scrape of github.com/users/{u}/contributions day tooltips

If a source is unavailable the affected value degrades to "--" or an empty
visualization. Nothing is ever invented.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.request
from datetime import date, datetime, timezone

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

USER = os.environ.get("PROFILE_USER", "ValiantZippu")
OUT_DIR = os.path.join("assets", "generated")
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""

API = "https://api.github.com"
GRAPHQL = "https://api.github.com/graphql"

# Repositories pinned to the top of the index, in order. Entries that do not
# exist on GitHub yet are still rendered as [ PLANNED ] cards.
FEATURED = [
    {"name": "Kaiteyo"},
    {"name": "Isekaiyo", "status": "PLANNED",
     "description": "Interactive fiction platform"},
]

MAX_CARDS = 4        # cards in the repository index (featured first)
MAX_LANG_REPOS = 30  # non-fork repos scanned for language stats
ACTIVE_DAYS = 120    # pushed within this window => [ ACTIVE ]

# Palette -------------------------------------------------------------------
BG = "#000000"
FG = "#FFFFFF"
SEC = "#B0B0B0"
MUT = "#666666"
DIM = "#2A2A2A"
HEAT = ["#111111", "#3C3C3C", "#6E6E6E", "#9E9E9E", "#FFFFFF"]
LANG_SHADES = ["#FFFFFF", "#B7B7B7", "#8A8A8A", "#646464", "#454545", "#2F2F2F"]

FONT = "ui-monospace,'JetBrains Mono','Fira Code','SF Mono',Menlo,Consolas,monospace"


def esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


def fmt(n) -> str:
    """1234 -> '1.2K', 15600 -> '15.6K', None -> '--'."""
    if n is None:
        return "--"
    n = int(n)
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        v = n / 1_000
        return (f"{v:.1f}".rstrip("0").rstrip(".") if v < 100 else str(round(v))) + "K"
    return str(n)


def warn(msg: str) -> None:
    print(f"[generate] warning: {msg}", file=sys.stderr)


# --------------------------------------------------------------------------- #
# HTTP helpers
# --------------------------------------------------------------------------- #

def _headers() -> dict:
    h = {"Accept": "application/vnd.github+json",
         "User-Agent": "profile-generator"}
    if TOKEN:
        h["Authorization"] = f"Bearer {TOKEN}"
    return h


def http_json(url: str):
    req = urllib.request.Request(url, headers=_headers())
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def graphql(query: str) -> dict:
    body = json.dumps({"query": query}).encode()
    headers = {"Content-Type": "application/json", **_headers()}
    req = urllib.request.Request(GRAPHQL, data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.loads(r.read().decode())
    if payload.get("errors"):
        raise RuntimeError(payload["errors"][0].get("message", "graphql error"))
    return payload.get("data", {})


# --------------------------------------------------------------------------- #
# Data fetching
# --------------------------------------------------------------------------- #

def fetch_user() -> dict:
    try:
        u = http_json(f"{API}/users/{USER}")
        return {"repos": u.get("public_repos"), "followers": u.get("followers")}
    except Exception as e:
        warn(f"user fetch failed: {e}")
        return {"repos": None, "followers": None}


def fetch_repos() -> list[dict]:
    repos, page = [], 1
    while page <= 5:
        try:
            batch = http_json(
                f"{API}/users/{USER}/repos?per_page=100&sort=pushed&page={page}")
        except Exception as e:
            warn(f"repos fetch failed: {e}")
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return repos


CONTRIB_QUERY = """
query {
  user(login: "%s") {
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      contributionCalendar {
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
""" % USER


def fetch_contributions():
    """GraphQL first (rich counts); public-page tooltip scrape as fallback."""
    if TOKEN:
        try:
            node = graphql(CONTRIB_QUERY)["user"]["contributionsCollection"]
            days = {}
            for week in node["contributionCalendar"]["weeks"]:
                for d in week["contributionDays"]:
                    days[d["date"]] = d["contributionCount"]
            return {"commits": node["totalCommitContributions"],
                    "prs": node["totalPullRequestContributions"],
                    "issues": node["totalIssueContributions"],
                    "days": days}
        except Exception as e:
            warn(f"graphql contributions failed: {e}")
    try:
        return scrape_contributions()
    except Exception as e:
        warn(f"contributions scrape failed: {e}")
        return None


def scrape_contributions() -> dict:
    """Parse per-day counts out of the public contributions page."""
    url = f"https://github.com/users/{USER}/contributions"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        html = r.read().decode()

    tips = re.findall(
        r'for="contribution-day-component-(\d+)-(\d+)"[^>]*>(.*?)</tool-tip>',
        html)
    cells: dict[tuple[int, int], int] = {}
    for col, row, tip in tips:
        m = re.match(r"\s*(\d+)\s+contributions?", tip)
        cells[(int(col), int(row))] = int(m.group(1)) if m else 0
    if not cells:
        raise RuntimeError("no day cells found")

    # Anchor the last populated column to the current week, walk backwards.
    last_col = max(c for c, _ in cells)
    today = datetime.now(timezone.utc).date()
    anchor_sunday = today.toordinal() - ((today.weekday() + 1) % 7)
    first_sunday = anchor_sunday - 7 * last_col

    days: dict[str, int] = {}
    for (col, row), cnt in cells.items():
        d = date.fromordinal(first_sunday + 7 * col + row)
        days[d.isoformat()] = cnt
    return {"days": days}


def fetch_languages(repos: list[dict]) -> dict[str, int]:
    totals: dict[str, int] = {}
    own = [r for r in repos if not r.get("fork")][:MAX_LANG_REPOS]
    for r in own:
        try:
            langs = http_json(r["languages_url"])
        except Exception:
            continue
        for lang, size in langs.items():
            totals[lang] = totals.get(lang, 0) + size
    return totals


# --------------------------------------------------------------------------- #
# Derived metrics
# --------------------------------------------------------------------------- #

def streaks(days: dict[str, int]) -> tuple[int, int]:
    """(longest streak, current streak) in days."""
    if not days:
        return 0, 0
    ordinals = {date.fromisoformat(d).toordinal(): c for d, c in days.items()}
    lo, hi = min(ordinals), max(ordinals)

    longest = run = 0
    for o in range(lo, hi + 1):
        run = run + 1 if ordinals.get(o, 0) > 0 else 0
        longest = max(longest, run)

    current, o = 0, hi
    while ordinals.get(o, 0) > 0:
        current += 1
        o -= 1
    return longest, current


def weekly_series(days: dict[str, int]) -> list[int]:
    """Contributions summed per ISO week column, oldest -> newest."""
    by_week: dict[int, int] = {}
    for iso, cnt in days.items():
        sunday = date.fromisoformat(iso).toordinal() - \
            ((date.fromisoformat(iso).weekday() + 1) % 7)
        by_week[sunday] = by_week.get(sunday, 0) + cnt
    return [by_week[k] for k in sorted(by_week)]


def repo_status(repo: dict | None, forced: str | None) -> str:
    if forced:
        return forced
    if repo is None:
        return "PLANNED"
    pushed = repo.get("pushed_at")
    if not pushed:
        return "DORMANT"
    dt = datetime.fromisoformat(pushed.replace("Z", "+00:00"))
    age = (datetime.now(timezone.utc) - dt).days
    return "ACTIVE" if age <= ACTIVE_DAYS else "DORMANT"


def select_cards(repos: list[dict]) -> list[dict]:
    by_name = {r["name"].lower(): r for r in repos}
    cards: list[dict] = []
    seen: set[str] = set()

    def add(spec: dict):
        name = spec["name"]
        key = name.lower()
        if key in seen:
            return
        seen.add(key)
        repo = by_name.get(key)
        desc = (spec.get("description") or (repo or {}).get("description")
                or "Personal project")
        tags = [t.upper() for t in (repo or {}).get("topics", [])[:3]]
        if repo and repo.get("language"):
            tags.insert(0, repo["language"].upper())
        elif spec.get("tags"):
            tags = [*spec["tags"], *tags]
        cards.append({
            "name": name,
            "desc": desc,
            "tags": tags[:4],
            "status": repo_status(repo, spec.get("status")),
            "url": f"https://github.com/{USER}/{name}",
            "stars": (repo or {}).get("stargazers_count"),
            "forks": (repo or {}).get("forks_count"),
        })

    for spec in FEATURED:
        add(spec)
    for r in sorted(repos, key=lambda x: x.get("pushed_at") or "",
                    reverse=True):
        if len(cards) >= MAX_CARDS:
            break
        if r.get("fork") or r["name"] == USER:
            continue
        add({"name": r["name"]})
    return cards


# --------------------------------------------------------------------------- #
# SVG primitives
# --------------------------------------------------------------------------- #

def svg_open(w: int, h: int) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" '
            f'height="{h}" viewBox="0 0 {w} {h}" role="img">'
            f'<rect width="{w}" height="{h}" fill="{BG}"/>')


def text(x, y, s, size, fill=FG, *, weight="normal", spacing=None,
         anchor="start", opacity=None) -> str:
    attrs = (f'x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" '
             f'fill="{fill}" font-weight="{weight}" text-anchor="{anchor}"')
    if spacing is not None:
        attrs += f' letter-spacing="{spacing}"'
    if opacity is not None:
        attrs += f' opacity="{opacity}"'
    return f"<text {attrs}>{esc(s)}</text>"


# --------------------------------------------------------------------------- #
# Renderers
# --------------------------------------------------------------------------- #

def render_header(metrics: dict) -> str:
    w, h = 880, 300
    cx = w // 2
    parts = [svg_open(w, h)]
    parts.append(f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" '
                 f'fill="none" stroke="{FG}" stroke-opacity="0.35"/>')
    parts.append(f'<line x1="0.5" y1="40" x2="{w-0.5}" y2="40" stroke="{FG}" '
                 f'stroke-opacity="0.25"/>')
    for i in range(3):
        parts.append(f'<circle cx="{26 + i*22}" cy="20" r="4.5" fill="none" '
                     f'stroke="{SEC}"/>')
    parts.append(text(96, 25, f"{USER.lower()}@github:~$ ./init_profile.sh",
                      13, SEC))
    parts.append(text(w - 24, 25, "[ OK ]", 13, FG, weight="bold",
                      anchor="end"))

    parts.append(text(cx, 132, "VALIANTZIPPU", 46, FG, weight="bold",
                      spacing="14", anchor="middle"))
    parts.append(f'<line x1="{cx-190}" y1="152" x2="{cx+190}" y2="152" '
                 f'stroke="{FG}" stroke-opacity="0.3"/>')
    parts.append(text(cx, 186, "> SYSTEM ARCHITECT . DEVELOPER . MUSICIAN . "
                      "DESIGNER", 14, SEC, spacing="1", anchor="middle"))
    parts.append(text(cx, 212, "> EXECUTING KAITEYO AND ISEKAIYO ...", 13,
                      MUT, spacing="1", anchor="middle"))
    parts.append(text(cx, 256, "STATUS : ONLINE", 13, FG, weight="bold",
                      anchor="middle"))
    parts.append(text(cx, 276, "MODE : BUILD", 13, MUT, spacing="2",
                      anchor="middle"))
    parts.append("</svg>")
    return "".join(parts)


TILES_H = 236  # 2 rows x 110 + 16 gap
HEAT_H = 141   # month label row 26 + 7 rows x 15 + padding
ACT_H = 170


def _tiles_frag(m: dict) -> str:
    """Metric tile grid fragment (no outer frame)."""
    streak = m.get("streak_longest")
    tiles = [
        ("REPOSITORIES", fmt(m.get("repos")), "PUBLIC"),
        ("STARS", fmt(m.get("stars")), "EARNED"),
        ("COMMITS", fmt(m.get("commits")), "LAST 365 DAYS"),
        ("LONGEST STREAK", "--" if streak is None else str(streak), "DAYS"),
        ("CONTRIBUTIONS", fmt(m.get("total_contribs")), "LAST 365 DAYS"),
        ("FOLLOWERS", fmt(m.get("followers")), "TOTAL"),
    ]
    tw, th, gap = 280, 110, 16
    parts = []
    for i, (label, value, sub) in enumerate(tiles):
        x = (i % 3) * (tw + gap)
        y = (i // 3) * (th + gap)
        parts.append(f'<rect x="{x+0.5}" y="{y+0.5}" width="{tw-1}" '
                     f'height="{th-1}" fill="none" stroke="{FG}" '
                     f'stroke-opacity="0.28"/>')
        parts.append(text(x + 16, y + 28, label, 11, MUT, spacing="2"))
        parts.append(text(x + 16, y + 72, value, 32, FG, weight="bold",
                          spacing="1"))
        parts.append(text(x + 16, y + 95, sub, 10, MUT, spacing="2"))
    return "".join(parts)


def render_metrics(m: dict) -> str:
    parts = [svg_open(872, TILES_H)]
    parts.append(_tiles_frag(m))
    parts.append("</svg>")
    return "".join(parts)


def _heat_frag(days: dict[str, int]) -> str:
    """Contribution heatmap fragment (no outer frame)."""
    cell, pitch, lbl_h, day_w = 12, 15, 26, 34
    cols: dict[int, dict[int, tuple[str, int]]] = {}
    for iso, cnt in sorted((days or {}).items()):
        d = date.fromisoformat(iso)
        sunday = d.toordinal() - ((d.weekday() + 1) % 7)
        cols.setdefault(sunday, {})[(d.weekday() + 1) % 7] = (iso, cnt)
    sundays = sorted(cols)

    parts = []
    if sundays:
        prev_month = None
        for wi, sunday in enumerate(sundays):
            first_iso = next((cols[sunday][r][0] for r in range(7)
                              if r in cols[sunday]), "")
            mo = date.fromisoformat(first_iso).month if first_iso else None
            if mo and mo != prev_month:
                prev_month = mo
                parts.append(text(day_w + wi * pitch, 14,
                                  ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
                                   "JUL", "AUG", "SEP", "OCT", "NOV",
                                   "DEC"][mo - 1], 10, MUT, spacing="1"))
            for row in range(7):
                iso, cnt = cols[sunday].get(row, ("", 0))
                if not iso:
                    continue
                level = 0 if cnt <= 0 else min(
                    4, 1 + (cnt > 1) + (cnt >= 4) + (cnt >= 8))
                x, y = day_w + wi * pitch, lbl_h + row * pitch
                parts.append(f'<rect x="{x}" y="{y}" width="{cell}" '
                             f'height="{cell}" rx="2" fill="{HEAT[level]}"/>')
        for ri, lbl in enumerate(["MON", "WED", "FRI"]):
            parts.append(text(0, lbl_h + ri * 2 * pitch + cell - 1, lbl, 9,
                              MUT))
    else:
        parts.append(text(440, HEAT_H // 2,
                          "// CONTRIBUTION DATA UNAVAILABLE", 13, MUT,
                          anchor="middle"))
    return "".join(parts)


def render_heatmap(days: dict[str, int]) -> str:
    parts = [svg_open(880, HEAT_H)]
    parts.append(_heat_frag(days))
    parts.append("</svg>")
    return "".join(parts)


def _act_frag(series: list[int]) -> str:
    """Weekly activity line-chart fragment (no outer frame)."""
    w = 880
    pad_l, pad_r, pad_t, pad_b = 44, 16, 14, 28
    parts = []
    if series:
        peak = max(max(series), 1)
        iw, ih = w - pad_l - pad_r, ACT_H - pad_t - pad_b
        n = len(series)
        px = lambda i: pad_l + iw * i / max(n - 1, 1)
        py = lambda v: pad_t + ih - ih * v / peak
        for frac in (0.25, 0.5, 0.75, 1.0):
            y = pad_t + ih - ih * frac
            parts.append(f'<line x1="{pad_l}" y1="{y:.1f}" x2="{w-pad_r}" '
                         f'y2="{y:.1f}" stroke="{FG}" stroke-opacity="0.08"/>')
            parts.append(text(pad_l - 8, y + 3, str(round(peak * frac)), 10,
                              MUT, anchor="end"))
        pts = " ".join(f"{px(i):.1f},{py(v):.1f}"
                       for i, v in enumerate(series))
        parts.append(f'<polyline points="{pts}" fill="none" stroke="{FG}" '
                     f'stroke-width="1.6"/>')
        for i, v in enumerate(series):
            if v > 0:
                parts.append(f'<rect x="{px(i)-2:.1f}" y="{py(v)-2:.1f}" '
                             f'width="4" height="4" fill="{SEC}"/>')
        parts.append(text(pad_l, ACT_H - 6, "-52W", 10, MUT))
        parts.append(text(w - pad_r, ACT_H - 6, "NOW", 10, MUT,
                          anchor="end"))
    else:
        parts.append(text(440, ACT_H // 2, "// ACTIVITY DATA UNAVAILABLE", 13,
                          MUT, anchor="middle"))
    return "".join(parts)


def render_activity(series: list[int]) -> str:
    parts = [svg_open(880, ACT_H)]
    parts.append(_act_frag(series))
    parts.append("</svg>")
    return "".join(parts)


def render_stats(metrics: dict, days: dict[str, int],
                 series: list[int]) -> str:
    """One continuous stats panel: tiles, heatmap and activity graph."""
    w = 880
    title_h = 34
    sec_h = 24   # per-section command label
    div_h = 30   # divider zone between sections
    h = (title_h + TILES_H + div_h
         + sec_h + HEAT_H + div_h
         + sec_h + ACT_H + 14)
    parts = [svg_open(w, h)]
    parts.append(f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" '
                 f'fill="none" stroke="{FG}" stroke-opacity="0.3"/>')

    y = title_h
    parts.append(text(24, 22, "$ ./stats --live", 12, MUT))
    parts.append(f'<g transform="translate(24,{y})">{_tiles_frag(metrics)}</g>')

    y += TILES_H + div_h // 2
    parts.append(f'<line x1="24" y1="{y}" x2="{w-24}" y2="{y}" '
                 f'stroke="{FG}" stroke-opacity="0.18"/>')

    y += div_h // 2 + sec_h
    parts.append(text(24, y - 8, "$ ./heatmap --amoled", 12, MUT))
    parts.append(f'<g transform="translate(24,{y})">{_heat_frag(days)}</g>')

    y += HEAT_H + div_h // 2
    parts.append(f'<line x1="24" y1="{y}" x2="{w-24}" y2="{y}" '
                 f'stroke="{FG}" stroke-opacity="0.18"/>')

    y += div_h // 2 + sec_h
    parts.append(text(24, y - 8, "$ ./activity --graph", 12, MUT))
    parts.append(f'<g transform="translate(24,{y})">{_act_frag(series)}</g>')

    parts.append("</svg>")
    return "".join(parts)


def render_detailed(contrib: dict | None, languages: dict[str, int]) -> str:
    w = 880
    c = contrib or {}
    lang_items = sorted(languages.items(), key=lambda kv: -kv[1])[:6]

    summary_h = 40 + len((
        "x", "y", "z", "w")) * 24
    lang_h = (56 + len(lang_items) * 34) if lang_items else 60
    h = summary_h + lang_h

    parts = [svg_open(w, h)]
    parts.append(text(24, 28, "$ ./analytics --breakdown", 13, SEC))
    parts.append(f'<line x1="24" y1="42" x2="{w-24}" y2="42" stroke="{FG}" '
                 f'stroke-opacity="0.2"/>')

    total_365 = sum((c.get("days") or {}).values()) or None
    rows = [
        ("PUSHES / COMMITS (365D)", fmt(c.get("commits"))),
        ("PULL REQUESTS (365D)", fmt(c.get("prs"))),
        ("ISSUES OPENED (365D)", fmt(c.get("issues"))),
        ("TOTAL CONTRIBUTIONS (365D)", fmt(total_365)),
    ]
    y = 70
    for label, val in rows:
        parts.append(text(24, y, label, 12, MUT, spacing="1"))
        parts.append(text(360, y, "::", 12, DIM))
        parts.append(text(400, y, val, 13, FG, weight="bold"))
        y += 24

    bar_y = y + 22
    parts.append(f'<line x1="24" y1="{bar_y-16}" x2="{w-24}" y2="{bar_y-16}" '
                 f'stroke="{FG}" stroke-opacity="0.2"/>')
    if lang_items:
        total = sum(v for _, v in lang_items)
        parts.append(text(24, bar_y + 8, "$ ./languages --ranked", 13, SEC))
        ly = bar_y + 40
        track_w = w - 480
        for i, (lang, size) in enumerate(lang_items):
            pct = size / total * 100
            shade = LANG_SHADES[min(i, len(LANG_SHADES) - 1)]
            parts.append(text(24, ly, lang.upper(), 12, FG, spacing="1"))
            bw = max(2, round(track_w * pct / 100))
            parts.append(f'<rect x="220" y="{ly-11}" width="{bw}" height="12" '
                         f'fill="{shade}"/>')
            parts.append(f'<rect x="220.5" y="{ly-10.5}" width="{track_w-1}" '
                         f'height="11" fill="none" stroke="{FG}" '
                         f'stroke-opacity="0.15"/>')
            parts.append(text(w - 24, ly, f"{pct:.1f}%", 12, SEC,
                              anchor="end"))
            ly += 34
    else:
        parts.append(text(24, bar_y + 8, "// LANGUAGE DATA UNAVAILABLE", 12,
                          MUT))
    parts.append("</svg>")
    return "".join(parts)


def wrap_desc(desc: str, limit: int = 88) -> list[str]:
    words, lines, cur = desc.split(), [], ""
    for wd in words:
        if cur and len(cur) + len(wd) + 1 > limit:
            lines.append(cur)
            cur = wd
            if len(lines) == 2:
                break
        else:
            cur = f"{cur} {wd}".strip()
    if cur and len(lines) < 2:
        lines.append(cur)
    return lines[:2]


def render_repo_card(card: dict, index: int) -> str:
    w, h = 880, 176
    num = f"{index + 1:02d}"
    status = card["status"]
    dimmed = status == "PLANNED"
    op = "0.55" if dimmed else None

    parts = [svg_open(w, h)]
    parts.append(f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" '
                 f'fill="none" stroke="{FG}" stroke-opacity="0.3"/>')
    parts.append(text(24, 38, f"{num}_ / {card['name'].upper()}", 17, FG,
                      weight="bold", spacing="2", opacity=op))
    parts.append(text(w - 24, 37, f"[ {status} ]", 12,
                      SEC if dimmed else FG, weight="bold", spacing="2",
                      anchor="end"))
    parts.append(f'<line x1="0.5" y1="54" x2="{w-0.5}" y2="54" stroke="{FG}" '
                 f'stroke-opacity="0.18"/>')

    dy = 82
    for line in wrap_desc(card["desc"]):
        parts.append(text(24, dy, line, 13, SEC, opacity=op))
        dy += 21

    tx, ty = 24, 128
    for tag in card["tags"]:
        tw = int(len(tag) * 8.1) + 24
        parts.append(f'<rect x="{tx}" y="{ty-15}" width="{tw}" height="21" '
                     f'rx="2" fill="none" stroke="{FG}" '
                     f'stroke-opacity="0.3"/>')
        parts.append(text(tx + 12, ty, tag, 11, MUT, spacing="1"))
        tx += tw + 10

    parts.append(f'<line x1="0.5" y1="146" x2="{w-0.5}" y2="146" '
                 f'stroke="{FG}" stroke-opacity="0.18"/>')
    stars = fmt(card["stars"])
    forks = fmt(card["forks"])
    parts.append(text(24, 164, f"STARS {stars}   FORKS {forks}", 11, MUT,
                      spacing="1"))
    label = "-> TRACK REPOSITORY" if dimmed else "-> OPEN REPOSITORY"
    parts.append(text(w - 24, 164, label, 12, FG, weight="bold", spacing="2",
                      anchor="end"))
    parts.append("</svg>")
    return "".join(parts)


CONTACT_CARDS = [
    ("GITHUB", "/ValiantZippu", f"https://github.com/{USER}"),
    ("EMAIL", "emailzippu@gmail.com", "mailto:emailzippu@gmail.com"),
    ("PORTFOLIO", "idontworkforothers.com", "https://idontworkforothers.com"),
]


def render_contact(label: str, value: str) -> str:
    w, h = 880, 92
    parts = [svg_open(w, h)]
    parts.append(f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" '
                 f'fill="none" stroke="{FG}" stroke-opacity="0.3"/>')
    parts.append(text(24, 32, label, 11, MUT, spacing="3"))
    parts.append(text(24, 66, value, 15, FG, weight="bold", spacing="0.5"))
    parts.append(text(w - 24, 66, "-> OPEN", 11, SEC, spacing="2",
                      anchor="end"))
    parts.append("</svg>")
    return "".join(parts)


IDENTITY_ROWS = [
    ("NAME", ["ValiantZippu"]),
    ("ALIAS", ["Vazuppu"]),
    ("ROLE", ["Developer / System Architect", "Musician / Designer"]),
    ("STATUS", ["Building in public"]),
    ("APPROACH", ["Create \u00b7 Solve \u00b7 Learn \u00b7 Repeat"]),
]
FOCUS_COLUMNS = [
    ("BUILDING", ["Kaiteyo", "Isekaiyo", "Personal Tooling"]),
    ("LEARNING", ["Java", "Rust", "TypeScript", "Kotlin", "Python", "Web"]),
    ("EXPLORING", ["System Design", "UX / UI", "Architecture",
                   "Design Language"]),
]
TOOLKIT_ROWS = [
    ("LANGUAGES", "Rust \u00b7 TypeScript \u00b7 Java \u00b7 Kotlin \u00b7 Python"),
    ("DEVELOPMENT", "Git \u00b7 GitHub \u00b7 Gradle \u00b7 VS Code"),
    ("DESIGN", "Figma \u00b7 Photoshop \u00b7 Clip Studio"),
    ("CREATIVE", "Ableton \u00b7 FL Studio \u00b7 DaVinci Resolve"),
    ("SYSTEMS", "Linux \u00b7 Android \u00b7 Windows"),
]


def render_about() -> str:
    w = 880
    id_h = 56 + sum(len(vals) + 1 for _, vals in IDENTITY_ROWS) * 24
    focus_h = 60 + max(len(items) for _, items in FOCUS_COLUMNS) * 24 + 28
    h = id_h + focus_h
    parts = [svg_open(w, h)]
    parts.append(f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" '
                 f'fill="none" stroke="{FG}" stroke-opacity="0.3"/>')
    parts.append(text(24, 32, "> cat ~/identity.dat", 13, SEC))
    parts.append(f'<line x1="24" y1="46" x2="{w-24}" y2="46" stroke="{FG}" '
                 f'stroke-opacity="0.18"/>')
    y = 78
    for label, values in IDENTITY_ROWS:
        parts.append(text(24, y, label, 12, MUT, spacing="2"))
        for j, val in enumerate(values):
            vx = 180 if j == 0 else 24
            parts.append(text(vx, y + j * 24, val, 13, FG, weight="bold"))
        y += (len(values) + 1) * 24
    parts.append(f'<line x1="24" y1="{y - 8}" x2="{w-24}" y2="{y - 8}" '
                 f'stroke="{FG}" stroke-opacity="0.18"/>')
    cy = y + 28
    col_x = [24, 330, 620]
    for (head, items), cx in zip(FOCUS_COLUMNS, col_x):
        parts.append(text(cx, cy, head, 13, FG, weight="bold", spacing="2"))
        for k, item in enumerate(items):
            parts.append(text(cx, cy + 26 + k * 24, item, 12, SEC))
    parts.append("</svg>")
    return "".join(parts)


def render_toolkit() -> str:
    w = 880
    h = 74 + len(TOOLKIT_ROWS) * 36
    parts = [svg_open(w, h)]
    parts.append(f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" '
                 f'fill="none" stroke="{FG}" stroke-opacity="0.3"/>')
    parts.append(text(24, 32, "$ ./toolkit --inventory", 13, SEC))
    parts.append(f'<line x1="24" y1="46" x2="{w-24}" y2="46" stroke="{FG}" '
                 f'stroke-opacity="0.18"/>')
    y = 80
    for label, values in TOOLKIT_ROWS:
        parts.append(text(24, y, label, 12, FG, weight="bold", spacing="2"))
        parts.append(text(260, y, values, 13, SEC))
        y += 36
    parts.append("</svg>")
    return "".join(parts)


def render_footer() -> str:
    w, h = 880, 196
    parts = [svg_open(w, h)]
    parts.append(f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" '
                 f'fill="none" stroke="{FG}" stroke-opacity="0.35"/>')
    parts.append(text(24, 36, "$ ./session.log", 13, SEC))
    rows = [("SYSTEM STATUS", "ONLINE"), ("MODE", "BUILD"),
            ("USER", "VALIANTZIPPU")]
    y = 76
    for label, value in rows:
        parts.append(text(24, y, label, 12, MUT, spacing="1"))
        parts.append(text(300, y, "::", 12, DIM))
        parts.append(text(340, y, value, 13, FG, weight="bold", spacing="1"))
        y += 26
    parts.append(text(w // 2, h - 22, "\u00a9 2026 VALIANTZIPPU", 12, MUT,
                      spacing="2", anchor="middle"))
    parts.append("</svg>")
    return "".join(parts)


def render_label(cmd: str) -> str:
    w, h = 880, 34
    parts = [svg_open(w, h)]
    parts.append(text(2, 22, cmd, 12, MUT))
    parts.append("</svg>")
    return "".join(parts)


# --------------------------------------------------------------------------- #
# Output (idempotent writes)
# --------------------------------------------------------------------------- #

def write_if_changed(path: str, content: str) -> bool:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:
        with open(path, encoding="utf-8") as f:
            if f.read() == content:
                return False
    except FileNotFoundError:
        pass
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[generate] wrote {path}")
    return True


def main() -> int:
    user = fetch_user()
    repos = fetch_repos()
    contrib = fetch_contributions()
    languages = fetch_languages(repos)

    stars = sum(r.get("stargazers_count", 0) for r in repos
                if not r.get("fork"))
    longest, _ = streaks((contrib or {}).get("days") or {})
    metrics = {
        "repos": user["repos"],
        "followers": user["followers"],
        "stars": stars,
        "commits": (contrib or {}).get("commits"),
        "streak_longest": longest if contrib else None,
        "total_contribs": sum(((contrib or {}).get("days") or {}).values())
                          or None,
    }

    outputs = {
        "header.svg": render_header(metrics),
        "stats.svg": render_stats(metrics, (contrib or {}).get("days") or {},
                                  weekly_series(
                                      (contrib or {}).get("days") or {})),
        "detailed.svg": render_detailed(contrib, languages),
    }
    for i, card in enumerate(select_cards(repos)):
        outputs[f"repo_{card['name']}.svg"] = render_repo_card(card, i)
    for label, value, _url in CONTACT_CARDS:
        outputs[f"contact_{label.lower()}.svg"] = render_contact(label, value)
    outputs["about.svg"] = render_about()
    outputs["toolkit.svg"] = render_toolkit()
    outputs["footer.svg"] = render_footer()
    outputs["label_projects.svg"] = render_label(
        "$ ls ~/repositories --index")
    outputs["label_contact.svg"] = render_label("$ ./contact --open")

    changed = sum(write_if_changed(os.path.join(OUT_DIR, name), body)
                  for name, body in outputs.items())
    print(f"[generate] done -- {len(outputs)} assets, {changed} changed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
