# Un site à film défilant — le modèle

Ce fichier existe pour qu'une autre intelligence artificielle, sans rien de
cette session, puisse reconstruire ce type de site et **ne pas repayer les
mêmes erreurs**. Tout ce qui suit a été mesuré, pas supposé. Quand un chiffre
apparaît, la mesure qui l'a produit est écrite à côté : c'est la seule façon de
savoir si elle vaut encore sur une autre machine.

Ce n'est pas un tutoriel. C'est la liste de ce qui casse.

---

## 1. Ce que c'est

Une page dont le fond est un **film que le défilement fait avancer image par
image**. Le visiteur ne regarde pas une vidéo : il la déroule. Par-dessus,
des blocs de texte transparents passent en revue les « actes ».

Trois techniques possibles, une seule qui tient :

| Technique | Verdict |
|---|---|
| `<video>` + `currentTime` | **Non.** Le positionnement image par image n'est fiable sur aucun navigateur ; on obtient des sauts et des images figées. |
| WebGL / three.js | **Non.** On dessine une image plate sur un fond plat. Le surcoût de la bibliothèque, du contexte et du shader ne rachète rien. |
| **Toile 2D + séquence d'images** | **Oui.** `createImageBitmap`, une fenêtre de préchargement glissante, `drawImage`. C'est ce qui est décrit ici. |

---

## 2. L'unité qui gouverne tout : le pixel de défilement par image

Ce n'est ni le nombre d'images, ni la durée. C'est **combien de pixels de
défilement séparent deux images**.

```
course  = prologue.offsetHeight - innerHeight     (mesuré dans la page servie)
images  = course / densité
```

- **33 px par image** : le réglage retenu ici. À 1000 px/s de défilement —
  une vitesse de molette courante — cela fait 30 changements d'image par
  seconde. C'est fluide.
- **Au-delà de 45 px par image**, ça saute visiblement.
- **6 px par image** : la densité d'un site de référence très soigné. Cinq
  fois plus d'images, cinq fois plus d'octets. Le rapport qualité/poids
  s'écroule au-delà de ~25.

**La course se MESURE dans la page servie. Elle ne se devine pas et ne se
recopie pas.** Elle dépend de la mise en page : ici, faire passer les actes de
130 à 170 svh l'a portée de 15 300 à 26 100 px. La constante n'a pas suivi, et
la construction a livré 464 images au lieu de 791 **en affichant fièrement
« 33,0 px par image »** alors que la densité réelle tombait à 56. Une constante
fausse qui sert aussi à calculer le message de contrôle ne peut pas se
contredire toute seule.

Mesurer, à chaque taille de fenêtre visée, et prendre **la plus grande** :

```js
document.getElementById('prologue').offsetHeight - innerHeight
```

Valeurs relevées sur ce site : 1440×900 → 26 100 px · 1280×800 → 23 200 ·
390×844 → 17 386 · 360×740 → 15 244.

---

## 3. Le coût dominant est le remplissage de la toile, pas le décodage

C'est le contresens le plus cher. Tout le monde soupçonne le décodeur ; c'est
`drawImage` qui coûte.

Mesuré, par image :

| Opération | Coût |
|---|---|
| dessiner à l'échelle 1:1 | **1,3 ms** |
| agrandir vers 3200×1800 avec `imageSmoothingQuality: 'high'` | **184 ms** |

Un site à 4 images par seconde a été ramené à 54 par ce seul correctif.

### La règle

**Ne jamais dessiner plus grand que le film.** On plafonne la densité de pixels
par la résolution réelle de la pellicule :

```js
const boite   = canvas.getBoundingClientRect();
const larg    = boite.width  || innerWidth;
const haut    = boite.height || innerHeight;
const plafond = larg < 820 ? 1.5 : 2;
// « juste » : la densité au-delà de laquelle on agrandirait le film.
const juste   = (filmL && filmH) ? Math.min(filmL / larg, filmH / haut) : plafond;
const dpr     = Math.min(devicePixelRatio || 1, plafond, juste);

canvas.width  = Math.round(larg * dpr);
canvas.height = Math.round(haut * dpr);
ctx.imageSmoothingEnabled = true;
ctx.imageSmoothingQuality = 'low';
```

**Aucun plancher à 1.** L'écrire `Math.max(1, …)` paraît prudent et rouvre le
défaut : sur une fenêtre plus large que le film — 1440p, ou 1080p à 125 % —
la toile redevient plus grande que la pellicule et le débit retombe à 6 à
10 images par seconde. Quand la fenêtre dépasse le film, il faut **laisser le
compositeur** faire l'agrandissement : il le fait sur le processeur graphique,
pour rien.

