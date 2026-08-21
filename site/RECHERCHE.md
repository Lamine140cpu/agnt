# Ce qu'on passait à côté

Recherche menée à la demande : chercher les techniques qui pourraient
améliorer nettement le moteur. Tout ce qui suit est **mesuré**, pas supposé.

## Comment lire les chiffres

Les mesures viennent de ce conteneur : quatre cœurs, **pas de carte
graphique**. Les valeurs absolues seront donc meilleures sur une vraie
machine — mais les rapports entre elles tiennent, et c'est ce qui compte pour
décider. Chaque mesure a été refaite machine au repos : une mesure prise
pendant un encodage a déjà, dans ce projet, fait conclure l'inverse de la
vérité.

---

## 1. Le défaut principal : on dessinait plus grand que le film

C'était invisible partout. Aucune erreur, aucun avertissement, aucun octet de
plus au chargement.

La toile était taillée à la densité de l'écran, plafonnée à 2. Sur un bureau
1600 × 900 en densité 2, cela fait une toile de **3200 × 1800**. Le film, lui,
mesure 1920 × 1080. Chaque image était donc agrandie de 67 %, à chaque trame,
pour n'ajouter **aucune information** : les pixels supplémentaires sont
inventés par l'interpolateur, pas lus dans le fichier.

Coût d'un seul `drawImage`, image 1920 × 1080 :

| toile visée | `low` | `medium` | `high` |
|---|---|---|---|
| 1920 × 1080 — rapport 1:1 | 1,31 ms | 1,36 ms | **1,32 ms** |
| 1600 × 900 — réduction | 5,71 ms | 26,8 ms | **27,5 ms** |
| 3200 × 1800 — agrandissement | 22,2 ms | 104 ms | **184 ms** |

184 ms par image, c'est 5 images par seconde. C'est exactement le « pas fluide
du tout sur PC » qu'on n'arrivait pas à expliquer. **Le décodeur n'y était pour
rien.**

Deux choses à noter dans ce tableau :

- au rapport 1:1, le réglage de qualité ne change rien du tout — il n'y a pas
  de rééchantillonnage à faire, `drawImage` recopie ;
- `high` n'a de sens que si l'on agrandit. Partout ailleurs il coûte cinq fois
  le dessin pour une différence qu'aucun œil ne relève sur une image en
  mouvement.

**Correction retenue.** La densité choisie est la plus grande qui laisse encore
l'image *couvrir* la toile sans être agrandie :

```js
const juste = min(filmL / innerWidth, filmH / innerHeight);
const dpr   = max(1, min(devicePixelRatio, plafond, juste));
```

Le facteur de couverture vaut alors exactement 1. Et la qualité de lissage
passe à `low` sauf quand on agrandit vraiment.

### Ce que ça donne, en défilement continu

Bureau 1600 × 900, densité 2 :

| | 600 px/s | 1000 px/s | 1800 px/s |
|---|---|---|---|
| avant — toile 3200 × 1800 | 4 i/s | 4 i/s | 4 i/s |
| après — toile 1920 × 1080 | 40 i/s | 39 i/s | 32 i/s |
| + sans le flou d'en-tête | **56 i/s** | **54 i/s** | **41 i/s** |

Téléphone 390 × 844, densité 3 — **la toile ne change pas de taille** ; tout le
gain vient du passage de `high` à `low` :

| | 600 px/s | 1000 px/s | 1800 px/s |
|---|---|---|---|
| avant | 31 i/s | 31 i/s | 32 i/s |
| après | **60 i/s** | **60 i/s** | **60 i/s** |

## 2. Le flou de l'en-tête coûtait un quart de l'affichage

`backdrop-filter: blur(6px)` sur une barre fixe, au-dessus d'une toile qui
change à chaque trame : le flou est recalculé à chaque trame, sur toute la
largeur. Mesuré à 1000 px/s : **40 i/s avec, 54 i/s sans.**

Retiré. Le dégradé sombre a été légèrement renforcé (.92 → .95) et porte le
texte tout seul.

## 3. Le retard du décodeur n'existe pas — c'était la mesure qui était fausse

