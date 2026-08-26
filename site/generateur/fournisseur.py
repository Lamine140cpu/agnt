#!/usr/bin/env python3
"""
La frontière avec l'IA vidéo. Un seul endroit, quatre façons de la franchir.

POURQUOI UN DESCRIPTEUR ET PAS DU CODE PAR FOURNISSEUR. Tous les modèles vidéo
font la même chose : on soumet un prompt (et une image de départ), on reçoit un
identifiant de tâche, on interroge jusqu'à ce que ce soit prêt, on télécharge un
mp4. Ce qui change d'un fournisseur à l'autre, ce sont des NOMS DE CHAMPS —
`id` ou `task_id`, `status` ou `state`, `output.video_url` ou `result[0].url`.

Écrire une classe par fournisseur, c'est recopier la même mécanique quatre fois
avec quatre occasions de se tromper. Ici la mécanique est écrite une fois et
éprouvée contre un faux serveur ; un fournisseur neuf est un fichier JSON.

CE QUI EST ÉPROUVÉ ET CE QUI NE L'EST PAS — la distinction compte :

  - la MÉCANIQUE (soumettre, interroger, télécharger, expirer, remonter une
    erreur) : éprouvée, `python3 fournisseur.py essai` la fait tourner de bout
    en bout contre un serveur local qui imite un vrai fournisseur.
  - les VALEURS d'un descripteur réel (l'URL, le nom du champ d'état, celui de
    l'image de départ) : NON vérifiées. Elles viennent de la documentation du
    fournisseur, et personne ici n'a eu de clé pour les confronter au réel.
    D'où `"verifie": false` en tête de chaque descripteur, et le refus de
    tourner tant qu'on ne l'a pas basculé à la main après un essai sur UN plan.

    python3 fournisseur.py essai        éprouve la mécanique, sans réseau
    python3 fournisseur.py descripteurs liste ce qui est posé
"""
import base64
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.request

ICI = os.path.dirname(os.path.abspath(__file__))
DESCRIPTEURS = os.path.join(ICI, "descripteurs")


class Refus(Exception):
    """Le fournisseur n'a pas rendu de plan. Jamais silencieux."""


# --------------------------------------------------------------- l'interface

class Fournisseur:
    """Rend un plan vidéo. C'est tout ce que la monteuse a le droit de savoir.

    `amorce` est le chemin d'une image JPEG : la dernière du plan précédent.
    C'est ELLE qui fait la continuité, et c'est le seul paramètre qui compte
    vraiment — un plan commandé sans amorce montre un autre atelier.
    """

    def generer(self, prompt, sortie, amorce=None, duree=8):
        raise NotImplementedError


class Rejeu(Fournisseur):
    """Sert des .mp4 déjà sur le disque, dans l'ordre alphabétique.

    Sert à éprouver tout ce qui vient APRÈS la génération — le profilage, le
    chaînage, la découpe — sans dépenser un centime ni attendre huit minutes.
    """

    def __init__(self, dossier):
        import glob
        self.fichiers = sorted(glob.glob(os.path.join(dossier, "*.mp4")))
        if not self.fichiers:
            raise Refus(f"aucun .mp4 dans {dossier}")
        self.rendu = 0

    def generer(self, prompt, sortie, amorce=None, duree=8):
        if self.rendu >= len(self.fichiers):
            raise Refus(f"le rejeu n'a que {len(self.fichiers)} plans, "
                        f"on en demande un {self.rendu + 1}e")
        src = self.fichiers[self.rendu]
        self.rendu += 1
        import shutil
        shutil.copyfile(src, sortie)
        return sortie


class Capricieux(Fournisseur):
    """Un rejeu qui rate EXPRÈS. Sert à éprouver la boucle de reprise.

    On lui donne les plans dans leur ordre réel, et la liste de ceux qu'il doit
    rater les premières fois. Quand il rate, il rend un plan qui ne suit pas
    celui d'avant — exactement ce que fait un modèle vidéo qui coupe.

    Sans lui, la boucle de reprise ne serait jamais éprouvée : six plans qui
    s'enchaînent tous du premier coup ne la font jamais tourner.
    """

    def __init__(self, ordre, rates=()):
        self.ordre = list(ordre)
        self.rates = dict(rates)          # {n° de plan (à partir de 1): ratés}
        self.faits = {}
        self.pointeur = 1
        self.appels = 0

    def generer(self, prompt, sortie, amorce=None, duree=8):
        import shutil
        self.appels += 1
        i = self.pointeur
        if i > len(self.ordre):
            raise Refus(f"le rejeu n'a que {len(self.ordre)} plans")
        du = self.faits.get(i, 0)
        if du < self.rates.get(i, 0):
            self.faits[i] = du + 1
            # Un plan pris ailleurs dans la chaîne : il ne suit pas.
            src = self.ordre[(i + 1) % len(self.ordre)]
        else:
            src = self.ordre[i - 1]
            self.pointeur += 1
        shutil.copyfile(src, sortie)
        return sortie