`imageSmoothingQuality: 'high'` est un filtre multi-passes. Il ne se justifie
que si l'on agrandit vraiment. Sinon c'est du coût pur.

Mesurer la toile **par `getBoundingClientRect()`**, jamais par la fenêtre : une
mise en page peut n'accorder au film qu'une colonne. Et poser un
`ResizeObserver` dessus.

---

## 4. La latence : deux retards de premier ordre s'additionnent

Symptôme classique : **« excellent sur téléphone, mou sur PC »**. Ce n'est pas
une impression, et ce n'est pas la puissance de la machine.

Le tactile pilote le défilement natif. La molette, elle, traverse souvent deux
lissages successifs :

1. un lissage de la molette vers une position de défilement visée ;
2. un rattrapage de l'image courante vers l'image visée.

Deux retards de premier ordre en série : mesuré **432 ms** entre le geste et
l'image. Un seul : 256 ms. Le doigt n'en traverse aucun, d'où l'asymétrie.

Correctif : quand la molette pilote, l'image suit **sans second lissage**.

```js
courant = (lent || molette) ? vise
                            : courant + (vise - courant) * (1 - Math.exp(-9 * dt));
```

Résultat mesuré : 444 ms → **185 ms**, la page et l'image arrivant ensemble.

### Et jamais de mise en page dans un gestionnaire de molette

```js
// NON — recalcul complet de la page à CHAQUE événement de molette.
cible = borne(cible + e.deltaY, 0, document.body.scrollHeight - innerHeight);
```

`scrollHeight` force le navigateur à recalculer toute la mise en page. Sur une
page de trente écrans, à la fréquence des événements de molette, c'est du gel.
Mesurer **une fois**, rafraîchir au redimensionnement.

---

## 5. Le cadrage sur téléphone — et le piège de la généralisation

Un écran de téléphone fait environ 0,46 de rapport. Un film en fait 1,78. En
cadrage « couvrir » :

```
part de la largeur du film visible  =  rapport de la toile / rapport du film
```

Dans un cas — et seulement dans celui-là — encoder une série intermédiaire
recadrée n'y change **rien** :

| Série intermédiaire | Recadrage du maître | Part visible de celle-ci | **Total** |
|---|---|---|---|
| 9:16 | 32 % | 82 % | **26 %** |
| 3:4 | 42 % | 62 % | **26 %** |
| carrée | 56 % | 46 % | **26 %** |
| 16:9 (le maître) | 100 % | 26 % | **26 %** |

### La condition qu'on oublie

**Cet invariant ne vaut que si la série étroite est un RECADRAGE du même
maître.** Si elle est un vrai montage — des plans composés pour le portrait —
elle ne montre pas le même cadre, et le calcul ne s'applique plus du tout.

Les deux cas existent, et ils étaient côte à côte dans le même dépôt :

| | série étroite | écart mesuré au recadrage centré reconstruit |
|---|---|---|
| le site client | un **recadrage** | 1,4 / 255 — le bruit de recompression JPEG |
| la vitrine | un **vrai montage** | 43 à 54 / 255 sur les quatre cinquièmes du film |

**La mesure qui tranche** : reconstruire soi-même un rognage centré du maître,
au format de la série étroite, et comparer image par image. Sous ~5/255 c'est
un recadrage ; au-delà, un montage. Ne jamais croire le commentaire du code là-
dessus : celui de ce dépôt affirmait « un vrai montage » pour une série qui
était un rognage.

### Le levier, quand c'est un recadrage

La hauteur donnée à la toile, rien d'autre :

| Le film occupe | Part du film visible |
|---|---|
| 100 % de l'écran | 26 % |
| 80 % | 32 % |
| **64 %** | **41 %** |
| 55 % | 47 % |

Retenu sur le site client : **64 %**, le texte de l'acte se posant en dessous.
Le coût est presque nul, parce que le voile qui porte le texte était **déjà**
opaque à 90 % aux deux tiers de la hauteur : le bas du film était enterré.

**Et ce correctif serait un défaut sur l'autre site.** Là où la série étroite
est un montage portrait composé pour occuper l'écran entier, lui donner une
bande de 64 % gâcherait le cadrage voulu. Le manifeste de chaque site doit donc
noter non seulement ce qu'on lui applique, mais ce qu'on ne lui applique pas.

---

## 5 bis. Choisir la série : la forme d'abord, le poids ensuite

Aucune règle simple ne couvre les deux cas ci-dessus. Celle qui tient :