On mesurait l'« absence » comme `image posée ≠ arrondi(image voulue)`. Ce
critère compare un entier à une position **fractionnaire**, alors que le
lecteur fond volontairement les deux images voisines. Il annonçait 48 %
d'absence sur une page parfaitement fluide.

Le bon critère est la **distance** :

| | images/s | retard moyen | 95ᵉ centile |
|---|---|---|---|
| bureau, 600 px/s | 56 | 0,51 image | 1 |
| bureau, 1000 px/s | 53 | 0,55 image | 0,9 |
| bureau, 1800 px/s | 39 | 0,48 image | 1 |
| téléphone, 1800 px/s | 60 | 0,51 image | 0,9 |

Un demi-image de retard moyen : c'est exactement ce que le fondu est censé
absorber. **Le chargeur suit.** Il n'y a rien à corriger de ce côté.

---

---

# Vérification de la piste n°1 du rapport de recherche

Le rapport approfondi désigne comme premier levier une chose que je n'avais pas
nommée : **un seul fichier AVIF en séquence, lu image par image avec
`ImageDecoder` de WebCodecs**. Compression inter-image ET accès indexé. Il avait
raison de pousser : ma conclusion « la vidéo ne rapporte que 15 % » était trop
pessimiste parce que j'avais testé **VP9**, pas **AV1**, et à qualité non
appariée.

Mesuré ici sur 160 images 1920 × 1080, séquence AVIF produite par `avifenc`
(libavif 1.0.4, `-k 12 -q 62 -s 6`), lue dans Chromium :

| | poids | PSNR contre la source |
|---|---|---|
| 160 fichiers AVIF séparés (en service) | 7,41 Mo — 47,4 ko/image | 37,36 dB |
| 1 séquence AVIF | **4,64 Mo — 29,7 ko/image** | **38,99 dB** |

**−37 % de poids ET 1,6 dB de mieux.** Projeté sur le plan large complet :
34 Mo → **22,9 Mo**.

Le décodage aussi est plus rapide, ce qui est contre-intuitif :

| | coût par image |
|---|---|
| fichiers AVIF séparés (décodage intra complet) | 62,8 ms |
| séquence AVIF, lecture **avant** continue | **29,2 ms** |
| séquence AVIF, saut au hasard | 65,2 ms |
| séquence AVIF, **marche arrière** image par image | **208,8 ms** |

## Le piège que le rapport n'a pas vu : la marche arrière

208 ms par image en remontant. C'est la nature même du codage inter-image : pour
rendre l'image N il faut avoir décodé depuis l'image-clé précédente, donc chaque
pas en arrière refait toute la marche. Un visiteur qui remonte la page — ce que
tout le monde fait — verrait la page tomber à 5 images par seconde.

Le profil image par image montre aussi que **Chromium garde un cache interne** :
une image récemment décodée revient en 0,1 ms. Mais la taille de ce cache n'est
pas réglable, donc on ne peut pas s'appuyer dessus.

**La parade est structurelle, pas un réglage** : décoder par **bloc de GOP**
entier et garder les douze images dans notre propre fenêtre, au lieu de demander
une image à la fois. La marche arrière à l'intérieur d'un bloc déjà décodé
devient gratuite, et le coût amorti retombe au niveau de la lecture avant.

## Le second piège : un seul fichier, c'est un seul téléchargement

Aujourd'hui la page affiche quelque chose après seize images, soit ~700 ko. Avec
un fichier unique de 23 Mo, plus rien ne s'affiche tant que les octets ne sont
pas là. `ImageDecoder` accepte un flux, mais on ne peut décoder que ce qui est
arrivé.

**Découper la séquence en segments** d'environ 120 images (une dizaine de
fichiers) conserve la compression inter-image, rend le premier écran aussi
rapide qu'aujourd'hui, et borne la marche à faire depuis l'image-clé.

## Ce que ça donnerait

Séquence en segments de 120 images, GOP 12, décodage par bloc :

- **−33 % de poids** à qualité supérieure ;
- **décodage deux fois plus rapide** en lecture avant ;
- marche arrière ramenée au coût de la lecture avant par le cache de blocs ;
- dix fichiers au lieu de 791 — un cache trivial et dix requêtes.

