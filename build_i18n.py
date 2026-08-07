#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genera /es/, /de/, /fr/ e /it/ a partir de index.html (ingles).

  python3 build_i18n.py        # construye
  python3 build_i18n.py --v    # ademas lista las cadenas sin traducir

Reglas:
  - Solo sustituye cadenas EXACTAS del diccionario. Lo que no este traducido
    se queda en ingles, nunca se inventa.
  - Reescribe rutas relativas a absolutas para que funcionen desde /es/ etc.
  - Anade selector de idioma, hreflang y og:locale.
  - Avisa de las cadenas sin traducir para poder completarlas despues.
"""
import os, re, sys

RAIZ = os.path.dirname(os.path.abspath(__file__))
IDIOMAS = ['es', 'de', 'fr', 'it']
NOMBRES = {'en': 'English', 'es': 'Español', 'de': 'Deutsch', 'fr': 'Français', 'it': 'Italiano'}
LOCALE = {'en': 'en_GB', 'es': 'es_ES', 'de': 'de_DE', 'fr': 'fr_FR', 'it': 'it_IT'}

# marcas, modelos y datos que NO se traducen nunca
INTOCABLES = {
    'Tassilo de la Torre', 'GD Andana', 'SOTO', 'ALPIN', 'outdoor Magazin',
    'Fujifilm X-T4', 'Fujifilm XF 18-55mm f/2.8-4', 'Tamron 18-300mm',
    'DJI Mini 3 Pro', 'GoPro Hero 10 Black', 'Nuka Sakdari', 'Atlas',
    'tassilo@tassilodelatorre.com', 'Instagram · @tassilodlts',
    'WhatsApp · +34 608 635 863', 'Media kit · PDF',
    '30 × 42 cm', '42 × 59 cm', '59 × 84 cm', '2,580 km', 'TU München',
    'ii.', 'iii.', 'iv.', 'Hold On, Europa', 'Befahrung des Tibers',
    'Bike', 'Kayak', 'Train', 'Expeditions 2026',
    '© 2026 Tassilo de la Torre Schönborn · Madrid',
    'La Vela di Calatrava, Rome',
    # marcas del carrusel (alt / aria-label)
    'Vaude', 'Katadyn', 'Ortlieb', 'Nutrisport', 'Danish Endurance', 'Kilpi',
    'Prabos', 'Petromax', 'Eassun', 'Qwstion', 'Sunwayfoto', 'Armytek',
    'Wuben', 'Turtle Fur', 'Infisport', 'Lomo', 'Sunslice', 'SilverAnt',
    'HoldFast', 'Slip-ins', 'Aquapac', 'Suntribe', 'Shade', 'RoKai',
    'Roselli', 'Avarcas MIBO', 'Tecnomar', 'Montane', 'Vango',
    'Immersion Research', 'Spetton',
    'website', 'summary_large_image', 'Main', 'en_GB', 'Language',
    'English', 'Español', 'Deutsch', 'Français', 'Italiano',
}

ATRIBUTOS = ('content', 'alt', 'title', 'aria-label', 'placeholder')


def cargar(idioma):
    ruta = os.path.join(RAIZ, 'i18n', idioma + '.py')
    if not os.path.exists(ruta):
        return None
    ns = {}
    with open(ruta, encoding='utf-8') as f:
        exec(f.read(), ns)
    return ns['T']


RELATIVA = ('#', '/', 'http', 'mailto:', 'data:', 'tel:', 'javascript:')


def absolutizar(s):
    """photos/x.jpg -> /photos/x.jpg, para que todo funcione desde /es/.

    Cubre atributos src/href, url() de CSS y las rutas relativas que el
    JavaScript del Atlas carga (atlas/routes.geojson, etc.).
    """
    def attr(m):
        a, url = m.group(1), m.group(2)
        if url.startswith(RELATIVA):
            return m.group(0)
        return '%s="/%s"' % (a, url)
    s = re.sub(r'\b(src|href)="([^"]+)"', attr, s)

    def css(m):
        comilla, url = m.group(1), m.group(2)
        if url.startswith(RELATIVA):
            return m.group(0)
        return "url(%s/%s%s)" % (comilla, url, comilla)
    s = re.sub(r"url\((['\"]?)([^)'\"]+)\1\)", css, s)

    def js(m):
        c, url = m.group(1), m.group(2)
        if url.startswith(RELATIVA):
            return m.group(0)
        return '%s/%s%s' % (c, url, c)
    s = re.sub(r"(['\"])((?:atlas|photos|logos|writing)/[A-Za-z0-9_\-./]+)\1", js, s)
    return s


def selector(actual):
    partes = []
    for cod in ['en'] + IDIOMAS:
        destino = '/' if cod == 'en' else '/%s/' % cod
        if cod == actual:
            partes.append('<span aria-current="true">%s</span>' % cod.upper())
        else:
            partes.append('<a href="%s" hreflang="%s" title="%s">%s</a>'
                          % (destino, cod, NOMBRES[cod], cod.upper()))
    return '<div class="langsel" aria-label="Language">' + ''.join(partes) + '</div>'


CSS_SEL = """
  .langsel{display:flex;gap:1px;align-items:center;font-family:var(--sans);
    font-size:10px;letter-spacing:.13em;order:3;flex:0 0 auto}
  .langsel a,.langsel span{padding:4px 5px;text-decoration:none;color:var(--ink);
    opacity:.5;border-bottom:1px solid transparent;transition:opacity .2s ease}
  .langsel a:hover{opacity:1}
  .langsel span[aria-current]{opacity:1;border-bottom-color:currentColor}
  @media(max-width:720px){.langsel{font-size:11px;margin-left:auto;margin-right:4px}
    .langsel a,.langsel span{padding:6px 5px}}
