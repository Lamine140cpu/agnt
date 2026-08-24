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
manifeste-transgold.json  le contrat du site client, avec ses sept questions ouvertes
manifeste-vitrine.json    celui de la vitrine — c'est LUI qui a révélé le générique
mesures.mjs               les relevés dans la page SERVIE (navigateur)
controleur.py             le verdict : contrat + fichiers + page. Sort en 1 si ça casse.

chaine.py                 LA CHAÎNE : construire, mesurer, reconstruire, contrôler
monteuse.py               des plans vidéo au dossier d'images, ordre MESURÉ
nouveau.py                fabrique la page et le contrat d'un site neuf, puis
                          MESURE ses courses dans la page servie
CHEFFE.md                 la brève de la cheffe d'orchestre, à lui donner telle quelle

../moteur/lecteur.js      LE LECTEUR, source unique, inséré à <!--LECTEUR-->
../moteur/socle.css       les 80 règles de structure, insérées à <!--SOCLE-->
../moteur/gabarit.html    la page neuve, correcte par construction
../PROMPTS-FILM.md        comment commander le film
../MODELE-FILM-DEFILANT.md  tout ce qui a été mesuré, et tout ce qui casse
```

## Un site neuf, de bout en bout

```bash
python3 nouveau.py <nom> film=<dossier> marque="…" titre="…" [demo]
# … écrire les six actes dans <nom>.html …
python3 monteuse.py <nom> plans=<dossier de .mp4>     # le film
python3 chaine.py <nom>                               # tout le reste
```

`chaine.py` enchaîne les quatre pas qui se faisaient à la main :

```
1. CONSTRUIRE     une première fois, pour avoir une page à mesurer
2. MESURER        les courses dans la page servie, et en déduire les images
3. RECONSTRUIRE   avec le compte que la mesure a donné
4. CONTRÔLER      et s'arrêter là si ça ne passe pas
```

On construit DEUX fois, et ce n'est pas une maladresse : la première donne une
page à mesurer, la seconde encode le nombre d'images que la mesure a donné.
Mesurer avant d'encoder, jamais l'inverse.

`chaine.py <nom> page` saute le réencodage de la pellicule : la mise en page
change dix fois par jour, le film une fois par site.

**L'étape 4 est une barrière, pas un rapport.** Si le contrôleur refuse, la
chaîne sort en erreur et ne publie rien. C'est tout l'intérêt d'avoir un
contrôle qui ne raisonne pas : on peut lui confier le droit de veto.

### La barrière a d'abord été creuse

Elle mérite d'être racontée, parce que c'est le défaut type de ce genre
d'outil. Première version : `mesurer` réécrivait `serie_attendue` avec ce
qu'il venait d'observer. Le contrôleur comparait donc la réalité à elle-même
— **un contrôle qui ne peut pas échouer**, et qui affiche `ok` avec aplomb.

Trouvé en sabotant volontairement le contrat pour voir si la chaîne s'en
apercevait : elle passait au vert. Le garde-fou s'établit maintenant au premier
passage, et ensuite les écarts sont **signalés, jamais gommés** — si le
changement est voulu, on corrige le contrat à la main, parce que c'est une
décision et qu'elle doit se prendre.

La leçon vaut pour tout ce qui sera ajouté ici : **un garde-fou qu'on n'a
jamais vu refuser n'est pas un garde-fou.** Le casser exprès une fois est le
seul moyen de savoir.

### L'ordre des plans se mesure

`monteuse.py` ne se fie pas aux noms de fichier. Sur le film menuiserie,
l'ordre des prompts et l'ordre réel des plans différaient : les fichiers
portaient les noms des prompts, la chaîne suivait l'ordre de génération. Se
fier au nom donnait un film qui saute trois fois.

Elle compare donc la dernière image de chaque plan à la première de tous les
autres — trente comparaisons — et déduit la chaîne des chiffres. Une vraie
jointure tient sous 6 sur 255, c'est le bruit de recompression ; une fausse est
au-dessus de 35. Si la chaîne est rompue, elle s'arrête : un film dont les
plans ne se suivent pas montre six ateliers différents.

**Ce qui n'est pas éprouvé : l'appel au modèle vidéo.** Il n'y avait pas de clé
dans l'environnement où la monteuse a été écrite, donc `commander()` lève
plutôt que de faire semblant. Le jour où une clé arrive, c'est cette
fonction-là qu'il faut éprouver — et sur UN SEUL plan d'abord.

Le second site a payé sa place : porté sur le contrat, il a montré que la règle
de choix de série écrite pour le premier était fausse pour lui — ses deux séries
ne montrent pas le même cadre — et le contrôleur y a trouvé deux défauts vivants
que personne n'avait vus, dont le bas de page qui touchait le bord de l'écran.
Le TROISIÈME a payé la sienne encore plus cher. Première page à n'avoir jamais
eu de copie du lecteur ni du socle, elle a trouvé trois trous que les deux
autres masquaient : le socle ne contenait pas la règle de la toile — la page
s'affichait vide sans une seule erreur ; le lecteur ne nommait pas l'élément
manquant quand la page en oubliait un ; et le choix de série ignorait le nombre
d'images, servant sur une fenêtre de 900 px une pellicule qui ne tenait pas la
densité.

Aucun des trois ne s'était manifesté en deux sites, parce qu'ils se
ressemblaient trop. C'est exactement pourquoi il ne fallait pas écrire la
cheffe d'orchestre avant d'avoir trois exemples.

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
