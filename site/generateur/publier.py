#!/usr/bin/env python3
"""
Publier : de dist/<clé>/ à une URL que le client peut ouvrir.

    python3 generateur/publier.py <clé>              publie dist/<clé>/
    python3 generateur/publier.py <clé> essai        vérifie sans rien envoyer

C'EST LA SEULE OPÉRATION DE TOUTE LA CHAÎNE QU'ON NE PEUT PAS DÉFAIRE.

Tout le reste se refait : un film se regénère, une page se reconstruit, un
contrôle se relance. Une page mise en ligne, elle, a pu être vue, indexée,
partagée. D'où trois précautions qui ne sont pas des politesses :

  1. ON NE PUBLIE PAS CE QUI N'A PAS ÉTÉ CONTRÔLÉ. Le contrôleur écrit son
     verdict à côté de la page ; sans ce fichier, on refuse. Publier
     « juste pour voir » est exactement la façon dont une page non vérifiée
     finit en ligne.
  2. On envoie l'index EN DERNIER. Les images d'abord, la page ensuite :
     l'inverse laisse, pendant toute la durée de l'envoi, une page qui
     réclame des images qui n'existent pas encore.
  3. On RELIT ce qu'on vient d'envoyer. Un envoi qui répond 200 n'est pas
     une preuve que le fichier est lisible à son adresse publique.

CHAQUE PUBLICATION VA DANS UN CHEMIN NEUF — `sites/<clé>/<version>/…`.

Mesuré : Cloudflare, devant le stockage, sert une copie périmée après un
renvoi. L'objet neuf faisait 115 355 octets et l'URL publique en rendait 14,
avec `cf-cache-status: EXPIRED`. Casser le cache à chaque lecture reviendrait
à ne plus en avoir du tout, sur onze cents images. Un chemin neuf ne peut pas
être périmé.

CE QUI EST ÉPROUVÉ : l'envoi, la relecture, l'ordre, et le refus de publier
sans verdict. Éprouvé contre un vrai seau Supabase.
"""
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request

ICI = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(ICI)

# Ce qui ne part pas : des fichiers de travail qui n'ont rien à faire en
# ligne, et qui pèsent.
IGNORES = {".DS_Store", "Thumbs.db", ".gitkeep"}
IGNORE_SUFFIXES = (".map", ".log", ".py", ".pyc")


def _env(nom):
    v = os.environ.get(nom)
    if not v:
        # On lit .env.local quand il est là : l'ouvrier tourne souvent depuis
        # un terminal où seul le fichier de l'application est renseigné.
        chemin = os.path.join(os.path.dirname(SITE), "console", ".env.local")
        if os.path.exists(chemin):
            for ligne in open(chemin, encoding="utf-8"):
                if ligne.startswith(nom + "="):
                    return ligne.split("=", 1)[1].strip()
    return v


class Seau:
    """La frontière avec le stockage. Une seule, comme partout ailleurs."""

    def __init__(self, url=None, cle=None, seau="sites"):
        self.url = (url or _env("NEXT_PUBLIC_SUPABASE_URL") or "").rstrip("/")
        self.cle = cle or _env("SUPABASE_SERVICE_ROLE_KEY")
        self.seau = seau
        if not self.url or not self.cle:
            sys.exit("NEXT_PUBLIC_SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY "
                     "sont requis pour publier.")

    def _req(self, chemin, methode, corps=None, type_=None, entetes=None):
        req = urllib.request.Request(
            f"{self.url}/storage/v1/{chemin}", data=corps, method=methode,
            headers={"Authorization": f"Bearer {self.cle}", "apikey": self.cle,
                     **({"Content-Type": type_} if type_ else {}),
                     **(entetes or {})})
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()

    def envoyer(self, chemin_distant, octets, type_):
        # `x-upsert` : republier un site doit écraser l'ancien, pas échouer
        # sur « le fichier existe déjà » et laisser la moitié d'une version.
        code, rep = self._req(f"object/{self.seau}/{chemin_distant}", "POST",
                              octets, type_, {"x-upsert": "true"})
        if code >= 300:
            raise RuntimeError(f"{chemin_distant} -> {code} : {rep[:200]!r}")
        return code

    def lien(self, chemin_distant):
        return f"{self.url}/storage/v1/object/public/{self.seau}/{chemin_distant}"

    def relire(self, chemin_distant):
        """Retourne la taille lue à l'adresse PUBLIQUE, ou None."""
        try:
            with urllib.request.urlopen(self.lien(chemin_distant), timeout=45) as r:
                return len(r.read())
        except urllib.error.HTTPError:
            return None


