#!/usr/bin/env python3
"""
L'architecte : écrit les six actes et les six sujets de plan, et RIEN D'AUTRE.

    python3 architecte.py <nom>                        écrit (demande une clé)
    python3 architecte.py <nom> rejeu=<fichier.json>   rejoue une réponse
    python3 architecte.py essai                        éprouve le garde-fou

CE QUI EST DANGEREUX ICI, ET POURQUOI CE FICHIER EXISTE

Un modèle à qui on demande d'écrire la page d'une entreprise de transport
écrira « vingt ans d'expérience », « une flotte de trente véhicules »,
« certifiés ISO 9001 » et un numéro de téléphone. Tout sera crédible. Tout
sera faux. Et plus le modèle est bon, plus ce sera crédible.

Ce n'est pas un défaut de raisonnement, c'est le métier du modèle : il complète.
On ne le corrige donc pas en le lui demandant gentiment dans la consigne — on
le lui demande AUSSI, mais surtout on VÉRIFIE ce qu'il rend.

    Tout ce qui ressemble à un fait dans le texte produit doit se retrouver
    dans les faits déclarés du manifeste. Sinon on refuse.

Chiffres, dates, quantités, durées, courriels, téléphones, identifiants,
certifications : chacun est cherché dans les faits déclarés, et un seul
intrus fait refuser la page entière. C'est brutal, et c'est voulu — un site
de client qui annonce une certification qu'il n'a pas, c'est son problème à
lui, pas une coquille.

LE GARDE-FOU EST ÉPROUVÉ, et dans les deux sens : `architecte.py essai` lui
donne exprès des textes qui inventent, et vérifie qu'il mord ; puis un texte
honnête, et vérifie qu'il laisse passer. Un garde-fou qu'on n'a jamais vu
refuser n'est pas un garde-fou.
"""
import json
import os
import re
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(ICI)
sys.path.insert(0, ICI)
from manifeste import ecrire  # noqa: E402


class Refus(Exception):
    pass


# ------------------------------------------------------- ce qui est un fait

# Chaque motif porte son nom, parce qu'un refus doit dire QUOI il a trouvé.
# Ils sont volontairement larges : un faux positif coûte une relecture, un
# faux négatif met une contrevérité en ligne sur le site d'un client.
MOTIFS = [
    ("un courriel",        r"[\w.+-]+@[\w-]+\.[\w.]+"),
    ("un site",            r"\b(?:https?://|www\.)\S+"),
    ("un téléphone",       r"(?:\+33|\b0)[\s.\-]?[1-9](?:[\s.\-]?\d{2}){4}\b"),
    ("un identifiant",     r"\b\d[\d\s.\-]{7,}\d\b"),
    ("une année",          r"\b(?:19|20)\d{2}\b"),
    ("une certification",  r"\b(?:ISO|NF|AFNOR|QUALIMAT|IFS|BRC|OEA)[\s\-]?\d*\b"),
    # Le séparateur de milliers fait partie du nombre. Sans lui, « 1 152 »
    # se lisait « 1 » puis « 152 », et aucun des deux ne se retrouvait dans
    # un manifeste qui déclare pourtant 1152.
    ("un chiffre",         r"\b\d{1,3}(?:[\s  ]\d{3})+\b"
                           r"|\b\d+(?:[.,]\d+)?\s*(?:%|€|km|kg|t\b|m²|h\b|/\d+)?"),
]

# Les nombres écrits en toutes lettres comptent autant : « une vingtaine de
# camions » est exactement le fait qu'on refuse d'inventer.
#
# « un » et « une » ne sont PAS dans cette liste, et c'est délibéré : ce sont
# d'abord des articles. « un atelier » n'avance rien, et le garde-fou qui le
# refusait rendait impossible d'écrire une phrase française — un garde-fou
# qu'on ne peut pas satisfaire finit débranché. Ils reviennent juste après,
# mais seulement devant une durée, où ils comptent vraiment.
_DENOMBRABLES = (r"ans?|années?|camions?|véhicules?|poids\s+lourds?|salariés?|"
                 r"employés?|collaborateurs?|chauffeurs?|conducteurs?|clients?|"
                 r"agences?|sites?|entrepôts?|générations?|tonnes?|hectares?|"
                 r"artisans?|compagnons?|ateliers?")
