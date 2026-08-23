# Le générateur — trois rôles, un contrat, un contrôleur

## Pourquoi ce n'est pas « trois IA qui se parlent »

Les défauts trouvés dans ce projet n'étaient **pas des erreurs de
raisonnement**. C'étaient des constantes qui avaient cessé de décrire la
réalité, chacune restant parfaitement cohérente avec elle-même :

| Constante | Écrite | Réelle | Ce que ça donnait |
|---|---|---|---|
| la course du prologue | 15 300 px | 26 100 px | 464 images au lieu de 791, densité 56 au lieu de 33 |
| la qualité d'encodage | q55 par défaut | q45 en production | pellicule deux tiers plus lourde au premier qui construit sans drapeau |
| la série téléphone | « un vrai montage » | un recadrage centré | le cadrage qu'on croyait corrigé et qui ne l'était pas |
| le compte d'images par série | 527 et 1152 | 791 et 527 | 404 en rafale et film figé au milieu du prologue |

Aucune n'a produit d'erreur. **Deux ont produit un message rassurant et faux.**
La dernière a été trouvée par le contrôleur écrit ici, une heure après avoir été
introduite — par le correctif d'une des trois autres.

Une intelligence qui re-raisonne à chaque fois reproduira cette dérive,
différemment à chaque exécution. Ce qu'il faut n'est pas plus d'intelligence,
c'est **un contrat écrit et un contrôle qui compte**.

## La règle

> **Personne ne recopie un chiffre qu'il n'a pas mesuré.**

Chaque valeur du manifeste porte son origine — `mesure`, `choix` ou
`registre` — et le contrôleur ne vérifie que les mesures. Il ne discute pas les
choix : ce sont ceux d'un humain, ils n'ont qu'à être respectés.

## Les quatre rôles

**1. La cheffe d'orchestre** *(intelligence artificielle)*
Parle à l'utilisateur et **détient le manifeste**. C'est là son vrai métier :
pas relayer de la prose, tenir le contrat. Les décisions qui font marcher ce
type de site sont numériques — 33 px par image, plafond de densité de pixels,
64 % de hauteur de toile, rapports de contraste. Une cheffe qui transmet des
phrases les perd toutes.
Elle n'écrit **jamais** un fait sur le client sans sa source.

**2. La monteuse** *(intelligence artificielle + chaîne déterministe)*
Lit `film` dans le manifeste, produit la séquence, **réécrit ce qu'elle a
réellement produit**.
Avertissement : une IA ne génère pas 1152 images cohérentes. Le film d'ici
vient de clips vidéo passés à ffmpeg. **Cette étape-là est déterministe et ne
doit pas être confiée à un modèle** — sinon la 400ᵉ image ne ressemble plus à
la 399ᵉ.

**3. L'architecte** *(intelligence artificielle)*
Lit le manifeste, construit la page, **mesure la course dans la page servie**
et la réécrit. Ne déduit jamais un nombre d'images d'une constante : il le
calcule à partir de la course qu'il vient de mesurer.

**4. Le contrôleur** *(pas une intelligence artificielle, et ça compte)*
Mesure et refuse. Un contrôle qui raisonne peut se laisser convaincre ; un
contrôle qui compare des nombres, non.

## Les fichiers

```
manifeste.py              le contrat : structure, origines, cohérence interne
manifeste-transgold.json  un contrat réel, rempli, avec ses sept questions ouvertes
mesures.mjs               les relevés dans la page SERVIE (navigateur)
controleur.py             le verdict : contrat + fichiers + page. Sort en 1 si ça casse.
```

## Usage

```bash
python3 manifeste.py manifeste-transgold.json          # valide et résume
python3 controleur.py manifeste-transgold.json ../dist/transgold
```

Le contrôleur sert lui-même le dossier sur un port libre — jamais en `file://`,
où les chemins relatifs, le typage MIME et les requêtes ne se comportent pas
comme en ligne.

## Ce qu'il vérifie

**Le contrat** — cohérence interne. Le nombre d'images déclaré doit être celui
que donne la course divisée par la densité visée. C'est ce contrôle qui
manquait le jour où la construction a livré 464 images en annonçant
« 33,0 px par image ».

**Les fichiers** — compte par série, **numérotation continue** (un trou laisse
le film figé), largeur, rapport, poids du logo.

**Les faits du client** — chaque valeur a une source ; les valeurs nulles sont
listées comme questions ouvertes, pas comblées au jugé ; les identifiants du
registre sont retrouvés tels quels dans la page.

**La page servie**, à chaque taille d'écran, **densité de pixels comprise** —
`390x844@3` et non `390x844` : à densité 1, l'agrandissement de toile ne se
produit pas et le contrôle qui coûte le plus cher ne mordrait sur rien.

- aucune erreur JavaScript
- débit en **médiane de trois passages** (une lecture isolée varie de 45 à 60)
- aucun débordement horizontal
- aucune image réclamée et absente
- aucun intitulé de menu tronqué, aucun lien resté bleu
- aucune ancre sous la barre d'en-tête
- la course mesurée correspond au contrat
- la **densité réelle** subie par le visiteur, pas celle annoncée
- la toile n'est jamais plus grande que le film
- la part du film réellement visible
- les contrastes, calculés sur le fond effectif

## Deux pièges de contrôleur, déjà payés ici

**Un contrôleur qui alerte à tort ne sera plus lu.** Deux fausses alertes ont
dû être corrigées dans celui-ci avant qu'il ne serve :

- Il lisait la définition du film dans `window.__IMAGE`. C'est un `ImageBitmap`,
  que le lecteur **ferme** quand l'image quitte la fenêtre de préchargement — et
  un bitmap fermé rapporte `0x0`. Le contrôleur criait « la toile est plus
  grande que le film » sur une page parfaitement saine. Il télécharge désormais
  une image du dossier réellement servi et la mesure.
- Il mesurait avant que la toile ne soit redessinée. Il attend maintenant.

## Ce que le contrôleur ne peut pas voir

Il faut le savoir, sinon on lui fait confiance au mauvais endroit.

- **La barre de défilement.** Le navigateur d'essai utilise des barres en
  surimpression. Un bandeau construit en `-50vw` ajoute une barre horizontale
  sur tout navigateur à barre classique, et le contrôleur ne la verra jamais.
  D'où la règle : séparer les rôles, l'élément extérieur porte la couleur, un
  élément intérieur borne le contenu.
- **Le goût.** Il dit qu'un contraste vaut 6,08:1, pas qu'une mise en page est
  belle.
- **La véracité d'un fait.** Il vérifie qu'une source est citée, pas qu'elle
  dit vrai.