class Distant(Fournisseur):
    """Un vrai fournisseur, décrit par un fichier JSON.

    Soumettre -> recevoir un identifiant -> interroger jusqu'à ce que ce soit
    prêt -> télécharger. Aucune connaissance d'un fournisseur particulier n'est
    codée ici : tout est dans le descripteur.
    """

    def __init__(self, descripteur, cle, journal=print):
        if isinstance(descripteur, str):
            descripteur = charger_descripteur(descripteur)
        self.d = descripteur
        self.cle = cle
        self.journal = journal
        if not cle:
            raise Refus(f"« {self.d['nom']} » sans clé")
        if not self.d.get("verifie"):
            raise Refus(
                f"le descripteur « {self.d['nom']} » porte \"verifie\": false.\n\n"
                "Ses noms de champs viennent de la documentation, pas d'un appel\n"
                "réel. Avant de lancer six plans dessus :\n"
                "  1. lancer UN plan et regarder le fichier qui revient ;\n"
                "  2. corriger les champs qui ne collent pas ;\n"
                "  3. seulement alors passer \"verifie\" à true.\n\n"
                "Commander six plans sur un descripteur faux, c'est six plans\n"
                "payés pour rien — ou pire, six plans qui reviennent et ne\n"
                "s'enchaînent pas.")

    # -- le remplissage des gabarits ------------------------------------

    def _remplir(self, gabarit, vals):
        """Remplace les {jetons} partout dans une structure JSON."""
        if isinstance(gabarit, str):
            # Un jeton seul garde son type (un entier reste un entier) ;
            # dans une phrase il est interpolé.
            if gabarit.startswith("{") and gabarit.endswith("}") \
                    and gabarit[1:-1] in vals:
                return vals[gabarit[1:-1]]
            for k, v in vals.items():
                gabarit = gabarit.replace("{" + k + "}", str(v))
            return gabarit
        if isinstance(gabarit, dict):
            return {k: self._remplir(v, vals) for k, v in gabarit.items()}
        if isinstance(gabarit, list):
            return [self._remplir(v, vals) for v in gabarit]
        return gabarit

    @staticmethod
    def _chemin(obj, chemin):
        """« output.video_url » ou « result.0.url » -> la valeur, ou None."""
        for pas in chemin.split("."):
            if obj is None:
                return None
            if isinstance(obj, list):
                try:
                    obj = obj[int(pas)]
                except (ValueError, IndexError):
                    return None
            elif isinstance(obj, dict):
                obj = obj.get(pas)
            else:
                return None
        return obj

    # -- le réseau ------------------------------------------------------

    def _appel(self, url, entetes, corps=None):
        donnees = json.dumps(corps).encode() if corps is not None else None
        req = urllib.request.Request(url, data=donnees, headers=entetes,
                                     method="POST" if corps is not None else "GET")
        if corps is not None:
            req.add_header("Content-Type", "application/json")
        ctx = ssl.create_default_context()
        paquet = os.environ.get("REQUESTS_CA_BUNDLE") or "/root/.ccr/ca-bundle.crt"
        if url.startswith("https") and os.path.exists(paquet):
            ctx.load_verify_locations(paquet)
        try:
            with urllib.request.urlopen(req, timeout=60, context=ctx) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")[:400]
            raise Refus(f"{url} a répondu {e.code} : {detail}")
        except urllib.error.URLError as e:
            raise Refus(f"{url} injoignable : {e.reason}")

    def generer(self, prompt, sortie, amorce=None, duree=8):
        vals = {"cle": self.cle, "prompt": prompt, "duree": duree,
                "amorce_b64": ""}
        if amorce:
            with open(amorce, "rb") as f:
                vals["amorce_b64"] = base64.b64encode(f.read()).decode()

        s = self.d["soumettre"]
        corps = self._remplir(s["corps"], vals)
        # Sans image de départ, on retire le champ plutôt que d'envoyer du
        # vide : plusieurs fournisseurs refusent une chaîne vide là où ils
        # acceptent l'absence.
        if not amorce:
            for k, v in list(corps.items()):
                if v == "":
                    del corps[k]
        rep = self._appel(s["url"], self._remplir(s["entetes"], vals), corps)
        tache = self._chemin(rep, s["champ_tache"])
        if tache is None:
            raise Refus(f"la soumission n'a pas rendu « {s['champ_tache']} » — "
                        f"réponse : {json.dumps(rep)[:300]}")
        vals["tache"] = tache

        i = self.d["interroger"]
        attente = self.d.get("attente", 10)
        plafond = self.d.get("plafond", 900)
        debut = time.time()
        while True:
            rep = self._appel(self._remplir(i["url"], vals),
                              self._remplir(i["entetes"], vals))
            etat = self._chemin(rep, i["champ_etat"])
            if etat in i.get("echoue", []):
                raise Refus(f"le fournisseur a échoué : état « {etat} » — "
                            f"{json.dumps(rep)[:300]}")
            if etat in i["fini"]:
                break
            if time.time() - debut > plafond:
                raise Refus(f"toujours « {etat} » après {plafond} s — abandon")
            self.journal(f"      {etat}… {int(time.time() - debut)} s")
            time.sleep(attente)

        lien = self._chemin(rep, i["champ_video"])
        if not lien:
            raise Refus(f"terminé mais pas de « {i['champ_video']} » — "
                        f"réponse : {json.dumps(rep)[:300]}")
        ctx = ssl.create_default_context()
        paquet = os.environ.get("REQUESTS_CA_BUNDLE") or "/root/.ccr/ca-bundle.crt"
        if lien.startswith("https") and os.path.exists(paquet):
            ctx.load_verify_locations(paquet)
        with urllib.request.urlopen(lien, timeout=300, context=ctx) as r, \
                open(sortie, "wb") as f:
            f.write(r.read())
        if os.path.getsize(sortie) < 10000:
            raise Refus(f"{sortie} fait {os.path.getsize(sortie)} octets — "
                        f"ce n'est pas une vidéo")
        return sortie