LETTRES = (r"\b(?:deux|trois|quatre|cinq|six|sept|huit|neuf|dix|onze|douze|"
           r"quinze|vingt|trente|quarante|cinquante|soixante|cent|mille|"
           r"dizaine|douzaine|vingtaine|trentaine|quarantaine|cinquantaine|"
           r"centaine|millier)s?\s+"
           r"(?:de\s+|d['’])?"
           r"(?:" + _DENOMBRABLES + r")\b")

# « un an de garantie », « une génération » : au singulier, ces tournures-là
# avancent bien une ancienneté. On les reprend, mais seulement devant une
# durée — jamais devant un lieu ou un objet.
LETTRES_DUREE = (r"\b(?:un|une)\s+(?:demi-)?"
                 r"(?:an|année|génération|siècle|décennie)\b")

# UN NOMBRE NU NE SE JUGE PAS, SON UNITÉ SI. « 45 chauffeurs » passait, parce
# que 45 figure bien dans un fait déclaré — le numéro de rue du siège, « 45 rue
# Jean Charcot ». Comparer le nombre seul ne pouvait pas les distinguer.
# On cherche donc le nombre AVEC ce qu'il compte, et c'est cette expression
# entière qu'on va chercher dans les faits : « 45 rue » y est, « 45 chauffeurs »
# n'y est pas.
# UNE ANNÉE N'EST PAS UN COMPTE. « © 2026 Atelier Martin » se lisait
# « 2026 ateliers » — un millésime suivi du nom de la marque. Les années
# sont donc exclues ici ; elles restent jugées par le motif « une année ».
# Angle mort assumé : « 1998 clients » passerait si 1998 était déjà déclaré
# comme date de création. Un faux positif sur chaque bas de page ferait
# débrancher le garde-fou, ce qui coûterait bien plus cher.
MOTIFS.append(("une quantité",
               r"\b(?!(?:19|20)\d{2}\b)\d+\s+(?:de\s+|d['’])?(?:"
               + _DENOMBRABLES + r")\b"))

# Ce qui ressemble à un chiffre sans en être un. Sans cette liste, le
# garde-fou refuserait les tournures ordinaires du français et personne ne
# le laisserait branché.
INNOCENTS = re.compile(
    r"^(?:un|une|des|de|d|le|la|les|deux\s+lignes?)$", re.I)


def _sans_accents_min(s):
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", s.lower())
                   if unicodedata.category(c) != "Mn")


def faits_declares(m):
    """Tout ce que le manifeste autorise à écrire. Rien de plus.

    Une valeur nulle n'entre pas : un fait sans source est une question
    ouverte, pas une permission.

    On ratisse TOUT le manifeste, pas seulement `client.faits`. La règle du
    dépôt est que chaque valeur porte son origine — `{valeur, origine}` — et
    c'est cela, la déclaration. Le site de démonstration l'a montré : il parle
    de sa propre fabrication (1 152 images, 33 px par image), des chiffres
    parfaitement sourcés mais rangés sous `film`. Ne lire que `client.faits`
    les faisait passer pour inventés.
    """
    # L'année en cours n'est pas un fait sur le client : c'est la mention de
    # copyright du bas de page. La refuser obligerait à la déclarer dans le
    # manifeste de chaque site, et à la corriger le 1er janvier — ce qui est
    # justement le genre de constante qui se périme en silence.
    import datetime
    permis = {str(datetime.date.today().year)}
    for f in m.get("client", {}).get("faits", []):
        v = f.get("valeur")
        if v is None:
            continue
        permis.add(_sans_accents_min(str(v)))
    for cle in ("marque", "titre", "site"):
        v = m.get(cle) or m.get("page", {}).get(cle)
        if v:
            permis.add(_sans_accents_min(str(v)))

    def ratisser(n):
        if isinstance(n, dict):
            if "valeur" in n and "origine" in n and n["valeur"] is not None:
                permis.add(_sans_accents_min(str(n["valeur"])))
            for k, v in n.items():
                # `_produit` est écrit par la monteuse d'après le disque :
                # c'est de la mesure, au même titre qu'une origine déclarée.
                if k == "_produit":
                    for w in v.values():
                        if isinstance(w, (int, float, str)):
                            permis.add(_sans_accents_min(str(w)))
                else:
                    ratisser(v)
        elif isinstance(n, list):
            for v in n:
                ratisser(v)

    ratisser(m)
    return permis


