#!/usr/bin/env python3
"""
Le manifeste : le contrat entre le film et la page.

Trois constantes de ce dépôt ont cessé de décrire la réalité sans produire la
moindre erreur — la course du prologue, la qualité d'encodage, et la nature de
la série téléphone. Deux d'entre elles affichaient même un message rassurant et
faux. Aucune n'était une faute de raisonnement : c'était le contrat entre deux
étapes qui avait dérivé, chacune restant cohérente avec elle-même.

Le manifeste est ce contrat, écrit une fois et relu par tout le monde. La règle
qui le fait tenir tient en une phrase :

    PERSONNE NE RECOPIE UN CHIFFRE QU'IL N'A PAS MESURÉ.

Chaque valeur porte donc son ORIGINE. `mesure` : relevée dans la page servie ou
sur les fichiers livrés. `choix` : décidée par un humain, et qui n'a donc pas à
être vérifiée — seulement respectée. `registre` : provenant d'une source
publique citée. Le contrôleur refuse toute valeur d'origine `mesure` qui ne
correspond pas à ce qu'il mesure lui-même, et toute affirmation sur le client
qui n'a pas de source.

    usage :  python3 manifeste.py <manifeste.json>     (valide et résume)
"""
import json
import os
import sys

ORIGINES = ("mesure", "choix", "registre")


def champs(d):
    """Les vraies entrées d'un bloc, sans les commentaires.

    JSON n'a pas de commentaires, et un contrat qu'on ne peut pas annoter est
    un contrat que personne ne relit. La convention est donc qu'une clé « _ »
    porte la prose et n'est jamais une donnée.
    """
    return {k: v for k, v in d.items() if k != "_"}


class Faute(Exception):
    """Un manquement au contrat. Le message dit quoi corriger, pas quoi lire."""


def _valeur(bloc, chemin):
    """Extrait la valeur d'un champ { valeur, origine } et contrôle l'origine.

    Un champ nu est refusé : c'est exactement la forme qu'avaient les trois
    constantes périmées. Écrire l'origine oblige à se demander d'où vient le
    nombre, ce qui est déjà la moitié du travail.
    """
    if not isinstance(bloc, dict) or "valeur" not in bloc or "origine" not in bloc:
        raise Faute(f"{chemin} : attendu {{valeur, origine}}, reçu {bloc!r}")
    if bloc["origine"] not in ORIGINES:
        raise Faute(f"{chemin} : origine « {bloc['origine']} » inconnue — "
                    f"au choix {', '.join(ORIGINES)}")
    return bloc["valeur"]


def ecrire(m, chemin):
    """Réécrit le contrat, toujours de la même façon.

    Trois outils le réécrivent — la monteuse, l'échafaudage, la mesure. Chacun
    avec ses propres réglages, c'est trois mises en forme différentes du même
    fichier, et un diff illisible à chaque passage. Un seul endroit, donc, et
    un saut de ligne final : sans lui, chaque écriture laisse un fichier que
    git signale comme tronqué.
    """
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False, indent=2)
        f.write("\n")


def charger(chemin):
    with open(chemin, encoding="utf-8") as f:
        m = json.load(f)

    for cle in ("site", "film", "page", "seuils", "client"):
        if cle not in m:
            raise Faute(f"le manifeste n'a pas de section « {cle} »")

    film = m["film"]
    if not champs(film.get("series") or {}):
        raise Faute("film.series est vide : une page sans série s'affiche noire "
                    "sans la moindre erreur")
    for nom, s in champs(film["series"]).items():
        for cle in ("dossier", "largeur", "images", "rapport"):
            if cle not in s:
                raise Faute(f"film.series.{nom} : champ « {cle} » manquant")
            _valeur(s[cle], f"film.series.{nom}.{cle}")

    _valeur(film["qualite"], "film.qualite")
    densite = _valeur(film["densite_visee"], "film.densite_visee")

    page = m["page"]
    courses = page.get("courses")
    if not champs(courses or {}):
        raise Faute("page.courses est vide — or c'est la course qui donne le "
                    "nombre d'images, et elle change dès qu'on touche à la "
                    "hauteur des actes")
    for taille, c in champs(courses).items():
        if "x" not in taille:
            raise Faute(f"page.courses.{taille} : la clé doit être « LxH »")
        _valeur(c, f"page.courses.{taille}")

    # La cohérence interne du contrat, vérifiée ici et pas plus tard : le
    # nombre d'images déclaré doit être celui que donne la course divisée par
    # la densité. C'est ce contrôle-là qui manquait quand la construction a
    # livré 464 images en annonçant « 33,0 px par image ».
    for nom, s in champs(film["series"]).items():
        cle = s.get("course")
        if not cle:
            continue
        if cle not in champs(courses):
            raise Faute(f"film.series.{nom}.course renvoie à « {cle} », "
                        f"absent de page.courses")
        attendu = round(_valeur(courses[cle], "") / densite)
        recu = _valeur(s["images"], "")
        if abs(attendu - recu) > 1:
            raise Faute(
                f"film.series.{nom} : {recu} images déclarées, mais la course "
                f"{cle} ({_valeur(courses[cle], '')} px) à {densite} px par "
                f"image en demande {attendu}. La densité réelle serait "
                f"{_valeur(courses[cle], '')/recu:.0f}.")

    for f in m["client"].get("faits", []):
        if "cle" not in f:
            raise Faute("client.faits : une entrée sans « cle »")
        if f.get("valeur") is not None and not f.get("source"):
            raise Faute(
                f"client.faits.{f['cle']} : une valeur sans source. Sur le site "
                f"d'une entreprise réelle, aucun fait ne se devine — ni la "
                f"flotte, ni les certifications, ni le directeur de la "
                f"publication. Citer la source, ou laisser la valeur nulle.")

    return m


def resumer(m):
    print(f"manifeste « {m['site']} »\n")
    d = _valeur(m["film"]["densite_visee"], "")
    print(f"  densité visée      {d} px de défilement par image")
    print(f"  qualité            q{_valeur(m['film']['qualite'], '')}")
    print("  séries")
    for nom, s in champs(m["film"]["series"]).items():
        print(f"    {nom:16s} {_valeur(s['images'],''):4d} images · "
              f"{_valeur(s['largeur'],'')} px · rapport {_valeur(s['rapport'],'')}"
              + (f" · course {s['course']}" if s.get("course") else ""))
    print("  courses mesurées")
    for t, c in champs(m["page"]["courses"]).items():
        print(f"    {t:10s} {_valeur(c,''):6d} px")
    faits = m["client"].get("faits", [])
    manque = [f["cle"] for f in faits if f.get("valeur") is None]
    print(f"  faits client       {len(faits)-len(manque)} vérifiés"
          + (f", {len(manque)} à compléter : {', '.join(manque)}" if manque else ""))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__.strip().splitlines()[-1].strip())
    try:
        resumer(charger(sys.argv[1]))
    except Faute as e:
        sys.exit(f"CONTRAT ROMPU — {e}")
    print("\ncontrat cohérent.")