def a_envoyer(racine):
    """Les fichiers à publier, l'index EN DERNIER."""
    tout = []
    for base, _, fichiers in os.walk(racine):
        for f in sorted(fichiers):
            if f in IGNORES or f.endswith(IGNORE_SUFFIXES):
                continue
            plein = os.path.join(base, f)
            tout.append((plein, os.path.relpath(plein, racine).replace(os.sep, "/")))
    # L'index part en dernier : tant qu'il n'est pas là, l'ancienne version
    # reste servie entière plutôt qu'une nouvelle à moitié montée.
    return sorted(tout, key=lambda t: (t[1] == "index.html", t[1]))


def verdict(racine):
    """Le contrôleur a-t-il dit oui ? Sans réponse, on ne publie pas."""
    chemin = os.path.join(racine, ".verdict.json")
    if not os.path.exists(chemin):
        return None
    try:
        return json.load(open(chemin, encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def publier(cle, seau=None, journal=print, forcer=False, version=None):
    racine = os.path.join(SITE, "dist", cle)
    if not os.path.isdir(racine):
        raise RuntimeError(f"dist/{cle}/ n'existe pas — rien à publier")

    v = verdict(racine)
    if not forcer:
        if v is None:
            raise RuntimeError(
                f"dist/{cle}/ n'a pas de verdict du contrôleur.\n"
                "On ne publie pas ce qui n'a pas été contrôlé : c'est la seule\n"
                "opération de la chaîne qu'on ne peut pas défaire.\n"
                "  python3 generateur/chaine.py " + cle)
        if not v.get("conforme"):
            raise RuntimeError(
                f"le contrôleur a REFUSÉ cette page : {v.get('motif', 'sans motif')}")

    seau = seau or Seau()
    fichiers = a_envoyer(racine)
    if not fichiers:
        raise RuntimeError(f"dist/{cle}/ est vide")

    import time
    version = version or time.strftime("%Y%m%d-%H%M%S")
    prefixe = f"{cle}/{version}"

    octets = 0
    for i, (plein, relatif) in enumerate(fichiers, 1):
        with open(plein, "rb") as f:
            donnees = f.read()
        type_ = mimetypes.guess_type(relatif)[0] or "application/octet-stream"
        seau.envoyer(f"{prefixe}/{relatif}", donnees, type_)
        octets += len(donnees)
        if i % 100 == 0 or i == len(fichiers):
            journal(f"  {i}/{len(fichiers)} fichiers · {octets / 1e6:.1f} Mo")

    # LA RELECTURE. Un 200 à l'envoi ne prouve pas que le fichier est lisible
    # à son adresse publique — droits du seau, propagation, nom mal encodé.
    lu = seau.relire(f"{prefixe}/index.html")
    if lu is None:
        raise RuntimeError("l'index a été envoyé mais ne se relit pas à son "
                           "adresse publique — le seau n'est peut-être pas public")
    if lu != os.path.getsize(os.path.join(racine, "index.html")):
        # Un chemin neuf ne devrait jamais rendre autre chose que ce qu'on
        # vient d'y mettre. Si ça arrive, c'est que la version n'est pas
        # neuve — et publier par-dessus une version servie est justement ce
        # qu'on cherche à ne jamais faire.
        raise RuntimeError(f"l'index relu fait {lu} octets, l'envoyé "
                           f"{os.path.getsize(os.path.join(racine, 'index.html'))} — "
                           f"la version « {version} » n'était pas neuve")
    journal(f"  index relu : {lu} octets, version {version}")
    return version


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__.strip())
    cle = sys.argv[1]
    if "essai" in sys.argv[2:]:
        racine = os.path.join(SITE, "dist", cle)
        f = a_envoyer(racine) if os.path.isdir(racine) else []
        v = verdict(racine)
        print(f"dist/{cle}/ : {len(f)} fichiers")
        print(f"verdict     : {v or 'ABSENT — la publication refuserait'}")
        if f:
            print(f"dernier     : {f[-1][1]}  (doit être index.html)")
        return
    v = publier(cle)
    print(f"\npublié sous la version {v}")
    print(f"la page se sert par l'application : /s/{cle}")


if __name__ == "__main__":
    main()