def _autorise(trouve, permis):
    """Un fait trouvé est autorisé s'il apparaît dans un fait déclaré.

    On compare sans accents, sans casse et sans séparateurs : un téléphone
    déclaré « 03 20 45 67 89 » doit couvrir « 03.20.45.67.89 ».
    """
    t = _sans_accents_min(trouve).strip()
    if not t or INNOCENTS.match(t):
        return True
    nu = re.sub(r"[^\w]", "", t)
    for p in permis:
        if t in p:
            return True
        if nu and nu in re.sub(r"[^\w]", "", p):
            return True
    return False


def inventions(texte, permis):
    """Les faits présents dans le texte et absents des faits déclarés.

    Rend une liste de (quoi, extrait). Vide = le texte n'avance rien qu'on
    ne puisse justifier.
    """
    trouves = []
    for quoi, motif in MOTIFS:
        for mo in re.finditer(motif, texte, re.I):
            brut = mo.group(0).strip()
            if not _autorise(brut, permis):
                trouves.append((quoi, brut))
    for motif, quoi in ((LETTRES, "une quantité"), (LETTRES_DUREE, "une durée")):
        for mo in re.finditer(motif, texte, re.I):
            if not _autorise(mo.group(0), permis):
                trouves.append((quoi, mo.group(0).strip()))
    # Un même intrus répété ne compte qu'une fois.
    vus, sortie = set(), []
    for quoi, brut in trouves:
        cle = _sans_accents_min(brut)
        if cle not in vus:
            vus.add(cle)
            sortie.append((quoi, brut))
    return sortie


# ---------------------------------------------------------- ce qu'on demande

CHAMPS = ("titre1", "titre2", "cibles1", "cibles2", "corps", "offre")

SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["actes", "sujets"],
    "properties": {
        "actes": {
            "type": "array", "minItems": 6, "maxItems": 6,
            "items": {
                "type": "object", "additionalProperties": False,
                "required": list(CHAMPS),
                "properties": {c: {"type": "string"} for c in CHAMPS},
            },
        },
        "sujets": {
            "type": "array", "minItems": 6, "maxItems": 6,
            "items": {"type": "string"},
        },
    },
}

CONSIGNE = """Tu écris les six actes de la page d'accueil d'un site, et les six
sujets des plans du film qui défile derrière.

LA RÈGLE QUI PASSE AVANT TOUTES LES AUTRES

N'écris AUCUN fait sur l'entreprise qui ne soit pas dans la liste ci-dessous.
Pas d'ancienneté, pas de nombre de véhicules ni de salariés, pas de
certification, pas de zone géographique, pas d'horaires, pas de téléphone,
pas de date de création. Rien.

Ce n'est pas une préférence de style : un contrôle automatique compare ton
texte à la liste des faits vérifiés et REFUSE la page entière s'il trouve un
chiffre, une date ou une quantité qui n'y figure pas. Un site qui annonce une
certification que l'entreprise n'a pas l'expose à des ennuis réels.

Tu peux parler du métier, du geste, de la matière, de ce que le client
ressent. Tout cela est vrai sans avoir besoin d'être vérifié.

LA FORME

Six actes. Chacun tient en :
  titre1, titre2  — le titre sur deux lignes, trois à cinq mots par ligne
  cibles1, cibles2 — à qui l'acte s'adresse, deux lignes courtes
  corps            — une à deux phrases, qui tiennent debout seules :
                     le visiteur en lira peut-être une sur six
  offre            — ce que ça promet, quatre mots au plus

Six sujets de plan, un par acte : une phrase décrivant ce que la caméra voit.
Pas de texte à l'image, pas de logo, pas de visage en gros plan. Ce sont des
lieux, des matières et des gestes."""


