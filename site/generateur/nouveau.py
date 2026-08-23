#!/usr/bin/env python3
"""
Fabrique le squelette d'un nouveau site : sa page et son contrat.

C'est l'outil de la cheffe d'orchestre. Il ne compose rien — il pose ce qui
DOIT être là et que trois sites ont appris à ne pas oublier, puis il dit quoi
faire ensuite, dans l'ordre.

    python3 nouveau.py <nom> film=<dossier> marque="…" titre="…" [demo]
    python3 nouveau.py <nom> mesurer <url>

Deux temps, et l'ordre compte :

  1. `nouveau.py <nom> …` écrit la page et le contrat, courses VIDES.
  2. on construit la page seule, on la sert, et `mesurer` relève les courses
     dans la page servie puis les écrit dans le contrat.
  3. alors seulement on encode : le nombre d'images se déduit de la course.

Mesurer d'abord, encoder ensuite. L'inverse a déjà coûté cher ici : des
constantes de course prises pour bonnes ont fait livrer 464 images au lieu de
791, en annonçant « 33,0 px par image » alors que la densité réelle tombait à
56. Une constante fausse qui sert aussi à calculer le message de contrôle ne
peut pas se contredire toute seule.
"""
import json
import os
import re
import subprocess
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(ICI)
GABARIT = os.path.join(SITE, "moteur", "gabarit.html")
NOEUD = "/opt/node22/bin/node"

# Les tailles où tout se vérifie. La densité de pixels EST une taille : à 1,
# l'agrandissement de toile ne se produit pas et le contrôle le plus cher du
# lecteur ne mordrait sur rien.
TAILLES = ["1440x900", "1280x800@2", "900x800", "390x844@3", "360x740@2"]

# Une palette de départ, sombre et neutre. Elle SERA changée — c'est la seule
# chose de ce fichier qui relève du goût, et elle n'est là que pour qu'une page
# fraîche s'affiche correctement avant qu'on y touche.
PALETTE = {
    "FOND": "#0A0C0E", "FOND_RVB": "10,12,14", "SURFACE": "#12161A",
    "ENCRE": "#EDE9E3", "GRIS": "#8A8F96", "SOURD": "#5C626A",
    "ACCENT": "#B8963E",
}

ACTE = """  <section class="{cote}" data-voile="{v}">
    <div class="tenir">
      <div class="mot">
        <p class="acte-num">Acte {n}</p>
        <{h} class="metier-titre">À écrire<br>acte {i}</{h}>
        <p class="cibles">À qui ça s’adresse<br><em>Deuxième ligne</em></p>
        <p class="corps">Ce que dit cet acte. Une phrase qui tient debout seule :
          le visiteur en lira peut-être une sur six.</p>
        <p class="offre">Ce que ça promet</p>{defiler}
      </div>
    </div>
  </section>
"""

SUITE = """<div id="suite">

  <section class="bloc bande" id="propos">
    <div class="chapitre">
      <div>
        <p class="eti pose">À écrire</p>
        <p class="titre t-xl pose" style="margin-top:18px">Le premier<br>
          <span class="ital">chapitre.</span></p>
      </div>
      <div>
        <p class="corps pose">Le corps du chapitre.</p>
      </div>
    </div>
  </section>

  <section class="bloc bande regle" id="parler">
    <div class="chapitre">
      <div>
        <p class="eti pose">Contact</p>
        <p class="titre t-xl pose" style="margin-top:18px">Le dernier<br>
          <span class="ital">chapitre.</span></p>
      </div>
      <div>
        <p class="corps pose">Le corps du chapitre.</p>
      </div>
    </div>
  </section>

  <footer class="bande pied">
    <span>À écrire</span>
  </footer>

</div>"""


def prologue():
    """Six actes vides. Six, parce qu'un plan de film vaut un acte, et qu'un
    film se fait de six plans de huit secondes enchaînés."""
    cotes = [("a-g", "g"), ("a-d", "d"), ("a-g", "g"),
             ("a-d", "d"), ("a-g", "g"), ("a-c", "c")]
    romains = ["I", "II", "III", "IV", "V", "VI"]
    out = ['<div id="prologue"><span id="top"></span>\n']
    for i, ((cote, v), n) in enumerate(zip(cotes, romains), 1):
        out.append(ACTE.format(
            cote=cote, v=v, n=n, i=i,
            # Un seul <h1> par page : c'est le titre du document. Les cinq
            # autres actes sont des <h2>.
            h="h1" if i == 1 else "h2",
            defiler='\n        <p class="defiler"><i></i> Défiler</p>' if i == 1 else ""))
    out.append("\n</div>")
    return "\n".join(out)


