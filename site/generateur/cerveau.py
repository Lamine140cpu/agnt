#!/usr/bin/env python3
"""
La frontière avec Claude. Un seul endroit, comme fournisseur.py pour la vidéo.

    from cerveau import Cerveau, Rejeu
    c = Cerveau(cle=...)                  # le vrai
    c = Rejeu("reponses.json")            # rejeu, pour éprouver ce qui suit

POURQUOI UNE FRONTIÈRE ET PAS DES APPELS ÉPARPILLÉS. Deux rôles appellent le
modèle — l'architecte et la cheffe. Si chacun construit sa requête, il y a deux
endroits où se tromper de modèle, deux endroits qui oublient les replis de
refus, deux endroits à corriger le jour où l'API bouge. Et surtout : deux
endroits qu'on ne peut pas éprouver sans clé.

Ici l'appel est écrit une fois, et `Rejeu` permet d'éprouver TOUT CE QUI SUIT
— la construction de la demande, la lecture de la réponse, et surtout les
garde-fous sur ce que le modèle rend — sans jamais toucher au réseau.

CE QUI N'EST PAS ÉPROUVÉ : l'appel lui-même. Il n'y avait pas de clé dans
l'environnement où ce fichier a été écrit. La forme suit la documentation de
l'API en vigueur, mais personne ne l'a vue tourner. Le jour où une clé arrive,
c'est `Claude.demander()` qu'il faut éprouver, et elle seule — sur UNE demande.

TROIS CHOIX QUI COMPTENT POUR UNE CHAÎNE SANS PERSONNE DEVANT L'ÉCRAN :

  - les REPLIS DE REFUS. Un refus de sécurité rend une réponse vide avec un
    code 200. Sans repli, la chaîne s'arrête en silence à trois heures du
    matin. Avec, l'API rejoue la demande sur un autre modèle dans le même
    appel.
  - le FLUX. Une génération longue sans flux tombe en délai d'attente.
  - l'EFFORT. `xhigh` pour l'écriture, `medium` pour le dialogue : le premier
    est hors ligne et la qualité prime, le second a quelqu'un en face.
"""
import json
import os
import sys

ICI = os.path.dirname(os.path.abspath(__file__))

# Les deux rôles, et le modèle de chacun. Écrit ici et nulle part ailleurs.
ROLES = {
    # Écrit les six actes. Hors ligne, personne n'attend, la qualité prime.
    "architecte": {"modele": "claude-fable-5", "effort": "xhigh", "jetons": 16000},
    # Dialogue avec le client. Quelqu'un attend devant l'écran.
    "cheffe":     {"modele": "claude-opus-5",  "effort": "medium", "jetons": 8000},
}


class Refus(Exception):
    """Le modèle n'a pas rendu ce qu'on lui demandait. Jamais silencieux."""


class Cerveau:
    """L'interface. C'est tout ce que l'architecte et la cheffe ont le droit
    de connaître — ni le nom du modèle, ni la forme de la requête."""

    def demander(self, role, systeme, messages, schema=None):
        raise NotImplementedError


class Claude(Cerveau):
    """Le vrai. NON ÉPROUVÉ : aucune clé n'était disponible ici."""

    def __init__(self, cle=None):
        self.cle = cle or os.environ.get("ANTHROPIC_API_KEY")
        if not self.cle:
            raise Refus(
                "pas de clé Claude.\n"
                "  export ANTHROPIC_API_KEY=…\n\n"
                "En attendant, tout ce qui suit l'appel s'éprouve en rejeu :\n"
                "  python3 architecte.py <nom> rejeu=<fichier de réponses>")
        try:
            import anthropic  # noqa: F401
        except ImportError:
            raise Refus("le paquet `anthropic` n'est pas installé :\n"
                        "  pip install anthropic")

    def demander(self, role, systeme, messages, schema=None):
        import anthropic
        r = ROLES[role]
        client = anthropic.Anthropic(api_key=self.cle)

        sortie = {"effort": r["effort"]}
        if schema:
            sortie["format"] = {"type": "json_schema", "schema": schema}

        # Flux : sans lui, une écriture longue tombe en délai d'attente.
        # Replis : sans eux, un refus arrête la chaîne en silence.
        with client.beta.messages.stream(
            model=r["modele"],
            max_tokens=r["jetons"],
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            system=systeme,
            output_config=sortie,
            messages=messages,
        ) as flux:
            rep = flux.get_final_message()

        if rep.stop_reason == "refusal":
            motif = getattr(rep.stop_details, "category", None)
            raise Refus(f"le modèle a refusé la demande (catégorie « {motif} »), "
                        f"et le repli aussi.")
        if rep.stop_reason == "max_tokens":
            raise Refus(f"réponse coupée à {r['jetons']} jetons — la demande "
                        f"est trop grosse, ou le plafond trop bas.")

        texte = "".join(b.text for b in rep.content if b.type == "text")
        if not schema:
            return texte
        try:
            return json.loads(texte)
        except json.JSONDecodeError as e:
            raise Refus(f"réponse illisible en JSON ({e}) : {texte[:300]}")


class Rejeu(Cerveau):
    """Rend des réponses écrites d'avance, pour éprouver ce qui vient après.

    Le fichier est une liste : une entrée par appel, dans l'ordre. Ça permet
    d'éprouver les garde-fous en leur donnant EXPRÈS de mauvaises réponses —
    un texte qui invente un numéro de téléphone, cinq actes au lieu de six.
    C'est le seul moyen de savoir que les garde-fous mordent.
    """

    def __init__(self, source):
        if isinstance(source, (list, dict)):
            self.reponses = source if isinstance(source, list) else [source]
        else:
            with open(source, encoding="utf-8") as f:
                self.reponses = json.load(f)
            if not isinstance(self.reponses, list):
                self.reponses = [self.reponses]
        self.rendu = 0
        self.demandes = []

    def demander(self, role, systeme, messages, schema=None):
        self.demandes.append({"role": role, "systeme": systeme,
                              "messages": messages})
        if self.rendu >= len(self.reponses):
            raise Refus(f"le rejeu n'a que {len(self.reponses)} réponses, "
                        f"on en demande une {self.rendu + 1}e")
        r = self.reponses[self.rendu]
        self.rendu += 1
        return r


def ouvrir(rejeu=None, cle=None):
    return Rejeu(rejeu) if rejeu else Claude(cle)


if __name__ == "__main__":
    print(__doc__.strip())
    print("\nles rôles :")
    for nom, r in ROLES.items():
        print(f"  {nom:12s} {r['modele']:16s} effort {r['effort']}")
    sys.exit(0)