Le coût : réécriture du chargeur (la fenêtre glissante raisonne en blocs et non
plus en images) et une dépendance à `ImageDecoder`, avec repli sur les fichiers
séparés pour les navigateurs qui ne l'exposent pas.

## Là où je ne suis pas d'accord avec le rapport

**L'interpolation d'images côté client contredit son propre § 13.** Le § 13
explique — à juste titre — que notre fondu entre images voisines fait déjà
office de flou de mouvement et permet de baisser la cadence. Si c'est vrai,
alors synthétiser les images intermédiaires avec un réseau de neurones ne
rapporte presque rien de plus qu'un fondu qui, lui, est gratuit. À cela s'ajoute
que l'interpolation doit produire l'image **avant** qu'on en ait besoin, alors
que le défilement est bidirectionnel et saute — c'est exactement le cas où elle
est le plus en retard.

**Le § 15 raisonne sur des statistiques génériques**, pas sur notre page. Le
numéro de téléphone est déjà dans une barre fixe visible en permanence, le film
ne bloque pas le premier rendu, et la page affiche quelque chose après 700 ko.
La recommandation de fond — ne jamais faire attendre le contenu utile — est
juste, mais elle est déjà appliquée. Ce qui reste vrai et non fait : baisser la
cadence de 30 à 24 images par seconde, et mesurer le LCP réel en conditions 4G.

---

# Les pistes examinées et écartées

## 4. Remplacer la suite d'images par une vidéo — écarté

Comparaison honnête, à qualité mesurée (PSNR contre les sources), sur les mêmes
791 images 1920 × 1080 :

| | poids | PSNR |
|---|---|---|
| 791 fichiers AVIF q45 (en service) | 34 Mo | **39,9 dB** |
| VP9 CRF 30, GOP 12 | 29 Mo | 38,1 dB |

