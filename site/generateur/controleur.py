#!/usr/bin/env python3
"""
Le contrôleur : il mesure le site construit et REFUSE de le laisser partir si
quelque chose a régressé.

Ce n'est pas une intelligence artificielle et ça ne doit pas en être une. Tous
les défauts de ce projet ont été trouvés par la mesure, et plusieurs ont été
introduits par une étape qui se croyait juste. Un contrôle qui raisonne peut se
laisser convaincre ; un contrôle qui compare des nombres, non.

Il vérifie trois choses, dans cet ordre :

  1. LE CONTRAT est cohérent avec lui-même        (manifeste.py)
  2. LES FICHIERS livrés sont ceux qu'il annonce  (comptes, tailles, poids)
  3. LA PAGE SERVIE mesure ce qu'elle promet      (mesures.mjs, navigateur)

    usage :  python3 controleur.py <manifeste.json> <dossier construit>
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
sys.path.insert(0, ICI)
from manifeste import charger, champs, _valeur, Faute  # noqa: E402

NOEUD = "/opt/node22/bin/node"


class Rapport:
    """Un verdict, pas un journal. Chaque ligne dit ce qu'on a mesuré."""

    def __init__(self):
        self.lignes, self.fautes = [], 0

    def dire(self, ok, quoi, detail=""):
        self.lignes.append(("  ok " if ok else "  NON", quoi, detail))
        if not ok:
            self.fautes += 1

    def titre(self, t):
        self.lignes.append((None, t, ""))

    def rendre(self):
        for marque, quoi, detail in self.lignes:
            if marque is None:
                print(f"\n{quoi}")
            else:
                print(f"{marque}  {quoi}" + (f" — {detail}" if detail else ""))
        print()
        if self.fautes:
            print(f"REFUSÉ — {self.fautes} contrôle(s) en échec.")
        else:
            print("Tout est conforme au contrat.")
        return 1 if self.fautes else 0


def _port_libre():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def servir(dossier):
    """Un serveur local le temps des mesures. Le navigateur d'essai ne doit
    jamais lire les fichiers en `file://` : les chemins relatifs, le typage
    MIME et les requêtes ne s'y comportent pas comme en ligne."""
    port = _port_libre()

    class Muet(http.server.SimpleHTTPRequestHandler):
        # Le film demande plus de mille images : le journal des requêtes
        # noierait le verdict, qui est la seule chose à lire ici.
        def log_message(self, *_):
            pass

        def handle_error(self, *_):
            # Une image absente fait écrire au client sur une connexion déjà
            # fermée ; la trace noierait le verdict. L'absence, elle, est
            # relevée côté navigateur, où elle a un sens.
            pass

    gest = functools.partial(Muet, directory=dossier)
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), gest)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{port}/index.html"


