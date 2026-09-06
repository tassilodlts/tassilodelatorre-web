#!/usr/bin/env python3
"""Builds /journeys/ from journeys/journeys.json.

The JSON is the source of truth: one entry per journey with title, year, lede,
cover and the ordered list of photo ids. Thumbnails are img/<id>_t.webp, the
full image img/<id>.webp. Pixel sizes are read from the files so every <img>
carries width and height and nothing jumps while loading.

    python3 build_journeys.py
"""
import json, pathlib, subprocess, html

ROOT = pathlib.Path(__file__).parent
J = ROOT / "journeys"
SITE = "https://tassilodelatorre.com"
SHOW_FIRST = 12          # photographs shown before "Show all"

NAV = """<div class="topbar">
  <div class="wrap">
    <a class="brand" href="/">Tassilo de la Torre</a>
    <nav aria-label="Main">
      <a href="/">Home</a>
      <a href="/journeys/" aria-current="page">Journeys</a>
      <a href="/brands/">Brands</a>
      <a href="/writing/">Writing</a>
      <a href="/nuka/">Nuka</a>
      <a href="/giving/">Giving</a>
      <a href="/#contact">Contact</a>
    </nav>
  </div>
</div>"""

FOOT = """<footer>
  <span>© 2026 Tassilo de la Torre Schönborn · Madrid</span>
  <span>Under human power.</span>
</footer>"""

ICONS = """<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/favicon.ico" sizes="32x32">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="stylesheet" href="/writing/style.css">
<link rel="stylesheet" href="/journeys/style.css">"""

LIGHTBOX = """<dialog class="lb" aria-label="Photograph">
  <figure><img alt=""></figure>
  <button class="prev" aria-label="Previous">&#8249;</button>
  <button class="next" aria-label="Next">&#8250;</button>
  <button class="close" aria-label="Close">&#215;</button>
  <span class="cnt"></span>
</dialog>
<script>
(function(){
  var links=[].slice.call(document.querySelectorAll('a.ph')),lb=document.querySelector('.lb');
  if(!links.length||!lb||!lb.showModal)return;
  var img=lb.querySelector('img'),cnt=lb.querySelector('.cnt'),i=0;
  function show(k){i=(k+links.length)%links.length;img.src=links[i].href;cnt.textContent=(i+1)+' / '+links.length;
    var n=links[(i+1)%links.length];if(n){var p=new Image();p.src=n.href;}}
  links.forEach(function(a,k){a.addEventListener('click',function(e){e.preventDefault();show(k);lb.showModal();});});
  lb.querySelector('.prev').onclick=function(){show(i-1)};
  lb.querySelector('.next').onclick=function(){show(i+1)};
  lb.querySelector('.close').onclick=function(){lb.close()};
  lb.addEventListener('click',function(e){if(e.target===lb)lb.close();});
  document.addEventListener('keydown',function(e){if(!lb.open)return;if(e.key==='ArrowLeft')show(i-1);if(e.key==='ArrowRight')show(i+1);});
  var more=document.querySelector('.more');
  if(more)more.onclick=function(){document.querySelectorAll('.ph.hidden').forEach(function(a){a.classList.remove('hidden')});more.remove();};
})();
</script>"""


def dims(paths):
    r = subprocess.run(["magick", "identify", "-format", "%i %w %h\n", *paths],
                       capture_output=True, text=True)
    out = {}
    for line in r.stdout.splitlines():
        n, w, h = line.rsplit(" ", 2)
        out[pathlib.Path(n).name] = (int(w), int(h))
    return out


def head(title, desc, url, image, kind="article"):
    e = html.escape
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:type" content="{kind}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{image}">
<meta name="twitter:card" content="summary_large_image">
{ICONS}
</head>
<body>

{NAV}

<div class="wrap">
<article>
"""


def tail(extra=""):
    return f"""</article>

{FOOT}
</div>
{extra}
</body>
</html>
"""


def photos_word(n):
    return f"{n} photograph" + ("" if n == 1 else "s")


def main():
    data = json.load(open(J / "journeys.json"))
    ids = sorted({p for pg in data["pages"] for p in pg["photos"]} | {pg["cover"] for pg in data["pages"]})
    d = dims([str(J / "img" / f"{i}_t.webp") for i in ids])

    # ---- OG previews as JPEG: WhatsApp, LinkedIn and X do not reliably show WebP
    for pg in data["pages"]:
        og = J / "img" / f"og-{pg['slug']}.jpg"
        if not og.exists():
            subprocess.run(["magick", str(J / "img" / f"{pg['cover']}.webp"), "-resize", "1600x1600>",
                            "-quality", "82", "-strip", str(og)], check=True)

    # ---- index
    idx = data["index"]
    out = head(f"{idx['title']} · Tassilo de la Torre", idx["description"], f"{SITE}/journeys/",
               f"{SITE}/journeys/img/og-{data['pages'][0]['slug']}.jpg", "website")
    out += f"""  <header>
    <p class="eyebrow">Archive</p>
    <h1>{html.escape(idx['title'])}</h1>
    <p class="standfirst">{html.escape(idx['standfirst'])}</p>
  </header>

  <div class="cards">
"""
    for pg in data["pages"]:
        w, h = d[f"{pg['cover']}_t.webp"]
        meta = " · ".join(x for x in (pg["year"], photos_word(len(pg["photos"]))) if x)
        out += f"""    <a class="card" href="{pg['slug']}.html">
      <img src="img/{pg['cover']}_t.webp" width="{w}" height="{h}" loading="lazy" decoding="async" alt="">
      <h2>{html.escape(pg['title'])}</h2>
      <p>{html.escape(meta)}</p>
    </a>
"""
    out += "  </div>\n"
    (J / "index.html").write_text(out + tail())

    # ---- one page per journey
    for pg in data["pages"]:
        n = len(pg["photos"])
        title = f"{pg['title']} · Journeys · Tassilo de la Torre"
        url = f"{SITE}/journeys/{pg['slug']}.html"
        out = head(title, pg["lede"], url, f"{SITE}/journeys/img/og-{pg['slug']}.jpg")
        eyebrow = " · ".join(x for x in ("Journey", pg["year"]) if x)
        out += f"""  <header>
    <p class="eyebrow">{eyebrow}</p>
    <h1>{html.escape(pg['title'])}</h1>
    <p class="standfirst">{html.escape(pg['lede'])}</p>
  </header>
  <div class="meta"><span>{photos_word(n)}</span></div>

  <div class="ph-grid">
"""
        for k, pid in enumerate(pg["photos"]):
            w, h = d[f"{pid}_t.webp"]
            hid = " hidden" if k >= SHOW_FIRST else ""
            out += (f'    <a class="ph{hid}" href="img/{pid}.webp">'
                    f'<img src="img/{pid}_t.webp" width="{w}" height="{h}" loading="lazy" decoding="async" alt="">'
                    f'<span class="fn">{pid}</span></a>\n')
        out += "  </div>\n"
        if n > SHOW_FIRST:
            out += f'  <button class="more" type="button">Show all {photos_word(n)}</button>\n'
        out += '  <a class="back" href="/journeys/">&#8592; All journeys</a>\n'
        extra = ('<button class="namebtn" type="button" onclick="document.body.classList.toggle(\'names\')">File names</button>\n'
                 + LIGHTBOX)
        (J / f"{pg['slug']}.html").write_text(out + tail(extra))
        print(f"{pg['slug']:24} {n:3} photographs")
    print("journeys/index.html")


if __name__ == "__main__":
    main()
