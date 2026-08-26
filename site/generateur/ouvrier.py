#!/usr/bin/env python3
"""
L'ouvrier : il dépile la file et fait tourner le moteur.

    python3 generateur/ouvrier.py                    tourne jusqu'à extinction
    python3 generateur/ouvrier.py une                prend UNE tâche et sort
    python3 generateur/ouvrier.py essai              éprouve, sans base ni réseau

POURQUOI UN OUVRIER SÉPARÉ, ET PAS DU CODE DANS L'APPLICATION

Le moteur met des minutes : commander six plans de huit secondes, les
mesurer, découper 1152 images, construire la page deux fois, la contrôler sur
cinq écrans dans un vrai navigateur. Aucune requête web ne survit à ça, et un
serveur web qui lance ffmpeg tombe au premier site un peu long.

Et surtout : le moteur est en Python, éprouvé, avec quarante contrôles qui
passent. Le réécrire pour qu'il tienne dans une route web, ce serait repayer
tous les défauts déjà payés.

CE QUI COMPTE ICI, C'EST LA DIFFÉRENCE ENTRE « REFUSÉE » ET « ERREUR »

    refusee : le contrôleur a dit non. La barrière a FONCTIONNÉ.
    erreur  : quelque chose s'est cassé. La barrière n'a rien pu juger.

Les confondre serait la faute la plus coûteuse de tout ce fichier : on
relancerait indéfiniment une tâche que le contrôleur refuse à raison, et on
prendrait un contrôle réussi pour une panne. Une tâche refusée n'est donc
JAMAIS reprise — elle attend qu'un humain corrige le contrat.

CE QUI N'EST PAS ÉPROUVÉ : la connexion à la base. Il n'y avait pas de projet
Supabase à écrire dans l'environnement où ce fichier a été écrit. Le mode
essai fait tourner tout le reste — la prise de tâche, l'aiguillage, la
distinction refus/erreur, le compte rendu — contre une fausse base.
"""
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

ICI = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(ICI)
NOM = os.environ.get("OUVRIER", f"ouvrier-{os.getpid()}")


class Base:
    """La frontière avec Supabase. Une seule, comme partout ailleurs."""

    def prendre(self): raise NotImplementedError
    def finir(self, tache_id, etat, motif=None, journal=None): raise NotImplementedError
    def projet(self, projet_id): raise NotImplementedError
    def dire(self, projet_id, texte, meta=None): raise NotImplementedError
    def publier(self, projet_id, version): raise NotImplementedError


class Postgrest(Base):
    """La vraie. NON ÉPROUVÉE : pas de projet Supabase ici."""

    def __init__(self, url=None, cle=None):
        self.url = (url or os.environ.get("SUPABASE_URL", "")).rstrip("/")
        self.cle = cle or os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
        if not self.url or not self.cle:
            sys.exit("SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY sont requis.\n"
                     "Pour éprouver sans base :  python3 generateur/ouvrier.py essai")

    def _appel(self, chemin, methode="GET", corps=None, entetes=None):
        req = urllib.request.Request(
            f"{self.url}{chemin}",
            data=json.dumps(corps).encode() if corps is not None else None,
            method=methode,
            headers={"apikey": self.cle, "Authorization": f"Bearer {self.cle}",
                     "Content-Type": "application/json", **(entetes or {})})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                brut = r.read().decode()
                return json.loads(brut) if brut.strip() else None
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"{chemin} -> {e.code} : {e.read().decode()[:300]}")

    def prendre(self):
        # `prendre_tache` verrouille avec `for update skip locked` : deux
        # ouvriers qui démarrent ensemble ne prennent pas la même tâche.
        t = self._appel("/rest/v1/rpc/prendre_tache", "POST", {"nom_ouvrier": NOM})
        return t or None

    def finir(self, tache_id, etat, motif=None, journal=None):
        self._appel(f"/rest/v1/taches?id=eq.{tache_id}", "PATCH", {
            "etat": etat, "motif": motif, "journal": journal or [],
            "fini_le": "now()"})

    def projet(self, projet_id):
        r = self._appel(f"/rest/v1/projets?id=eq.{projet_id}&select=*")
        return r[0] if r else None

    def dire(self, projet_id, texte, meta=None):
        self._appel("/rest/v1/messages", "POST", {
            "projet": projet_id, "role": "journal", "texte": texte,
            "meta": meta or {}})

    def publier(self, projet_id, version):
        # La VERSION est ce qui compte : chaque publication va dans un chemin
        # neuf, et c'est cette ligne qui dit lequel est servi.
        self._appel(f"/rest/v1/projets?id=eq.{projet_id}", "PATCH", {
            "version": version, "etat": "publie", "publie_le": "now()"})