def fichiers(m, out, r):
    """Les images livrées sont-elles celles que le contrat annonce ?"""
    r.titre("LES FICHIERS")
    from PIL import Image
    for nom, s in champs(m["film"]["series"]).items():
        dossier = os.path.join(out, "assets", "film", _valeur(s["dossier"], ""))
        if not os.path.isdir(dossier):
            r.dire(False, f"série {nom}", f"{dossier} n'existe pas — la page "
                                          f"s'afficherait noire sans erreur")
            continue
        noms = sorted(f for f in os.listdir(dossier) if not f.startswith("."))
        attendu = _valeur(s["images"], "")
        r.dire(len(noms) == attendu, f"série {nom} : {len(noms)} images",
               "" if len(noms) == attendu else f"le contrat en annonce {attendu}")

        # Les BORNES, pas seulement le compte : une numérotation qui saute
        # laisse le dernier tiers du défilement figé sur la même image.
        if noms:
            premier, dernier = noms[0], noms[-1]
            suite = [f"f{i:04d}{os.path.splitext(premier)[1]}"
                     for i in range(1, len(noms) + 1)]
            r.dire(noms == suite, f"série {nom} : numérotation continue",
                   "" if noms == suite else f"de {premier} à {dernier}, avec des trous")

            im = Image.open(os.path.join(dossier, premier))
            larg = _valeur(s["largeur"], "")
            r.dire(im.width == larg, f"série {nom} : largeur {im.width} px",
                   "" if im.width == larg else f"le contrat dit {larg}")
            rapp = round(im.width / im.height, 3)
            att = _valeur(s["rapport"], "")
            r.dire(abs(rapp - att) < 0.01, f"série {nom} : rapport {rapp}",
                   "" if abs(rapp - att) < 0.01 else f"le contrat dit {att}")

    for f in m["client"].get("faits", []):
        if f["cle"] == "logo" and f.get("valeur"):
            chemin = os.path.join(out, f["valeur"])
            plafond = m["seuils"].get("logo_octets_max")
            if os.path.exists(chemin) and plafond:
                poids = os.path.getsize(chemin)
                r.dire(poids <= plafond, f"logo : {poids/1024:.0f} Ko",
                       "" if poids <= plafond else
                       f"plafond {plafond/1024:.0f} Ko — il est dans le chemin "
                       f"critique du premier affichage")
            else:
                r.dire(os.path.exists(chemin), "logo présent", chemin)


def page(m, url, r):
    """Ce que la page servie mesure réellement."""
    tailles = ",".join(m["seuils"]["tailles_a_verifier"])
    p = subprocess.run([NOEUD, os.path.join(ICI, "mesures.mjs"), url, tailles],
                       capture_output=True, text=True)
    if p.returncode != 0:
        r.titre("LA PAGE SERVIE")
        r.dire(False, "les mesures n'ont pas pu être prises", p.stderr.strip()[:400])
        return
    d = json.loads(p.stdout)
    seuils, courses = m["seuils"], champs(m["page"]["courses"])
    densite = _valeur(m["film"]["densite_visee"], "")
    series = champs(m["film"]["series"])

    r.titre("LA PAGE SERVIE")
    r.dire(not d["erreurs"], "aucune erreur JavaScript",
           " · ".join(d["erreurs"])[:300])
    ips = d["images_par_seconde"]
    r.dire(ips["mediane"] >= seuils["images_par_seconde"],
           f"débit {ips['mediane']} i/s (médiane de {ips['passages']})",
           "" if ips["mediane"] >= seuils["images_par_seconde"]
           else f"seuil {seuils['images_par_seconde']}")

    for taille, e in d["ecrans"].items():
        r.titre(f"L'ÉCRAN {taille}")
        r.dire(not e["deborde"], "aucun débordement horizontal",
               "" if not e["deborde"] else
               "vérifier les constructions en 100vw : la barre de défilement y "
               "est comptée, la largeur du contenu non")
        r.dire(not e["menu_tronques"], "aucun intitulé tronqué",
               " · ".join(e["menu_tronques"]))
        r.dire(e["liens_bleus"] == 0, "aucun lien resté bleu",
               "" if e["liens_bleus"] == 0 else f"{e['liens_bleus']} lien(s)")
        r.dire(not e.get("absentes"), "aucune image réclamée et absente",
               "" if not e.get("absentes") else
               f"{e['absentes_total']} manquantes — " + " · ".join(e["absentes"])
               + " — le compte déclaré dans la page ne vaut pas celui du dossier")
        r.dire(not e["sous_la_barre"], "aucune ancre sous l'en-tête",
               " · ".join(e["sous_la_barre"]) +
               (f" (en-tête {e['tete_hauteur']} px)" if e["sous_la_barre"] else ""))

        sans_densite = taille.split("@")[0]
        if sans_densite in courses:
            attendue = _valeur(courses[sans_densite], "")
            ecart = abs(e["course"] - attendue)
            r.dire(ecart <= max(50, attendue * 0.01),
                   f"course {e['course']} px",
                   "" if ecart <= max(50, attendue * 0.01) else
                   f"le contrat mesure {attendue} — la mise en page a bougé, "
                   f"le nombre d'images ne vaut plus")
            # La densité RÉELLE, celle que le visiteur subit.
            servie = e.get("serie_servie")
            n = next((_valeur(s["images"], "") for nom, s in series.items()
                      if _valeur(s["dossier"], "") == servie), None)
            if n:
                reelle = e["course"] / n
                r.dire(reelle <= seuils["densite_max"],
                       f"densité réelle {reelle:.0f} px par image ({servie})",
                       "" if reelle <= seuils["densite_max"] else
                       f"visée {densite}, plafond {seuils['densite_max']} — "
                       f"le film saute")

        if e["image"] and e["toile_px"]:
            il, ih = map(int, e["image"].split("x"))
            tl, th = map(int, e["toile_px"].split("x"))
            r.dire(tl <= il and th <= ih,
                   f"toile {e['toile_px']} sur image {e['image']}",
                   "" if tl <= il and th <= ih else
                   "la toile est plus grande que le film : c'est le "
                   "remplissage qui coûte, pas le décodage (184 ms l'image "
                   "en agrandissement contre 1,3 en 1:1)")
        if e["part_visible"] is not None:
            r.dire(True, f"part du film visible {e['part_visible']*100:.0f} %")

        c = e["contrastes"]
        if c.get("corps"):
            r.dire(c["corps"] >= seuils["contraste_corps"],
                   f"contraste du corps {c['corps']}:1",
                   "" if c["corps"] >= seuils["contraste_corps"]
                   else f"seuil {seuils['contraste_corps']}")
        if c.get("second_plan"):
            r.dire(c["second_plan"] >= seuils["contraste_second_plan"],
                   f"contraste du second plan {c['second_plan']}:1",
                   "" if c["second_plan"] >= seuils["contraste_second_plan"]
                   else f"seuil {seuils['contraste_second_plan']}")


