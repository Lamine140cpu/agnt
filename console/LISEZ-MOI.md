# La console Ultra Motion

L'application. Le moteur, lui, reste en Python dans `../site/generateur/` :
il porte quarante contrôles éprouvés, la boucle de reprise et le contrôleur.
Le réécrire en TypeScript reviendrait à repayer tous les défauts déjà payés.

```
console/          Next.js 16 — la console (chat + projection)
supabase/         le schéma et ses politiques de ligne
site/generateur/  LE MOTEUR, inchangé, plus l'ouvrier qui dépile la file
```

## Les frontières

Quatre, et chacune a un mode rejeu pour être éprouvée sans clé :

| frontière | fichier | éprouvée ? |
|---|---|---|
| Claude | `lib/cheffe.ts` | non — pas de clé |
| registre des entreprises | `lib/registre.ts` | non — domaine refusé par le proxy |
| Stripe | `lib/paiement.ts` | non — pas de clé |
| modèle vidéo | `../site/generateur/fournisseur.py` | mécanique oui, descripteurs non |

## Le garde-fou des faits est un jumeau

La même règle tourne en Python (`architecte.py`) et en TypeScript
(`lib/contrat.ts`). Elle est en double parce que la cheffe écrit en DIRECT
dans le chat : filtrer seulement au moment de construire laisserait passer à
l'écran une phrase que le moteur refuserait ensuite.

Deux implémentations de la même règle divergent toujours — sauf si elles
répondent au même questionnaire :

    site/generateur/vecteurs-faits.json

Ajouter un cas là-bas le rend obligatoire des deux côtés.

```bash
npm run verif                          # le jumeau TypeScript
python3 ../site/generateur/architecte.py essai   # le jumeau Python
```

## Ce qu'il faut éprouver le jour où les clés arrivent

Dans cet ordre, et chacune sur UN essai avant d'en faire quoi que ce soit :

1. le crochet Stripe, AVANT toute mise en production — un plan qui ne
   redescend jamais est un client qui garde un accès qu'il ne paye plus ;
2. l'appel Claude, et notamment les replis de refus : le SDK installé ne
   connaît pas encore le champ, il est passé par-dessus les types ;
3. le registre, sur un seul SIREN, en regardant les noms de champs ;
4. le modèle vidéo, sur UN plan.