def _drapeau(nom, defaut=""):
    for a in sys.argv[2:]:
        if a.startswith(nom + "="):
            return a.split("=", 1)[1]
    return defaut


def creer(nom):
    film = _drapeau("film", nom)
    marque = _drapeau("marque", nom.replace("-", " ").title())
    titre = _drapeau("titre", f"{marque} — à écrire")
    demo = "demo" in sys.argv[2:]
    canonique = _drapeau("canonique", f"https://lamine140cpu.github.io/agnt/{nom}/")

    page = os.path.join(SITE, f"{nom}.html")
    contrat = os.path.join(ICI, f"manifeste-{nom}.json")
    for f in (page, contrat):
        if os.path.exists(f):
            sys.exit(f"{f} existe déjà — on n'écrase pas un site.")

    g = open(GABARIT, encoding="utf-8").read()
    valeurs = dict(PALETTE,
                   FILM=film, MARQUE=marque, TITRE=titre,
                   TITRE_COURT=titre.split("—")[0].strip(),
                   DESCRIPTION="À écrire : 145 caractères au plus, c'est la "
                               "phrase que lit celui qui hésite entre deux résultats.",
                   CANONIQUE=canonique,
                   # Une démonstration se déclare DANS l'en-tête, pas seulement
                   # dans un coin du bas de page : c'est le premier endroit où
                   # le regard passe.
                   ETIQUETTE_TETE='<span class="demo"><i></i>Démonstration</span>'
                                  if demo else "<span></span>",
                   PROLOGUE=prologue(), SUITE=SUITE)
    for cle, val in valeurs.items():
        g = g.replace("{{" + cle + "}}", val)
    reste = re.findall(r"\{\{(\w+)\}\}", g)
    if reste:
        sys.exit(f"marques non remplacées dans le gabarit : {', '.join(set(reste))}")
    open(page, "w", encoding="utf-8").write(g)

    m = {
        "site": nom,
        "_": "Contrat neuf. Les courses sont VIDES : elles se mesurent dans la "
             "page servie, jamais avant. Tant qu'elles le sont, le nombre "
             "d'images ne veut rien dire.",
        "film": {
            "series": {
                "accueil": {
                    "dossier": {"valeur": film, "origine": "choix"},
                    "largeur": {"valeur": 1920, "origine": "choix"},
                    "hauteur": {"valeur": 1080, "origine": "choix"},
                    "images": {"valeur": 0, "origine": "mesure"},
                    "rapport": {"valeur": 1.778, "origine": "choix"},
                    "course": "1440x900",
                },
                "accueil-etroit": {
                    "_": "Le MÊME cadre, moins large. Surtout pas un recadrage "
                         "portrait : en cadrage « couvrir », la part du film "
                         "visible ne dépend que du rapport de la toile et de "
                         "celui du maître, jamais de la série intermédiaire.",
                    "dossier": {"valeur": f"{film}-etroit", "origine": "choix"},
                    "largeur": {"valeur": 1440, "origine": "choix"},
                    "hauteur": {"valeur": 810, "origine": "choix"},
                    "images": {"valeur": 0, "origine": "mesure"},
                    "rapport": {"valeur": 1.778, "origine": "choix"},
                    "course": "390x844",
                },
            },
            "qualite": {"valeur": 45, "origine": "choix"},
            "densite_visee": {"valeur": 33, "origine": "choix"},
        },
        "page": {
            "courses": {"_": "À MESURER — python3 nouveau.py %s mesurer <url>" % nom},
            "ancres": ["propos", "parler"],
            "serie_attendue": {},
            "toile_hauteur_telephone": {"valeur": "64svh", "origine": "choix"},
        },
        "seuils": {
            "images_par_seconde": 55, "densite_max": 40,
            "contraste_corps": 4.5, "contraste_second_plan": 3.0,
            "tailles_a_verifier": TAILLES,
        },
        "client": {
            "_": "Aucun fait ne se devine. Une valeur nulle est une question "
                 "ouverte au client, pas un trou à combler au jugé. Les "
                 "identifiants se vérifient au registre national : "
                 "https://recherche-entreprises.api.gouv.fr/search?q=<SIREN>",
            "faits": [] if demo else [
                {"cle": "raison_sociale", "valeur": None, "source": None},
                {"cle": "siren", "valeur": None, "source": None},
                {"cle": "siege", "valeur": None, "source": None},
                {"cle": "telephone", "valeur": None, "source": None},
                {"cle": "directeur_publication", "valeur": None, "source": None,
                 "_": "Obligation légale."},
                {"cle": "hebergeur", "valeur": None, "source": None,
                 "_": "Obligation légale."},
            ],
        },
    }
    json.dump(m, open(contrat, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

    print(f"écrit  {os.path.relpath(page, SITE)}")
    print(f"écrit  {os.path.relpath(contrat, SITE)}\n")
    print("ENSUITE, DANS CET ORDRE :\n")
    print(f"  1. écrire les six actes et le bas de page dans {nom}.html")
    print(f"  2. poser le film dans assets/film/{film}/  (voir PROMPTS-FILM.md)")
    print(f"  3. mesurer les courses :")
    print(f"       python3 build_flux.py client={nom} manifeste=generateur/manifeste-{nom}.json")
    print(f"       cd dist/{nom} && python3 -m http.server 8000 &")
    print(f"       python3 generateur/nouveau.py {nom} mesurer http://127.0.0.1:8000/index.html")
    print(f"  4. reconstruire — le nombre d'images se déduit alors de la course")
    print(f"  5. contrôler :")
    print(f"       python3 generateur/controleur.py generateur/manifeste-{nom}.json dist/{nom}")


def mesurer(nom, url):
    """Relève les courses dans la page SERVIE et les écrit dans le contrat.

    C'est ici que la règle du dépôt s'applique : personne ne recopie un chiffre
    qu'il n'a pas mesuré. Le nombre d'images en découle, et n'est donc jamais
    saisi à la main non plus.
    """
    contrat = os.path.join(ICI, f"manifeste-{nom}.json")
    if not os.path.exists(contrat):
        sys.exit(f"{contrat} est introuvable")
    m = json.load(open(contrat, encoding="utf-8"))

    p = subprocess.run([NOEUD, os.path.join(ICI, "mesures.mjs"), url,
                        ",".join(m["seuils"]["tailles_a_verifier"])],
                       capture_output=True, text=True)
    if p.returncode != 0:
        sys.exit(f"les mesures ont échoué :\n{p.stderr[:600]}")
    d = json.loads(p.stdout)

    courses = {"_": "prologue.offsetHeight - innerHeight, relevé dans la page "
                    "servie. Elles changent dès qu'on touche à la hauteur des "
                    "actes : les remesurer alors, sans quoi la densité ment."}
    servies = {}
    for taille, e in d["ecrans"].items():
        if e.get("course"):
            courses[taille.split("@")[0]] = {"valeur": e["course"], "origine": "mesure"}
        if e.get("serie_servie"):
            servies[taille] = e["serie_servie"]
    m["page"]["courses"] = courses
    m["page"]["serie_attendue"] = dict(
        {"_": "Une mauvaise série ne se voit pas à l'écran, elle se paye en "
              "octets — ou en film qui saute."}, **servies)

    densite = m["film"]["densite_visee"]["valeur"]
    for nom_s, s in m["film"]["series"].items():
        if s.get("_") is not None and "course" not in s:
            continue
        cle = s.get("course")
        if cle and cle in courses:
            s["images"]["valeur"] = round(courses[cle]["valeur"] / densite)

    json.dump(m, open(contrat, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

    print(f"courses relevées dans {url}\n")
    for t, c in courses.items():
        if t != "_":
            print(f"  {t:10s} {c['valeur']:6d} px")
    print()
    for nom_s, s in m["film"]["series"].items():
        print(f"  {nom_s:16s} -> {s['images']['valeur']:4d} images "
              f"à {densite} px de défilement par image")
    print(f"\nécrit dans {os.path.relpath(contrat, SITE)}")
    print("\nreconstruire maintenant : le compte d'images vient de changer.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__.strip())
    nom = sys.argv[1]
    if not re.fullmatch(r"[a-z0-9-]+", nom):
        sys.exit("le nom doit tenir en minuscules, chiffres et tirets : "
                 "il sert de nom de fichier, de dossier et d'adresse.")
    if "mesurer" in sys.argv[2:]:
        i = sys.argv.index("mesurer")
        if len(sys.argv) <= i + 1:
            sys.exit("il manque l'adresse de la page servie")
        mesurer(nom, sys.argv[i + 1])
    else:
        creer(nom)