**15 % de moins pour une qualité légèrement inférieure.** Ce n'est pas un gain
qui justifie de réécrire le moteur. (Les chiffres H.264 relevés plus tôt —
41 à 78 Mo selon le GOP — étaient à CRF 18, donc à une qualité bien plus haute :
ils n'étaient pas comparables.)

Le saut à une position quelconque, lui, s'est révélé meilleur que prévu :
**6,3 ms en moyenne, 37 ms au pire**. C'est utilisable. Mais le débit en
lecture accélérée plafonne à 20 images/s en décodage logiciel, et surtout un
élément `<video>` ne donne accès qu'à **une** image à la fois : impossible de
préparer une fenêtre glissante. On perdrait la seule garantie qui fait tenir le
lecteur.

## 5. WebCodecs — disponible, mais pas pour ça

`VideoDecoder` existe partout depuis Safari 26 (Chrome 94, Firefox 130). Il
donnerait le contrôle image par image qui manque à `<video>`.

Mais il faut alors démultiplexer le MP4 soi-même, et surtout gérer les GOP :
pour afficher l'image N il faut décoder depuis l'image-clé précédente, soit
jusqu'à onze décodages de plus. Et chaque `VideoFrame` retient de la mémoire
système qu'il faut fermer à la main.

Beaucoup de machinerie pour les 15 % du point 4. **Écarté.**

## 6. `createImageBitmap(blob, { resizeWidth })` — écarté comme levier de vitesse

Mesuré : 17,65 ms tel quel contre 24 à 36,6 ms avec redimensionnement. La
réduction s'ajoute **après** le décodage, elle ne l'allège pas.

En revanche elle divise la mémoire par 4 à 960 px. C'est un levier sur la
*profondeur de la fenêtre*, pas sur la vitesse. À garder en réserve si un jour
la mémoire redevient la contrainte.

## 7. Garder les octets compressés en mémoire — marginal

C'est ce que fait velaarmon avec son tableau `h[]` : une image purgée est
re-décodée au lieu d'être re-téléchargée. Mesuré, par image 1920 × 1080 :

| | durée |
|---|---|
| requête, cache HTTP froid | 16,7 ms |
| requête, cache HTTP chaud | 7,9 ms |
| **décodage AVIF** | **62,8 ms** |
| dessin (rapport 1:1) | 1,3 ms |

Garder le blob économise les 7,9 ms de la requête chaude — **11 % du coût
total**, contre de la mémoire retenue en permanence. Le cache HTTP du
navigateur fait déjà l'essentiel du travail. **Écarté.**

## 8. Changer de format d'image — écarté

| format, 1920 × 1080 | poids moyen | décodage |
|---|---|---|
| AVIF q45 (en service) | 42 ko | 62,8 ms |
| WebP q82 | 90 ko | 44,0 ms |
| JPEG q82 | 156 ko | 49,2 ms |

WebP décode 30 % plus vite mais pèse 2,1 fois plus : 34 Mo deviendraient 72 Mo.
Le compromis n'en vaut pas la peine tant que le décodeur suit — et il suit
(point 3).

## 9. `OffscreenCanvas` + `Worker` — sans objet désormais

L'idée était de sortir le dessin du fil principal. Mais le décodage était déjà
hors fil principal (`createImageBitmap`), et depuis le point 1 le dessin coûte
**1,3 ms**. Il n'y a plus rien à déplacer.

## 10. `alpha: false`, `desynchronized: true` — déjà en place

Vérifié dans le code des deux pages. J'avais annoncé le contraire : c'était
faux.

## 11. Un écran d'attente — déjà en place

Le voile attend seize images décodées et affiche une jauge. Déjà fait.

---

# Le vrai trou : le référencement

Pour un site de transporteur, c'était le manque le plus coûteux de tout le
projet — et il n'a rien à voir avec le décodage.

Avant : titre de deux mots (`Trans Gold`), aucune description, aucune image de
partage, aucune donnée structurée, pas de sitemap. Pour un moteur de recherche,
trente écrans de film et de texte se résumaient à deux mots.

Personne ne tape « trans gold marchandises ». On tape « transporteur palette
Aulnay » ou « transport lot complet Seine-Saint-Denis ». Si ces phrases ne sont
rattachées à rien, la page n'est jamais proposée.

Ajouté aux deux sites :

- un titre long et une description de 145 caractères (au-delà de 160, un moteur
  coupe la phrase en plein milieu) ;
- les balises Open Graph et Twitter, avec une vignette 1200 × 630 tirée du film ;
- un `<link rel="canonical">`, `robots`, `theme-color` ;
- un bloc JSON-LD `LocalBusiness` + `Organization` pour Trans Gold : adresse,
  coordonnées géographiques, SIREN, SIRET, code APE, date de création,
  catalogue de prestations. **Toutes ces données viennent du registre national
  des entreprises**, pas d'une supposition : une donnée structurée fausse se
  retourne contre le site ;
- `robots.txt` et `sitemap.xml`, produits par la construction d'après l'adresse
  canonique déclarée dans la page.

## Ce qui reste à faire de ce côté

**L'hébergement.** GitHub Pages renvoie `cache-control: max-age=600` sur tous
les fichiers, et ce n'est pas réglable. Dix minutes. Un visiteur qui revient
une heure plus tard **re-télécharge les 34 Mo du film**. Chez un hébergeur qui
laisse poser `max-age=31536000, immutable` sur les images (Cloudflare Pages,
Netlify, Vercel — gratuits à cette échelle), la deuxième visite serait
quasiment instantanée. C'est probablement le plus gros gain restant, et il ne
demande aucune ligne de code.

Deux autres points, mineurs : GitHub Pages ne sert qu'en gzip (22 ko pour la
page) là où brotli donnerait environ 17 ko ; et les images AVIF sont servies
avec l'en-tête `content-type: image/jpeg` — le navigateur reconnaît le format
aux octets, donc ça marche, mais ça interdit toute négociation de format et
n'importe quel intermédiaire qui « optimiserait les JPEG » les casserait.

**Les adresses absolues.** Les six URL déclarées dans les balises pointent vers
l'hébergement provisoire. Le jour du nom de domaine, il faut les reprendre —
une adresse canonique fausse fait indexer la mauvaise page.

**Trois informations toujours attendues du client**, sans lesquelles les
mentions légales restent incomplètes : le directeur de la publication (deux
dirigeants au registre, ça ne se devine pas), l'hébergeur retenu, et si
« une vingtaine » désigne les camions ou les salariés — le registre annonce
11 à 19 salariés en 2023.