"""


def hreflang():
    out = ['<link rel="alternate" hreflang="en" href="https://tassilodelatorre.com/">']
    for cod in IDIOMAS:
        out.append('<link rel="alternate" hreflang="%s" href="https://tassilodelatorre.com/%s/">'
                   % (cod, cod))
    out.append('<link rel="alternate" hreflang="x-default" href="https://tassilodelatorre.com/">')
    return '\n'.join(out)


def visibles(s):
    """Cadenas visibles, tal cual salen del HTML (sin des-escapar)."""
    t = re.sub(r'<style.*?</style>', '', s, flags=re.S)
    t = re.sub(r'<script.*?</script>', '', t, flags=re.S)
    fuera, vistos = [], set()
    for x in re.findall(r'>([^<>]{3,})<', t):
        x = x.strip()
        if not x or len(x) < 3 or x in vistos:
            continue
        if re.fullmatch(r'[\W\d\s·→←]+', x):
            continue
        vistos.add(x)
        fuera.append(x)
    for a in ATRIBUTOS:
        for m in re.findall(r'\b%s="([^"]{4,})"' % a, t):
            if m in vistos or m.startswith(('http', '#', 'width=')):
                continue
            vistos.add(m)
            fuera.append(m)
    return fuera


def preparar_ingles(src):
    """Anade selector, hreflang y og:locale a la version inglesa."""
    if 'langsel' in src:
        return src, False
    src = src.replace('  /* ---------- partners ---------- */',
                      CSS_SEL + '  /* ---------- partners ---------- */', 1)
    src = src.replace('</head>', hreflang() +
                      '\n<meta property="og:locale" content="en_GB">\n</head>', 1)
    src = src.replace('</nav>', '</nav>\n      ' + selector('en'), 1)
    return src, True


def main():
    ruta_src = os.path.join(RAIZ, 'index.html')
    src = open(ruta_src, encoding='utf-8').read()

    src, cambiado = preparar_ingles(src)
    if cambiado:
        open(ruta_src, 'w', encoding='utf-8').write(src)
        print('index.html (en): selector, hreflang y og:locale anadidos')

    todas = visibles(src)
    print('cadenas detectadas: %d' % len(todas))

    for cod in IDIOMAS:
        T = cargar(cod)
        if T is None:
            print('  %s: sin diccionario, saltado' % cod)
            continue
        out = src
        out = out.replace('<html lang="en">', '<html lang="%s">' % cod, 1)

        # primero las cadenas largas, para no romper las cortas
        for k in sorted(T, key=len, reverse=True):
            v = T[k]
            if not v or k in INTOCABLES:
                continue
            out = re.sub(r'>(\s*)' + re.escape(k) + r'(\s*)<',
                         lambda m, v=v: '>' + m.group(1) + v + m.group(2) + '<', out)
            for a in ATRIBUTOS:
                out = out.replace('%s="%s"' % (a, k), '%s="%s"' % (a, v))
            out = out.replace('<title>%s</title>' % k, '<title>%s</title>' % v)

        for k in sorted(T, key=len, reverse=True):
            v = T[k]
            if not v or k in INTOCABLES:
                continue
            if len(k) > 20:            # solo cadenas largas del JavaScript
                # escapar apostrofos: el literal JS va entre comillas simples
                js = v.replace('\\', '\\\\').replace("'", "\\'")
                out = out.replace("'" + k + "'", "'" + js + "'")

        out = absolutizar(out)
        out = re.sub(r'<link rel="canonical" href="[^"]*"',
                     '<link rel="canonical" href="https://tassilodelatorre.com/%s/"' % cod, out)
        out = out.replace('<meta property="og:locale" content="en_GB">',
                          '<meta property="og:locale" content="%s">' % LOCALE[cod], 1)
        out = re.sub(r'<div class="langsel"[^>]*>.*?</div>', selector(cod), out,
                     flags=re.S, count=1)

        destino = os.path.join(RAIZ, cod)
        os.makedirs(destino, exist_ok=True)
        open(os.path.join(destino, 'index.html'), 'w', encoding='utf-8').write(out)

        faltan = [x for x in todas if x not in T and x not in INTOCABLES]
        print('  %s: %d/%d traducidas, faltan %d'
              % (cod, len(todas) - len(faltan), len(todas), len(faltan)))
        if faltan and '--v' in sys.argv:
            for f in faltan:
                print('       falta: %s' % f[:100])


if __name__ == '__main__':
    main()
