#!/usr/bin/env python3
"""
Construit la version tout-en-un de la page pour publication en Artifact.

La page du dépôt charge three.js comme un module ES depuis ./vendor/. Dans un
Artifact il n'y a pas de fichiers voisins, et la CSP refuse aussi bien un hôte
externe qu'un `import` depuis une URL data:. On replie donc three.js dans le
même <script type="module"> que le reste : chaque fichier est enveloppé dans
une IIFE (sinon les noms minifiés de haut niveau entrent en collision), son
`export {}` devient un `return {}`, et l'`import` du coeur devient une
déstructuration.
"""
import base64, os, re, sys

SITE = os.path.dirname(os.path.abspath(__file__))
PAGE = sys.argv[1] if len(sys.argv) > 1 else "index.html"
OUT = os.path.join(SITE, "dist", PAGE)


def parse_specifiers(block):
    """'a as b, c' -> [('a','b'), ('c','c')]"""
    pairs = []
    for part in block.split(","):
        part = part.strip()
        if not part:
            continue
        if " as " in part:
            left, right = part.split(" as ")
            pairs.append((left.strip(), right.strip()))
        else:
            pairs.append((part, part))
    return pairs


def cut(src, start):
    """Découpe la clause {...} qui commence à `start` ; renvoie (contenu, fin)."""
    open_brace = src.index("{", start)
    close_brace = src.index("}", open_brace)
    return src[open_brace + 1:close_brace], close_brace + 1


def wrap_core(src):
    m = re.search(r"\bexport\s*\{", src)
    block, end = cut(src, m.start())
    body = src[:m.start()] + src[end:].lstrip(";\n")
    # export {local as exported}  ->  {exported: local}
    fields = ",".join(f"{exported}:{local}" for local, exported in parse_specifiers(block))
    return '(function(){"use strict";\n' + body + "\nreturn {" + fields + "};\n})()"


def wrap_module(src, core_var):
    # import {exported as local} from "./three.core.min.js"  ->  const {exported: local} = core
    m = re.search(r'\bimport\s*\{', src)
    block, end = cut(src, m.start())
    end = src.index(";", src.index("three.core.min.js", end)) + 1
    binding = ",".join(f"{exported}:{local}" for exported, local in parse_specifiers(block))
    body = src[:m.start()] + src[end:]

    fields = []
    while True:
        m = re.search(r"\bexport\s*\{", body)
        if not m:
            break
        block, end = cut(body, m.start())
        # `export {...} from "./three.core.min.js"` ré-exporte sans créer de
        # liaison locale : ces noms doivent être repris depuis le coeur.
        reexport = re.match(r'\s*from\s*["\'][^"\']*["\']\s*;?', body[end:])
        if reexport:
            end += reexport.end()
            fields += [f"{exported}:{core_var}.{name}" for name, exported in parse_specifiers(block)]
        else:
            fields += [f"{exported}:{local}" for local, exported in parse_specifiers(block)]
        body = body[:m.start()] + body[end:].lstrip(";\n")

    return ('(function(){"use strict";\nconst {' + binding + "} = " + core_var + ";\n"
            + body + "\nreturn {" + ",".join(fields) + "};\n})()")


def main():
    os.chdir(SITE)
    b64 = lambda p: base64.b64encode(open(p, "rb").read()).decode()

    bundle = (
        "/* three.js r185 — replié en place : voir build_artifact.py */\n"
        "const __threeCore = " + wrap_core(open("vendor/three.core.min.js").read()) + ";\n"
        "const THREE = " + wrap_module(open("vendor/three.module.min.js").read(), "__threeCore") + ";\n"
    )

    src = open(PAGE).read()
    head = src.split("<head>", 1)[1].split("</head>", 1)[0]
    body = src.split("<body>", 1)[1].rsplit("</body>", 1)[0]
    head = re.sub(r'<meta charset[^>]*>\s*', "", head)
    head = re.sub(r'<meta name="viewport"[^>]*>\s*', "", head)
    page = head.strip() + "\n" + body.strip() + "\n"

    marker = "import * as THREE from './vendor/three.module.min.js';"
    if marker not in page:
        sys.exit("l'import de three.js est introuvable — le marqueur a changé")
    page = page.replace(marker, bundle)

    for name in sorted(os.listdir("assets/web")):
        uri = "data:image/jpeg;base64," + b64("assets/web/" + name)
        page = page.replace(f"'assets/web/{name}'", f"'{uri}'")
        page = page.replace(f"`assets/web/wrap-${{f.key}}.jpg`",
                            "`data:image/jpeg;base64,${LABEL_B64[f.key]}`")

    labels = {n[5:-4]: b64("assets/web/" + n) for n in os.listdir("assets/web") if n.startswith("wrap-")}
    if "LABEL_B64" in page:
        page = page.replace("const FLAVOURS = [",
            "const LABEL_B64 = " + __import__("json").dumps(labels) + ";\nconst FLAVOURS = [", 1)

    for font in ("anton", "archivo"):
        uri = "data:font/woff2;base64," + b64(f"assets/fonts/{font}.woff2")
        page = page.replace(f"url('assets/fonts/{font}.woff2')", f"url({uri})")

    for leftover in ("vendor/", "assets/web/", "assets/fonts/", "data:text/javascript"):
        if leftover in page:
            sys.exit(f"référence externe restante : {leftover}")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w").write(page)
    print(f"écrit {OUT} — {len(page)/1024/1024:.2f} Mo")


if __name__ == "__main__":
    main()