1. **LA FORME.** Garder les séries dont le rapport est le plus proche de celui
   de la toile. C'est ce critère qui trouve un montage portrait. Quand deux
   séries ont le même rapport — le cas du recadrage — elles restent toutes
   les deux en lice et le second critère tranche.
2. **LE POIDS.** Parmi elles, la **plus petite qui couvre la toile sans
   agrandissement**. Agrandir coûte le remplissage, le poste le plus cher du
   lecteur. Servir plus large que nécessaire double la charge mobile pour un
   rendu identique. Si aucune ne suffit, la plus grande.

Le rapport se compare **en logarithme** : sans cela, 0,56 et 1,78 face à une
toile carrée donneraient des écarts de 0,44 et 0,78 alors qu'ils sont à
distance égale.

### Deux décisions au pixel près s'y sont trompées

Elles méritent d'être connues, parce qu'elles sont du même genre et qu'aucune
ne produit d'erreur visible :

- **Un rapport arrondi qui décide.** Écrite avec `rapport: 1.778`, la règle
  calculait `1440 / 1,778 = 809,9` et jugeait une série de 810 px trop courte.
  Les séries déclarent donc leurs **deux dimensions réelles**, jamais un
  rapport.
- **Un ajustement exact qui ne survit pas.** La toile du téléphone fait
  `64 svh` de 844, soit 540,156 points, donc **810,23** pixels d'appareil : la
  pellicule de 810, taillée pour ce cas précis, le ratait d'un quart de pixel,
  et le téléphone recevait celle de 1920 — le double de la charge. **Deux pour
  cent de tolérance.** Un ajustement au pixel près ne survit ni aux hauteurs de
  fenêtre variables, ni aux barres du navigateur, ni au zoom.

Et surtout : **une mauvaise série ne se voit pas à l'écran, elle se paye en
octets.** Le contrôle doit donc être explicite — quelle série est attendue à
quelle taille — sinon la régression passe.

---

## 6. `position: sticky` : le conteneur doit être bien plus haut

Un élément collant de 100svh dans une section de 130svh ne dispose que de
30svh de course — 10svh sur un téléphone, où les barres du navigateur mangent
le reste. Il paraît immobile, puis saute.

Régle : viser **au moins trois fois** la hauteur de l'élément collant. Ici les
sections sont passées de 130 à 170svh, et c'est cette modification qui a
périmé la course du film (voir § 2).

---

## 7. Mesurer : la médiane de trois passages

Une lecture isolée du débit d'images varie **de 45 à 60** sur la même page sans
rien changer. Deux fausses alertes ont été levées dans ce projet sur des
lectures uniques.

**Toujours la médiane de trois passages.** Et se rappeler qu'un conteneur sans
processeur graphique donne des valeurs absolues pessimistes : les **rapports**
restent valables, pas les chiffres.

---

## 8. Le contrat de construction

C'est là que tout se défait silencieusement. Trois constantes de ce projet ont
cessé de décrire la réalité sans que rien ne le signale :

| Constante | Écrite | Réelle | Conséquence |
|---|---|---|---|
| course | 15 300 px | 26 100 px | 464 images au lieu de 791, densité 56 au lieu de 33 |
| qualité | q55 par défaut | q45 en production | pellicule deux tiers plus lourde si quelqu'un construit sans drapeau |
| série étroite | « un vrai montage » | un rognage centré | le cadrage téléphone qu'on croyait corrigé |
| compte d'images par série | 527 et 1152 | 791 et 527 | 404 en rafale, film figé au milieu du prologue |

Aucune n'a produit d'erreur. Deux ont produit un **message rassurant et faux**.

### Ce qu'une construction doit faire

1. **Mesurer** la course dans la page servie, à chaque taille visée.
2. **Écrire** dans la page le nombre d'images réellement livré, en comptant les
   remplacements effectués — pas en vérifiant que le texte « a changé ».
3. **Refuser d'écrire** si un point d'ancrage attendu manque. Une page qui
   compile mais s'affiche noire est le pire mode de panne : elle ne se
   signale pas. Vérifier la présence de la toile, du prologue, de la suite et
   de l'écran d'attente avant de produire quoi que ce soit.
4. **Nommer explicitement** le dossier de sortie de chaque série. Ni déduit de
   la clé, ni déduit du dossier source : les deux ont déjà écrit les images à
   côté de là où la page les cherchait.
5. **Relire ce qu'on vient d'écrire.** Compter les substitutions réussies ne
   prouve rien : deux substitutions peuvent avoir visé la même ligne. C'est
   arrivé — le garde-fou comptait « exactement une correspondance » pour
   chacune des deux séries, et c'était la même. Seule la relecture, série par
   série, comparée au dossier livré, le dit.