def demande(m):
    faits = [f for f in m.get("client", {}).get("faits", [])
             if f.get("valeur") is not None]
    ouvertes = [f["cle"] for f in m.get("client", {}).get("faits", [])
                if f.get("valeur") is None]
    lignes = [f"  - {f['cle']} : {f['valeur']}" for f in faits] or \
             ["  (aucun — n'écris donc aucun fait chiffré, pas un seul)"]
    contexte = [f"Le site : {m.get('site', '?')}", "", "FAITS VÉRIFIÉS :"] + lignes
    if ouvertes:
        contexte += ["", "FAITS ABSENTS — le client ne les a pas encore donnés.",
                     "Ne les invente pas, n'y fais pas allusion :",
                     "  " + ", ".join(ouvertes)]
    if m.get("_"):
        contexte += ["", "Nature du site : " + m["_"]]
    return CONSIGNE, [{"role": "user", "content": "\n".join(contexte)}]


def verifier(rep, m):
    """Le garde-fou. Structure d'abord, faits ensuite. Refuse, ne corrige pas.

    Corriger serait pire : on ne saurait plus ce que le modèle a vraiment
    rendu, et le contrôle deviendrait une politesse.
    """
    if not isinstance(rep, dict):
        raise Refus(f"réponse de type {type(rep).__name__}, attendu un objet")
    for cle, n in (("actes", 6), ("sujets", 6)):
        if len(rep.get(cle) or []) != n:
            raise Refus(f"{n} « {cle} » attendus, "
                        f"{len(rep.get(cle) or [])} rendus")
    for i, a in enumerate(rep["actes"], 1):
        manquants = [c for c in CHAMPS if not (a.get(c) or "").strip()]
        if manquants:
            raise Refus(f"acte {i} : {', '.join(manquants)} vide(s)")

    permis = faits_declares(m)
    texte = "\n".join(
        [v for a in rep["actes"] for v in a.values()] + list(rep["sujets"]))
    trouves = inventions(texte, permis)
    if trouves:
        lignes = "\n".join(f"    {quoi} : « {brut} »" for quoi, brut in trouves)
        raise Refus(
            f"{len(trouves)} fait(s) inventé(s) — la page est refusée :\n"
            f"{lignes}\n\n"
            "Aucun de ces éléments ne figure dans les faits vérifiés du\n"
            "manifeste. Deux issues, jamais une troisième :\n"
            "  - le fait est vrai : le faire confirmer par le client, l'ajouter\n"
            "    au manifeste avec sa source, et relancer ;\n"
            "  - le fait est inventé : relancer, il ne sera pas le même.")
    return rep


# ------------------------------------------------------------------ l'écriture

def poser(m, rep):
    """Range les actes et les sujets dans le manifeste, avec leur origine."""
    m["page"]["actes"] = rep["actes"]
    m["film"]["sujets"] = rep["sujets"]
    m["page"]["_actes"] = ("Écrits par l'architecte, puis passés au garde-fou "
                           "des faits : tout chiffre, date ou quantité présent "
                           "ici se retrouve dans client.faits.")
    return m