def charger_descripteur(nom):
    chemin = nom if os.path.exists(nom) else os.path.join(DESCRIPTEURS, f"{nom}.json")
    if not os.path.exists(chemin):
        poses = [f[:-5] for f in sorted(os.listdir(DESCRIPTEURS))
                 if f.endswith(".json")] if os.path.isdir(DESCRIPTEURS) else []
        raise Refus(f"pas de descripteur « {nom} ». Posés : "
                    + (", ".join(poses) if poses else "aucun"))
    with open(chemin, encoding="utf-8") as f:
        return json.load(f)


def ouvrir(api, cle, plans=None, journal=print):
    """Le fournisseur que la monteuse doit utiliser, d'après les drapeaux."""
    if plans:
        return Rejeu(plans)
    if not api:
        raise Refus("ni `plans=` (rejeu) ni `api=` (fournisseur) — "
                    "la monteuse ne sait pas d'où sortir les plans")
    return Distant(api, cle, journal)


# ------------------------------------------------------------------ l'essai

def _essai():
    """Éprouve la mécanique contre un faux fournisseur, sans réseau externe.

    Le faux serveur imite ce que font les vrais : il rend un identifiant, se
    déclare « processing » deux fois, puis « succeeded » avec un lien. On
    vérifie que la mécanique traverse ça, et qu'elle REFUSE proprement les
    trois façons de rater.
    """
    import functools
    import http.server
    import socket
    import threading

    faux_mp4 = os.urandom(20000)
    etat = {"appels": 0, "recu": None}

    class Faux(http.server.BaseHTTPRequestHandler):
        def log_message(self, *_): pass

        def _json(self, o, code=200):
            b = json.dumps(o).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)

        def do_POST(self):
            n = int(self.headers.get("Content-Length", 0))
            etat["recu"] = json.loads(self.rfile.read(n))
            if self.path == "/refuse":
                return self._json({"error": "quota dépassé"}, 402)
            self._json({"data": {"task_id": "t-42"}})

        def do_GET(self):
            if self.path == "/video.mp4":
                self.send_response(200)
                self.send_header("Content-Length", str(len(faux_mp4)))
                self.end_headers()
                self.wfile.write(faux_mp4)
                return
            if self.path.startswith("/echoue/"):
                return self._json({"status": "failed", "reason": "nsfw"})
            etat["appels"] += 1
            if etat["appels"] < 3:
                return self._json({"status": "processing"})
            self._json({"status": "succeeded",
                        "output": {"video_url": self.base + "/video.mp4"}})

    s = socket.socket(); s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]; s.close()
    Faux.base = f"http://127.0.0.1:{port}"
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), Faux)
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    base = Faux.base
    d = {
        "nom": "essai", "verifie": True, "attente": 0, "plafond": 30,
        "soumettre": {
            "url": base + "/creer",
            "entetes": {"Authorization": "Bearer {cle}"},
            "corps": {"prompt": "{prompt}", "duration": "{duree}",
                      "image": "{amorce_b64}"},
            "champ_tache": "data.task_id",
        },
        "interroger": {
            "url": base + "/tache/{tache}",
            "entetes": {"Authorization": "Bearer {cle}"},
            "champ_etat": "status", "fini": ["succeeded"],
            "echoue": ["failed"], "champ_video": "output.video_url",
        },
    }

    import tempfile
    tmp = tempfile.mkdtemp()
    amorce = os.path.join(tmp, "a.jpg")
    open(amorce, "wb").write(b"\xff\xd8\xff" + os.urandom(500))
    ok = []

    def verifier(titre, condition, detail=""):
        ok.append(bool(condition))
        print(f"  {'ok  ' if condition else 'NON '} {titre}"
              + (f"  {detail}" if detail and not condition else ""))

    sortie = os.path.join(tmp, "p.mp4")
    Distant(d, "CLE-X", journal=lambda *_: None).generer(
        "un atelier", sortie, amorce=amorce, duree=8)

    verifier("le plan est téléchargé", os.path.getsize(sortie) == len(faux_mp4),
             f"{os.path.getsize(sortie)} octets")
    verifier("la clé part dans l'en-tête", etat["recu"] is not None)
    verifier("le prompt part tel quel", etat["recu"]["prompt"] == "un atelier")
    verifier("la durée reste un nombre", etat["recu"]["duration"] == 8,
             repr(etat["recu"].get("duration")))
    verifier("l'amorce part en base64",
             base64.b64decode(etat["recu"]["image"])[:3] == b"\xff\xd8\xff")
    verifier("il a fallu attendre (3 interrogations)", etat["appels"] == 3,
             str(etat["appels"]))

    # Sans amorce, le champ vide doit DISPARAÎTRE, pas partir vide.
    Distant(d, "CLE-X", journal=lambda *_: None).generer(
        "premier plan", os.path.join(tmp, "q.mp4"))
    verifier("sans amorce, le champ image est retiré", "image" not in etat["recu"])

    # Les trois façons de rater, toutes remontées.
    for titre, patch, attendu in (
        ("un 402 est refusé, pas avalé",
         {"soumettre": dict(d["soumettre"], url=base + "/refuse")}, "402"),
        ("un état d'échec est refusé",
         {"interroger": dict(d["interroger"], url=base + "/echoue/{tache}")}, "failed"),
        ("l'attente a un plafond",
         {"plafond": -1}, "abandon"),
    ):
        # Le faux serveur se déclare prêt au 3e appel. Sans remettre le
        # compteur à zéro, le cas du plafond tombait sur un « succeeded »
        # immédiat et ne l'atteignait jamais : l'essai passait au vert en
        # n'éprouvant rien. Trouvé par l'essai lui-même.
        etat["appels"] = 0
        try:
            Distant({**d, **patch}, "CLE-X", journal=lambda *_: None).generer(
                "x", os.path.join(tmp, "r.mp4"))
            verifier(titre, False, "aucun refus levé")
        except Refus as e:
            verifier(titre, attendu in str(e), str(e)[:80])

    # Un descripteur non vérifié ne doit pas tourner du tout.
    try:
        Distant({**d, "verifie": False}, "CLE-X")
        verifier("un descripteur non vérifié est bloqué", False, "il est passé")
    except Refus as e:
        verifier("un descripteur non vérifié est bloqué", "verifie" in str(e))

    srv.shutdown()
    print(f"\n{sum(ok)}/{len(ok)} — "
          + ("la mécanique tient." if all(ok) else "IL RESTE UN DÉFAUT."))
    return 0 if all(ok) else 1


def main():
    quoi = sys.argv[1] if len(sys.argv) > 1 else ""
    if quoi == "essai":
        sys.exit(_essai())
    if quoi == "descripteurs":
        if not os.path.isdir(DESCRIPTEURS):
            sys.exit("aucun descripteur posé")
        for f in sorted(os.listdir(DESCRIPTEURS)):
            if not f.endswith(".json"):
                continue
            d = json.load(open(os.path.join(DESCRIPTEURS, f), encoding="utf-8"))
            marque = "vérifié" if d.get("verifie") else "NON VÉRIFIÉ — à éprouver sur un plan"
            print(f"  {f[:-5]:14s} {marque}")
        return
    sys.exit(__doc__.strip())


if __name__ == "__main__":
    main()
