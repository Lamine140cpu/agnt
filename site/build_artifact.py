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
PAGES = [a for a in sys.argv[1:] if not a.startswith("-")]
PAGE = PAGES[0] if PAGES else "index.html"
OUT = os.path.join(SITE, "dist", ("leger-" if "--leger" in sys.argv else "") + PAGE)


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


def alleger(chemin):
    """Recomprime une image avant de l'embarquer, en mode --leger.

    Les étiquettes sont livrées en 2528 px parce que la caméra vient les lire
    de très près. Mais depuis que la typographie est tracée au code, l'artwork
    n'est plus qu'un fond à 16 % : le rendre en 1280 px ne se voit pas, et
    divise le poids du fichier par cinq. Un fichier de huit mégaoctets ne
    s'envoie pas, ne se lit pas, et sur certaines machines ne s'ouvre pas.
    """
    import io
    from PIL import Image

    im = Image.open(chemin)
    if max(im.size) > 1280:
        k = 1280 / max(im.size)
        im = im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))),
                       Image.LANCZOS)
    tampon = io.BytesIO()
    im.convert("RGB").save(tampon, "JPEG", quality=82, optimize=True, progressive=True)
    return tampon.getvalue()


def main():
    os.chdir(SITE)
    leger = "--leger" in sys.argv

    def b64(p):
        """L'environnement est laissé intact quoi qu'il arrive : c'est du RGBE,
        mantisses en haut et exposants en bas. Le rééchantillonner mélangerait
        les deux moitiés, et interpoler un exposant n'a aucun sens."""
        octets = alleger(p) if (leger and p.endswith(".jpg")) else open(p, "rb").read()
        return base64.b64encode(octets).decode()

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

    config = open("site.config.js").read()
    config = re.sub(r"\bexport\s+const\s+CONFIG", "const CONFIG", config)
    page = page.replace("import { CONFIG } from './site.config.js';", config)

    marker = "import * as THREE from './vendor/three.module.min.js';"
    if marker not in page:
        sys.exit("l'import de three.js est introuvable — le marqueur a changé")
    page = page.replace(marker, bundle)

    # les matières sont nommées dans un gabarit `assets/web/${nom}.jpg`
    # seules les matières réellement appelées par la page sont embarquées
    utilisees = set(re.findall(r"matiere\('([\w-]+)'", page))
    matieres = {n: "data:image/jpeg;base64," + b64(f"assets/web/{n}.jpg")
                for n in sorted(utilisees) if os.path.exists(f"assets/web/{n}.jpg")}
    if "`assets/web/${nom}.jpg`" in page:
        page = page.replace("`assets/web/${nom}.jpg`", "MATIERES[nom]")
        page = page.replace("const maxAniso = renderer.capabilities.getMaxAnisotropy();",
                            "const MATIERES = " + __import__("json").dumps(matieres) +
                            ";\n  const maxAniso = renderer.capabilities.getMaxAnisotropy();", 1)

    for name in sorted(os.listdir("assets/web")):
        uri = "data:image/jpeg;base64," + b64("assets/web/" + name)
        page = page.replace(f"'assets/web/{name}'", f"'{uri}'")
        page = page.replace("`assets/web/${ARTWORK}-${f.key}.jpg`",
                            "`data:image/jpeg;base64,${LABEL_B64[ARTWORK + '-' + f.key]}`")

    # seul le jeu d'étiquettes retenu par la page est embarqué
    actif = re.search(r"artwork:\s*'(\w+)'", open("site.config.js").read())
    prefixe = (actif.group(1) if actif else "label") + "-"
    labels = {n[:-4]: b64("assets/web/" + n)
              for n in os.listdir("assets/web")
              if n.startswith(prefixe) and n.endswith(".jpg")}
    if "LABEL_B64" in page:
        page = page.replace("const ARTWORK = CONFIG.artwork;",
            "const LABEL_B64 = " + __import__("json").dumps(labels) + ";\nconst ARTWORK = CONFIG.artwork;", 1)

    for font in ("anton", "archivo"):
        uri = "data:font/woff2;base64," + b64(f"assets/fonts/{font}.woff2")
        page = page.replace(f"url('assets/fonts/{font}.woff2')", f"url({uri})")

    # seules les références citées comptent : une occurrence en commentaire
    # n'est pas une ressource à charger
    for chemin in ("vendor/", "assets/web/", "assets/fonts/", "site.config.js"):
        for guillemet in ("'", '"', "`"):
            if guillemet + chemin in page or "/" + chemin in page.replace("//", ""):
                if guillemet + chemin in page:
                    sys.exit(f"référence externe restante : {guillemet}{chemin}")
    if "data:text/javascript" in page:
        sys.exit("un import depuis une URL data: subsiste, la CSP le refuserait")

    # Le dossier de projet voyage dans la page : c'est le même fichier qu'on
    # ouvre pour la voir tourner et qu'on ouvre pour comprendre ce qu'elle fait.
    dossier = os.path.join(SITE, "DOSSIER.md")
    if os.path.exists(dossier):
        texte = open(dossier, encoding="utf-8").read().replace("--", "––")
        page = "<!--\n" + texte + "\n-->\n" + page

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write(page)
    print(f"écrit {OUT} — {len(page)/1024/1024:.2f} Mo")


if __name__ == "__main__":
    main()