def client(m, out, r):
    """Aucun fait non vérifié ne doit être publié."""
    r.titre("LES FAITS DU CLIENT")
    src = open(os.path.join(out, "index.html"), encoding="utf-8").read()
    manquants = [f for f in m["client"]["faits"] if f.get("valeur") is None]
    r.dire(True, f"{len(m['client']['faits']) - len(manquants)} fait(s) avec source")
    if manquants:
        r.dire(True, f"{len(manquants)} à compléter",
               ", ".join(f["cle"] for f in manquants))
    for f in m["client"]["faits"]:
        if f.get("valeur") and f["cle"] in ("siren", "siret_siege", "code_ape"):
            nu = f["valeur"]
            espace = src.replace("&nbsp;", " ").replace(" ", " ")
            vu = nu in src or " ".join(
                [nu[0:3], nu[3:6], nu[6:9]] + ([nu[9:]] if len(nu) > 9 else [])
            ).strip() in espace
            r.dire(vu, f"{f['cle']} publié tel qu'au registre",
                   "" if vu else f"« {nu} » introuvable dans la page")


def main():
    if len(sys.argv) != 3:
        sys.exit("usage : python3 controleur.py <manifeste.json> <dossier construit>")
    chemin, out = sys.argv[1], sys.argv[2]
    r = Rapport()

    r.titre("LE CONTRAT")
    try:
        m = charger(chemin)
        r.dire(True, "le manifeste est cohérent avec lui-même")
    except Faute as e:
        r.dire(False, "le manifeste se contredit", str(e))
        sys.exit(r.rendre())

    if not os.path.isdir(out):
        r.dire(False, "le dossier construit n'existe pas", out)
        sys.exit(r.rendre())

    fichiers(m, out, r)
    client(m, out, r)
    srv, url = servir(out)
    try:
        page(m, url, r)
    finally:
        srv.shutdown()
    sys.exit(r.rendre())


if __name__ == "__main__":
    main()