def essai():
    """Éprouve le garde-fou sur les vecteurs PARTAGÉS avec l'application.

    Les cas ne sont pas écrits ici : ils vivent dans vecteurs-faits.json, et
    console/lib/contrat.ts répond au même questionnaire. Deux codes qui jugent
    la même chose divergent toujours — sauf s'ils passent le même examen. Une
    divergence voudrait dire qu'on affiche dans le chat une phrase que le
    moteur refusera ensuite, et l'utilisateur aurait raison de n'y plus rien
    comprendre.
    """
    chemin = os.path.join(ICI, "vecteurs-faits.json")
    if not os.path.exists(chemin):
        sys.exit(f"{chemin} est introuvable — c'est le questionnaire commun")
    v = json.load(open(chemin, encoding="utf-8"))
    m = {"site": "essai", "client": {"faits": v["faits"]}}
    permis = faits_declares(m)
    ok = []

    largeur = max(len(c["quoi"]) for c in v["cas"])
    for c in v["cas"]:
        t = inventions(c["texte"], permis)
        bon = bool(t) == c["mord"]
        if bon and c.get("extrait"):
            bon = any(c["extrait"] in b for _, b in t)
        ok.append(bon)
        verbe = "refuse " if c["mord"] else "laisse "
        print(f"  {'ok  ' if bon else 'NON '} {verbe} {c['quoi']:<{largeur}}")
        if not bon:
            detail = ", ".join(f"{q} : « {b} »" for q, b in t) or "rien"
            print(f"       « {c['texte'][:70]} »")
            print(f"       trouvé : {detail}")

    print("\n  LA VÉRIFICATION COMPLÈTE")
    bon = {"actes": [{c: "Le bois" if c != "corps" else
                      "On écoute la matière avant de la couper."
                      for c in CHAMPS} for _ in range(6)],
           "sujets": ["un atelier de menuiserie"] * 6}
    try:
        verifier(bon, m)
        ok.append(True); print("  ok   une réponse honnête et complète passe")
    except Refus as e:
        ok.append(False); print(f"  NON  une réponse honnête est refusée : {e}")

    for titre, casse in (
        ("cinq actes au lieu de six",
         {"actes": bon["actes"][:5], "sujets": bon["sujets"]}),
        ("un acte au champ vide",
         {"actes": [dict(bon["actes"][0], offre="  ")] + bon["actes"][1:],
          "sujets": bon["sujets"]}),
        ("un acte qui invente",
         {"actes": [dict(bon["actes"][0], corps="Vingt ans de métier.")]
          + bon["actes"][1:], "sujets": bon["sujets"]}),
    ):
        try:
            verifier(casse, m)
            ok.append(False); print(f"  NON  {titre} : c'est passé")
        except Refus:
            ok.append(True); print(f"  ok   {titre} est refusé")

    print(f"\n{sum(ok)}/{len(ok)} — "
          + ("le garde-fou mord." if all(ok) else "IL RESTE UN DÉFAUT."))
    return 0 if all(ok) else 1


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__.strip())
    if sys.argv[1] == "essai":
        sys.exit(essai())

    nom = sys.argv[1]
    rejeu = None
    for a in sys.argv[2:]:
        if a.startswith("rejeu="):
            rejeu = a.split("=", 1)[1]
    contrat = os.path.join(ICI, f"manifeste-{nom}.json")
    if not os.path.exists(contrat):
        sys.exit(f"{contrat} est introuvable — lancer d'abord nouveau.py")
    m = json.load(open(contrat, encoding="utf-8"))

    from cerveau import ouvrir, Refus as RefusCerveau
    try:
        c = ouvrir(rejeu=rejeu)
        systeme, messages = demande(m)
        rep = c.demander("architecte", systeme, messages, schema=SCHEMA)
    except RefusCerveau as e:
        sys.exit(f"\n{e}")

    try:
        verifier(rep, m)
    except Refus as e:
        print(f"\nREFUSÉ\n\n{e}")
        sys.exit(1)

    ecrire(poser(m, rep), contrat)
    print(f"six actes et six sujets écrits dans manifeste-{nom}.json")
    for i, a in enumerate(rep["actes"], 1):
        print(f"  {i}. {a['titre1']} {a['titre2']}")
    print(f"\nensuite :  python3 generateur/chaine.py {nom}")


if __name__ == "__main__":
    main()