class FausseBase(Base):
    """Une base en mémoire. Éprouve tout ce qui n'est pas le réseau."""

    def __init__(self, taches, projets):
        self.file = list(taches)
        self.projets = projets
        self.finies = []
        self.dits = []

    def prendre(self):
        return self.file.pop(0) if self.file else None

    def finir(self, tache_id, etat, motif=None, journal=None):
        self.finies.append({"id": tache_id, "etat": etat, "motif": motif,
                            "journal": journal or []})

    def projet(self, projet_id):
        return self.projets.get(projet_id)

    def dire(self, projet_id, texte, meta=None):
        self.dits.append(texte)

    def publier(self, projet_id, version):
        self.publiees = getattr(self, "publiees", [])
        self.publiees.append((projet_id, version))


# ------------------------------------------------------------- le travail

class Refuse(Exception):
    """Le contrôleur a dit non. Ce n'est PAS une panne."""


def _lancer(cmd, journal, minutes=30):
    """Lance une étape du moteur et retient ce qu'elle a dit."""
    p = subprocess.run(cmd, cwd=SITE, capture_output=True, text=True,
                       timeout=minutes * 60)
    lignes = [l for l in p.stdout.splitlines() if l.strip()]
    journal.extend(lignes[-40:])
    if p.returncode != 0:
        # La chaîne sort en 1 quand le CONTRÔLEUR refuse, et aussi quand
        # quelque chose casse. On les distingue sur ce que la chaîne a
        # imprimé : elle dit « le contrôleur refuse » dans le premier cas,
        # et c'est cette phrase-là qui fait la différence entre « corriger
        # le contrat » et « réparer la machine ».
        sortie = p.stdout + p.stderr
        if "le contrôleur refuse" in sortie or "REFUSÉ" in sortie:
            raise Refuse("\n".join(
                [l for l in lignes if l.strip().startswith("NON")][:8]
                or lignes[-6:]))
        raise RuntimeError((p.stderr or p.stdout)[-900:])
    return lignes


def faire(tache, base, py=sys.executable):
    """Exécute une tâche. Rend (etat, motif, journal)."""
    journal = []
    projet = base.projet(tache["projet"])
    if not projet:
        return "erreur", "projet introuvable", journal
    cle = projet["cle"]
    quoi = tache["quoi"]

    try:
        if quoi == "filmer":
            api = os.environ.get("FOURNISSEUR_VIDEO")
            plans = (tache.get("charge") or {}).get("plans")
            cmd = [py, "generateur/monteuse.py", cle]
            cmd += [f"plans={plans}"] if plans else [
                f"api={api}", f"cle={os.environ.get('FOURNISSEUR_VIDEO_CLE', '')}"]
            _lancer(cmd, journal, minutes=60)

        elif quoi in ("construire", "controler"):
            # `chaine.py` fait déjà construire → mesurer → reconstruire →
            # contrôler, et s'arrête si le contrôleur refuse. On ne refait
            # pas cet enchaînement ici : deux endroits qui l'écrivent
            # finiraient par ne plus le faire dans le même ordre.
            #
            # `page` SAUTE LE RÉENCODAGE quand la pellicule est déjà là. La
            # mise en page change dix fois par jour, le film une fois par
            # site : sans ce drapeau, chaque retouche de texte réencodait
            # 1152 images et prenait plus de dix minutes. Mesuré en essayant.
            cmd = [py, "generateur/chaine.py", cle]
            pellicule = os.path.join(SITE, "assets", "film", cle)
            if os.path.isdir(pellicule) and os.listdir(pellicule):
                cmd.append("page")
                journal.append(f"pellicule déjà là ({len(os.listdir(pellicule))} "
                               f"images) — réencodage sauté")
            _lancer(cmd, journal, minutes=45)

        elif quoi == "publier":
            # LA SEULE OPÉRATION QU'ON NE PEUT PAS DÉFAIRE. publier.py refuse
            # sans le verdict du contrôleur ; on ne le contourne pas d'ici.
            import publier as P
            version = P.publier(cle, journal=journal.append)
            base.publier(tache["projet"], version)
            journal.append(f"publié sous la version {version}")
        else:
            return "erreur", f"tâche inconnue : {quoi}", journal

        return "faite", None, journal

    except Refuse as e:
        # PAS une erreur. La barrière a fonctionné, et la tâche ne doit
        # jamais être reprise toute seule : c'est le contrat qu'il faut
        # corriger, pas la machine qu'il faut relancer.
        return "refusee", str(e), journal
    except subprocess.TimeoutExpired:
        return "erreur", "le moteur a dépassé son temps", journal
    except Exception as e:
        return "erreur", str(e)[-500:], journal


def tour(base):
    """Un passage : prend une tâche s'il y en a une, la fait, la clôt."""
    t = base.prendre()
    if not t:
        return None
    print(f"[{NOM}] tâche {t['id']} · {t['quoi']}")
    debut = time.time()
    etat, motif, journal = faire(t, base)
    base.finir(t["id"], etat, motif, journal)

    marque = {"faite": "ok", "refusee": "REFUSÉ", "erreur": "ERREUR"}[etat]
    print(f"[{NOM}] {marque} en {int(time.time() - debut)} s"
          + (f" — {(motif or '').splitlines()[0][:90]}" if motif else ""))

    if etat == "refusee":
        base.dire(t["projet"],
                  "Le contrôleur refuse la page. Rien n'est publié.\n" + (motif or ""),
                  {"refus": True})
    elif etat == "erreur":
        base.dire(t["projet"], f"L'étape « {t['quoi']} » n'a pas pu aller au bout.",
                  {"erreur": motif})
    return etat


