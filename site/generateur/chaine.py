#!/usr/bin/env python3
"""
La chaîne : du film au site contrôlé, sans intervention.

    python3 generateur/chaine.py <nom> [page] [publier]

Elle enchaîne ce qui était fait à la main, dans l'ordre qui compte :

    1. CONSTRUIRE     une première fois, pour avoir une page à mesurer
    2. MESURER        les courses dans la page servie, et en déduire les images
    3. RECONSTRUIRE   avec le compte que la mesure a donné
    4. CONTRÔLER      et s'arrêter là si ça ne passe pas

L'ÉTAPE 4 EST UNE BARRIÈRE, PAS UN RAPPORT. Si le contrôleur refuse, la chaîne
sort en erreur et ne publie rien. C'est tout l'intérêt d'avoir un contrôle qui
ne raisonne pas : on peut lui confier le droit de veto.

POURQUOI CONSTRUIRE DEUX FOIS. La course du prologue dépend de la hauteur des
actes, et le nombre d'images se déduit de la course. Tant que la page n'existe
pas, la course n'est pas mesurable ; tant que la course n'est pas mesurée, le
nombre d'images ne veut rien dire. Ce dépôt a livré 464 images au lieu de 791
pour avoir sauté cette étape — en annonçant fièrement la bonne densité.

`page` saute le réencodage quand les images sont déjà là : la mise en page
change dix fois par jour, la pellicule une fois par site.
"""
import json
import os
import socket
import subprocess
import sys
import threading
import http.server
import functools

ICI = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(ICI)


class Etape:
    """Un pas de la chaîne. Il réussit, ou la chaîne s'arrête."""

    def __init__(self, n, total, titre):
        self.n, self.total, self.titre = n, total, titre
        print(f"\n\033[1m[{n}/{total}] {titre}\033[0m")

    def lancer(self, cmd, cwd=SITE, montrer=3):
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
        lignes = [l for l in p.stdout.splitlines() if l.strip()]
        for l in lignes[-montrer:]:
            print(f"    {l}")
        if p.returncode != 0:
            print(f"\n\033[1mARRÊT\033[0m — l'étape {self.n} a échoué.")
            if p.stderr.strip():
                print(p.stderr.strip()[-1200:])
            elif lignes:
                print("\n".join(lignes[-20:]))
            sys.exit(1)
        return p.stdout


def _servir(dossier):
    s = socket.socket(); s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]; s.close()

    class Muet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *_): pass
        def handle_error(self, *_): pass

    srv = http.server.ThreadingHTTPServer(
        ("127.0.0.1", port), functools.partial(Muet, directory=dossier))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{port}/index.html"


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__.strip())
    nom = sys.argv[1]
    page_seule = "page" in sys.argv[2:]
    publier = "publier" in sys.argv[2:]

    contrat = os.path.join(ICI, f"manifeste-{nom}.json")
    if not os.path.exists(contrat):
        sys.exit(f"{contrat} est introuvable — lancer d'abord nouveau.py")
    out = os.path.join(SITE, "dist", nom)
    rel = f"generateur/manifeste-{nom}.json"
    py = sys.executable

    # Le film doit exister AVANT tout : sans lui, la construction produit une
    # page qui s'affiche noire sans la moindre erreur.
    m = json.load(open(contrat, encoding="utf-8"))
    film = m["film"]["series"]["accueil"]["dossier"]["valeur"]
    source = os.path.join(SITE, "assets", "film", film)
    if not os.path.isdir(source) or not os.listdir(source):
        sys.exit(f"assets/film/{film}/ est vide — lancer d'abord la monteuse :\n"
                 f"  python3 generateur/monteuse.py {nom} plans=<dossier>")

    total = 5 if publier else 4
    base = [py, "build_flux.py", f"client={nom}", f"manifeste={rel}"]

    e = Etape(1, total, "CONSTRUIRE — une page à mesurer")
    e.lancer(base + (["page"] if page_seule else []))

    e = Etape(2, total, "MESURER — les courses dans la page servie")
    srv, url = _servir(out)
    try:
        e.lancer([py, "generateur/nouveau.py", nom, "mesurer", url], montrer=12)
    finally:
        srv.shutdown()

    e = Etape(3, total, "RECONSTRUIRE — avec le compte que la mesure a donné")
    e.lancer(base + ["page"] if page_seule else base)

    e = Etape(4, total, "CONTRÔLER — barrière, pas rapport")
    p = subprocess.run([py, "generateur/controleur.py", rel, f"dist/{nom}"],
                       cwd=SITE, capture_output=True, text=True)
    print(p.stdout)
    if p.returncode != 0:
        print("\033[1mARRÊT\033[0m — le contrôleur refuse. Rien n'est publié.")
        sys.exit(1)

    # LE VERDICT, ÉCRIT À CÔTÉ DE LA PAGE. C'est lui que le publieur exige :
    # sans preuve que le contrôleur a dit oui, rien ne part en ligne. Le
    # laisser en mémoire ne servirait à rien — l'ouvrier qui publie tourne
    # dans un autre processus, parfois une heure plus tard.
    import json as _json, datetime as _dt
    with open(os.path.join(out, ".verdict.json"), "w", encoding="utf-8") as f:
        _json.dump({"conforme": True,
                    "le": _dt.datetime.now().isoformat(timespec="seconds"),
                    "_": "Écrit par chaine.py APRÈS que le contrôleur a dit oui. "
                         "publier.py refuse de mettre en ligne sans ce fichier."},
                   f, ensure_ascii=False, indent=2)

    if publier:
        Etape(5, total, "PUBLIER")
        # Ce message disait « la publication n'est pas câblée » longtemps
        # après qu'elle l'ait été. Un message rassurant et faux est ce que ce
        # dépôt traque partout ailleurs ; il n'avait rien à faire ici.
        sys.path.insert(0, ICI)
        import publier as P
        version = P.publier(nom, journal=lambda l: print("    " + l))
        print(f"    version {version} — la page se sert par /s/{nom}")

    print(f"\n\033[1mdist/{nom}/ est prêt.\033[0m")


if __name__ == "__main__":
    main()