5. **Ne recopier que les fichiers que la page cite réellement** (repérés par
   expression régulière sur la source), pour ne pas embarquer trois jeux de
   polices dont deux sont inutiles.

---

## 8 bis. Une seule source, jamais une recopie

C'est le défaut structurel de ce genre de projet, et il ne se signale jamais.

Mesuré dans ce dépôt avant correction : **six versions différentes du même
lecteur** cohabitaient, divergeant de 8 à 13 %. Cinq refontes et la vitrine
tournaient sans les correctifs de fluidité, de cadrage et de définition. Le
dépôt le disait déjà de lui-même — « un correctif de fluidité avait dû être
porté trois fois de suite » — et personne n'en avait tiré la conséquence.

Même chose côté style : sur 90 sélecteurs communs à deux sites, **80 avaient un
corps identique au caractère près**. Les dix qui divergeaient étaient ceux qui
doivent — palette, en-tête, pied, hauteur des actes — sauf un : un correctif
fait d'un côté et jamais reporté, qui laissait **les quatre sections du bas de
l'autre site à 0 px du bord de l'écran sur téléphone**.

### Ce qui marche

```
moteur/lecteur.js     le lecteur, inséré à la place de <!--LECTEUR-->
moteur/socle.css      les règles de structure, insérées à <!--SOCLE-->
```

**Insérés à la construction, pas chargés par `<script src>` ou `<link>`.** Un
site client tient sur une seule page : une requête de plus avant que le film ne
démarre coûterait un aller-retour à chaque visite, pour un cache que personne
ne réutiliserait. Une source sur le disque, zéro requête en ligne.

Le socle va **en tête** de la feuille du site, qui garde ainsi le dernier mot
sur tout ce qu'elle redéclare.

### Sortir du code d'une feuille de style change la cascade

Une relecture ne prouve rien là-dessus. La preuve se mesure : **empreinte des
styles CALCULÉS de chaque élément**, sur plusieurs dizaines de propriétés et
plusieurs tailles d'écran, avant et après.

Fait ici sur 295 et 199 éléments × 34 propriétés × 3 tailles : une seule
différence de chaque côté, sur le même élément — un filet **animé**, dont
l'opacité est échantillonnée au hasard d'une boucle de 2,6 s. Zéro différence
réelle.

Prévoir ce test AVANT de toucher à une feuille de style partagée. Sans lui, on
ne peut ni affirmer que le remaniement est neutre, ni savoir ce qu'il a cassé.

### Ce qui doit rester au site

Ce qui est propre à un site, mesuré sur deux : la palette (`:root`), l'en-tête,
le pied de page, la hauteur des actes, les voiles, le décalage d'ancre. Et
**tout ce qui vient d'une décision** — un correctif juste pour l'un peut être
un défaut pour l'autre, comme la bande de 64 svh sur téléphone.

---

## 9. La liste de vérification avant livraison

À automatiser. Chaque ligne correspond à un défaut réellement rencontré.

**Le film**
- [ ] La toile se dimensionne à sa boîte CSS, pas à la fenêtre ; `ResizeObserver` posé.
- [ ] Densité de pixels plafonnée par la résolution du film, **sans plancher à 1**.
- [ ] `imageSmoothingQuality` à `'low'` hors agrandissement réel.
- [ ] Débit ≥ 55 images/s, **médiane de trois passages**, à 1440×900 et 390×844.
- [ ] Aucune image manquante en fin de séquence (vérifier les deux dernières et les deux premières par leur nom de fichier).
- [ ] Le nombre d'images écrit dans la page est celui du dossier livré — **relu dans le fichier écrit**, pas déduit du nombre de substitutions.
- [ ] **Aucune image réclamée et absente** : parcourir tout le prologue en écoutant les réponses ≥ 400. C'est la signature d'un compte faux, et elle ne se voit qu'au-delà du point où les images cessent d'exister.
- [ ] **La série servie est celle attendue**, à chaque taille. Une mauvaise série ne se voit pas à l'écran, elle se paye en octets.
- [ ] La **densité réelle** — course mesurée ÷ images livrées — pas celle qu'annonce la construction.