def _essai():
    """Éprouve l'aiguillage et la distinction refus / erreur, sans rien
    d'extérieur. Le point à ne jamais casser : une tâche refusée n'est pas
    une tâche en erreur, et elle ne se reprend pas toute seule."""
    ok = []

    def verifier(titre, cond, detail=""):
        ok.append(bool(cond))
        print(f"  {'ok  ' if cond else 'NON '} {titre}" + (f"  {detail}" if not cond else ""))

    projets = {"p1": {"id": "p1", "cle": "menuiserie", "etat": "construire"}}

    # 1. PUBLIER SANS VERDICT DU CONTRÔLEUR EST REFUSÉ.
    #    C'est la seule opération qu'on ne peut pas défaire : mettre en ligne
    #    une page que personne n'a contrôlée est exactement ce qu'on empêche.
    b = FausseBase([{"id": 1, "projet": "p1", "quoi": "publier", "charge": {}}], projets)
    tour(b)
    verifier("publier sans verdict ne passe pas", b.finies[0]["etat"] == "erreur",
             str(b.finies[0]["etat"]))
    verifier("et le motif dit pourquoi",
             "verdict" in (b.finies[0]["motif"] or "").lower(),
             (b.finies[0]["motif"] or "")[:70])
    verifier("rien n'a été enregistré comme publié",
             not getattr(b, "publiees", []))

    # 2. Un projet absent est une erreur.
    b = FausseBase([{"id": 2, "projet": "inconnu", "quoi": "construire", "charge": {}}], {})
    tour(b)
    verifier("un projet introuvable est une erreur", b.finies[0]["etat"] == "erreur")

    # 3. LE POINT CENTRAL : un refus du contrôleur n'est pas une panne.
    global _lancer
    vrai = _lancer
    try:
        def refuse(cmd, journal, minutes=30):
            journal.append("  NON  série servie « x » — le contrat attend « y »")
            raise Refuse("  NON  série servie « x » — le contrat attend « y »")
        _lancer = refuse
        b = FausseBase([{"id": 3, "projet": "p1", "quoi": "construire", "charge": {}}], projets)
        tour(b)
        verifier("un refus du contrôleur est « refusee », pas « erreur »",
                 b.finies[0]["etat"] == "refusee", str(b.finies[0]["etat"]))
        verifier("le refus est expliqué au client",
                 any("contrôleur refuse" in d for d in b.dits))
        verifier("le motif porte ce que le contrôleur a dit",
                 "série servie" in (b.finies[0]["motif"] or ""))

        def casse(cmd, journal, minutes=30):
            raise RuntimeError("ffmpeg introuvable")
        _lancer = casse
        b = FausseBase([{"id": 4, "projet": "p1", "quoi": "construire", "charge": {}}], projets)
        tour(b)
        verifier("une vraie panne reste « erreur »", b.finies[0]["etat"] == "erreur")

        def marche(cmd, journal, minutes=30):
            journal.append("dist/menuiserie/ est prêt.")
            return journal
        _lancer = marche
        b = FausseBase([{"id": 5, "projet": "p1", "quoi": "construire", "charge": {}}], projets)
        tour(b)
        verifier("une construction réussie est « faite »", b.finies[0]["etat"] == "faite")
        verifier("rien n'est dit au client quand tout va bien", not b.dits)
    finally:
        _lancer = vrai

    # 4. La file vide ne fait rien plutôt que de tourner à vide.
    verifier("une file vide rend None", tour(FausseBase([], projets)) is None)

    print(f"\n{sum(ok)}/{len(ok)} — "
          + ("l'ouvrier tient." if all(ok) else "IL RESTE UN DÉFAUT."))
    return 0 if all(ok) else 1


def main():
    quoi = sys.argv[1] if len(sys.argv) > 1 else ""
    if quoi == "essai":
        sys.exit(_essai())

    base = Postgrest()
    if quoi == "une":
        sys.exit(0 if tour(base) else 0)

    print(f"[{NOM}] en attente de tâches")
    vide = 0
    while True:
        try:
            fait = tour(base)
        except Exception as e:
            # L'ouvrier ne meurt pas d'une base momentanément injoignable :
            # il attend. Mourir ici laisserait la file s'accumuler sans que
            # personne ne le sache.
            print(f"[{NOM}] base injoignable : {e}")
            time.sleep(15)
            continue
        vide = 0 if fait else min(vide + 1, 8)
        time.sleep(1 + vide * 2)


if __name__ == "__main__":
    main()