**La mise en page**
- [ ] Aucun débordement horizontal : `documentElement.scrollWidth <= clientWidth`, à 1440, 1280, 900, 390 et 360 px.
- [ ] **Se méfier de `100vw`** : il compte la barre de défilement, la largeur du contenu non. Un bandeau pleine largeur construit en `-50vw` ajoute une barre horizontale sur tout navigateur à barre classique — et un navigateur d'essai à barres en surimpression **ne peut pas le voir**. Séparer les rôles : l'élément extérieur porte la couleur, un élément intérieur borne le contenu.
- [ ] Aucun intitulé tronqué dans la navigation (`scrollWidth > clientWidth` sur chaque lien).
- [ ] Les décalages d'ancre dépassent la hauteur réelle de l'en-tête — la mesurer, elle change dès qu'on y met un logo.
- [ ] Aucun lien resté bleu.
- [ ] **Marge latérale respectée** : pour chaque bloc et le pied, la position du premier texte. Sous 12 px du bord, c'est un `padding` en raccourci qui a écrasé celui d'une classe posée avant — trouvé DEUX fois ici, et invisible ailleurs que sur téléphone.
- [ ] Un masque de fondu ne s'applique qu'aux largeurs où la rangée défile vraiment.

**Les couleurs**
- [ ] Contrastes calculés, pas jugés à l'œil. Corps ≥ 4,5:1, second plan ≥ 3:1.
- [ ] Une règle portant un identifiant l'emporte sur une règle de classe : vérifier qu'un correctif général ne repeint pas un bouton dont la couleur était voulue.

**Les images fournies par le client**
- [ ] Détourage d'un fond blanc **par diffusion depuis les bords**, jamais par seuil de clarté : un logo contient ses propres blancs, un seuil les troue.
- [ ] Un pixel d'adoucissement sur le masque, sinon la compression JPEG laisse un liseré crénelé.
- [ ] Redimensionner et quantifier : un logo d'en-tête affiché à 60 px n'a pas à peser 173 Ko. Ici 18 Ko, indiscernable, comparé côte à côte avant de trancher.
- [ ] Attributs `width`/`height` sur l'image, pour que la barre ne sursaute pas.

---

## 10. Ce qu'on n'invente jamais

Sur le site d'une entreprise réelle, **aucun fait ne se devine** : ni la taille
de la flotte, ni les certifications, ni le numéro de licence, ni le directeur
de la publication, ni les horaires, ni l'adresse électronique. Un pied de page
qui affirme faux est pire qu'un pied de page court.

Les données d'immatriculation se vérifient au registre national :

```
https://recherche-entreprises.api.gouv.fr/search?q=<SIREN>
```

Le reste se demande au client. Tant qu'il n'a pas répondu, la mention reste
visiblement à compléter — jamais remplie au jugé.

Et un logo ne se redessine pas de mémoire : ce serait inventer l'identité d'une
société. On demande le fichier.

---

## 11. Le squelette

```
<canvas id="toile">              fixe, plein cadre, z-index 1
<div id="prologue">              z-index 3, transparent
  <section>                      un acte — 3 écrans sur bureau, 2 sur téléphone
    ::before                     le voile fixe, allumé quand l'acte entre en scène
    .tenir > .mot                le texte, calé en bas
<div id="suite">                 z-index 4, OPAQUE — recouvre la toile sans l'éteindre
  <section>…</section>           les blocs classiques
  <footer>                       le pied de page
<div id="voile">                 l'écran d'attente : #etape, #jauge, #pct
```

Points à ne pas manquer :

- `#suite` **opaque** : c'est ce qui éteint le film sans une ligne de
  JavaScript, et c'est plus robuste que n'importe quel `display:none` piloté.
- Le voile de chaque acte est **fixe et plein cadre**. Un dégradé incliné dans
  une boîte plus haute que large trace sa propre diagonale, et elle se voit :
  garder les dégradés strictement horizontaux ou verticaux.
- L'écran d'attente doit dire **où en est le chargement**. Une toile vide sans
  message est indiscernable d'une panne.
- Prévoir `?diag=1` : un panneau qui affiche fenêtre, densité, taille de toile,
  durée de trame, retard du décodeur. Il a trouvé plus de défauts que la
  lecture du code — à condition qu'il compare des entiers à des entiers, sinon
  il accuse le décodeur à tort.

---

## 12. L'ordre dans lequel construire

1. Le film d'abord : obtenir la séquence d'images, connaître sa résolution et
   son rapport.
2. La page nue avec la toile, sans texte. Vérifier le débit d'images **avant**
   d'écrire quoi que ce soit d'autre.
3. Mesurer la course. En déduire le nombre d'images. Encoder.
4. Poser les actes, puis remesurer la course : elle a changé.
5. Le bas du site, le pied de page, les mentions légales.
6. La liste de vérification du § 9, en entier, à chaque livraison.

L'étape 4 est celle qu'on oublie. C'est elle qui a périmé la densité de ce
site pendant plusieurs semaines sans que rien ne le dise.
