# Atteindre le niveau Ciao / Apple / Lusion — état des lieux

Recherche menée le 15 août 2026. Trois sources : un démontage direct des
fichiers de ciaoenergy.com, deux recherches web approfondies, et nos propres
mesures sur le moteur maison.

Les faits marqués **mesuré** ont été vérifiés en téléchargeant les fichiers ou
en chronométrant le code. Les faits marqués **rapporté** viennent de sources
citées, non reproduites ici.

---

## 1. Ce que charge réellement Ciao Energy — mesuré

Fichiers téléchargés depuis `cdn.mprez.fr` et ouverts.

| Ressource | Poids | Contenu |
|---|---|---|
| `can.glb` | **159 Ko** | **5 702 triangles**, 3 maillages (`Shell`, `Bottom`, `Top`), 2 matières (`Etiquette` métal 0 rugosité 0,5 ; `Metal`), **aucune image embarquée** |
| `base.glb` | 607 Ko | 24 432 triangles — le socle (câble cuivre, tubes, embases) |
| `hdri2.hdr` | 1,36 Mo | vraie carte HDR, chargée par `RGBELoader` |
| étiquette AVIF | 180 Ko | une par parfum, **hors du .glb**, échangeable |
| fonds animés | 1 à 2,7 Mo | **vidéos** mp4 + webm, une par parfum |

Bibliothèques : three.js, `GLTFLoader`, `RGBELoader`, `EffectComposer`,
`BloomPass`, `FXAAShader`, `SMAAPass`, `OutputPass` — plus **GSAP
ScrollTrigger et SplitText** pour la chorégraphie. Le site est un Webflow ;
tout le WebGL est un script ajouté.

**Total 3D ≈ 2,3 Mo.** Notre page voiture en pèse 13.

### Ce que ça établit

- Leur canette fait 5 702 triangles ; notre canette procédurale en fait
  environ 4 400. **Même ordre de grandeur.** La technique n'a jamais été
  l'écart.
- Leur architecture est la nôtre : un moteur, un objet léger, l'habillage
  chargé à part et échangeable. On avait déduit « moteur + configuration »
  tout seuls ; c'est bien ce qu'ils font.
- Trois choses qu'ils font mieux et qui se copient en une journée : une vraie
  HDRI plutôt qu'un JPEG dont on reconstruit la dynamique, des vidéos de fond
  plutôt qu'un dégradé, et GSAP plutôt qu'une boucle maison.

---

## 2. Les aveux des studios primés — rapporté

La section la plus utile de toute la recherche. Aucun de ces studios ne
calcule d'éclairage global en temps réel. Aucun. Ils pré-calculent tout ce
qui peut l'être et réservent le GPU au mouvement.

**Lusion** ([étude de cas Awwwards](https://www.awwwards.com/case-study-for-lusion-by-lusion-winner-of-site-of-the-month-may.html))
mélange du **pré-rendu Redshift hors ligne** avec du temps réel : une vidéo
de 150 Ko, la position de caméra exportée en JSON pour raccorder les deux.
Leur simulation de tissu est calculée dans **Houdini** et stockée en
ArrayBuffer de 220 Ko. L'animation de sommets passe par des **textures PNG**
— une pour les positions, une pour les normales — avec 11 images-clés
interpolées sur 66, et des flottants 32 bits ramenés à des entiers 16 bits.
Échelonnement machine explicite : **983 Ko sur desktop, 246 Ko sur mobile**,
4 096 sommets contre 1 024.

**Edan Kwan**, fondateur de Lusion
([billet](https://medium.com/@edankwan/lost-in-parallel-universe-dba640efd39a)) :
« sacrifier la qualité d'image pour faire tourner une simulation de fumée en
temps réel à 60 images par seconde était une idée stupide ».

**Shopify Spring '26**
([Codrops](https://tympanus.net/codrops/2026/06/26/engineering-the-web-experience-behind-shopifys-spring-26-edition-everywhere/))
est le plus explicite : leur lumière volumétrique **est une vidéo**,
pré-traitée en textures tableau KTX2. Ils écrivent noir sur blanc « mouvement
exporté en vidéo quand l'animer au runtime ne valait pas son coût ».
Échelonnement à quatre niveaux. Et une phrase directement transposable à
notre chorégraphie : **« la position de défilement pilote des uniformes, pas
des re-rendus »**.

**The Sleepers** ([Codrops](https://tympanus.net/codrops/2026/07/10/the-sleepers-creating-an-atmospheric-webgl-experience-with-lightweight-techniques/))
: le brouillard volumétrique est « une sorte de tour de passe-passe
colorimétrique appliqué aux matières ». Zéro volumétrie.

**Active Theory** ([billet](https://medium.com/active-theory/the-story-of-technology-built-at-active-theory-5d17ae0e3fb4))
n'utilise même pas three.js — moteur maison *Hydra*. Pour adidas, des
vêtements de plus de 500 000 polygones et des textures 4K ont été écrasés en
maillages mobiles à deux textures 2K, et **ce sont les normal maps cuites
depuis les originaux qui portent tout le rendu**.

---

## 3. La géométrie : le verdict sur le génératif — rapporté

Question posée : peut-on passer des images cohérentes que Gemini produit à un
maillage de voiture **avec habitacle** ?

**Réponse : non, pas aujourd'hui.** Et la raison est précise.

### TRELLIS.2 : « enclosed interior structures » veut dire représenter, pas inventer

Le [papier](https://arxiv.org/abs/2512.14692) dit que la représentation
O-Voxel « peut modéliser une topologie arbitraire, y compris des surfaces
entièrement fermées ». Le verbe est *modéliser*. C'est une propriété du
**format de données**, pas une capacité de génération : contrairement aux
champs de distance signée, O-Voxel enregistre où la surface croise les arêtes
d'une grille, ce qui ne se soucie pas de savoir si elle se referme.

La preuve contraire est dans
[l'issue #140](https://github.com/microsoft/TRELLIS.2/issues/140) : « la
plupart des générations ajoutent une coque interne entière ». Ce n'est pas un
habitacle, c'est une **seconde carrosserie parasite** décalée vers
l'intérieur. Aucune réponse des mainteneurs.

Second bloquant, décisif pour nous :
[l'issue #103](https://github.com/microsoft/TRELLIS.2/issues/103) rapporte que
« les performances avec des entrées multi-images sont étonnamment pires
qu'avec une seule image ». **Nos douze vues cohérentes ne servent à rien avec
TRELLIS.2.** Il n'en consommera qu'une.

Le seul point excellent : **licence MIT sur le code et les poids**, la plus
permissive du marché. Hébergement : gratuit sur le Space Hugging Face,
0,25 à 0,35 $ par génération sur fal.ai, 24 Go de VRAM en local.

### Les concurrents

| Outil | Multi-vues | Habitacle | Licence de sortie |
|---|---|---|---|
| TRELLIS.2 | non | non (double coque) | **MIT** |
| Meshy 7 | **4 vues à slots nommés** | non | propriété pleine sur plan payant |
| Tripo 3.0 | oui | non | commercial sur Pro+ ; gratuit = non commercial |
| Rodin / Hyper3D | **jusqu'à 5 images** | non | commercial sur tous les plans |
| Hunyuan3D 3.1 | **jusqu'à 8 vues** | non | **exclut l'Union européenne** |

Deux choses à retenir. **Hunyuan est hors jeu depuis la France** : sa licence
exclut explicitement l'UE, le Royaume-Uni et la Corée du Sud, motif AI Act.
Et paradoxalement, **TRELLIS.2 est le plus mal adapté à notre situation**
malgré sa licence : c'est le seul qui refuse le multi-vues.

Aucun ne produit d'habitacle. La règle documentée par Meshy l'explique :
le système fonctionne quand « toutes les parties sont clairement visibles sous
au moins un angle ». Un habitacle occlus ne l'est jamais.

### La piste qui marche : capturer au lieu de deviner

Un [Toyota 4Runner a été numérisé en splat gaussien, habitacle
compris](https://80.lv/articles/look-inside-toyota-4runner-turned-into-a-3d-gaussian-splat)
— quelques centaines de photos, environ une heure de prise de vue.

**Et nous avons déjà notre moteur de rendu de splats.** C'est ce qui change
l'arbitrage : la conversion splat vers maillage est l'étape qui dégrade tout,
et nous pouvons la sauter.

Outils : **Scaniverse** (Niantic) est gratuit, traite sur l'appareil en 60 à
90 secondes et exporte en PLY et SPZ. **KIRI Engine** (~18 $/mois) est le seul
avec conversion splat vers maillage intégrée. **RealityScan 2.1** (Epic) est
gratuit sous un million de dollars de chiffre d'affaires.

Difficultés connues du scan de voiture : peinture réfléchissante, pare-brise
qui devient un voile blanc, optiques de phares ingérables. Ciel couvert
obligatoire, recouvrement de 60 à 80 %, trois hauteurs de prise de vue.

---

## 4. Le plan d'action, par ordre de rentabilité

### À faire — rendement immédiat

**1. Passer des couleurs par sommet à un atlas de lightmap.**
C'est notre plus grand écart mesurable avec les studios primés. Notre rebond
est cuit correctement mais échantillonné à la densité du maillage : le dégradé
de contact et l'ombrage d'angle sont lissés par l'interpolation. Un atlas
2048² sur un second jeu de coordonnées donne le contact net qui se lit comme
« rendu hors ligne ». Coût runtime : **négatif**. Gains rapportés sur des
projets comparables : ×3 à ×4 sur desktop, ×5 sur mobile, et −15 % sur le
poids du GLB.

**2. Câbler les matières déjà disponibles** — `clearcoat`, `iridescence`,
`anisotropy` sont dans `MeshPhysicalMaterial` et ne demandent que d'être
activées. Le vernis à double lobe est le signal le plus immédiat de « ce site
a coûté cher ».

**3. Le défilement pilote des uniformes, jamais un re-rendu.** Coût négatif,
gain de fluidité direct. C'est la règle explicite de Shopify.

**4. Échelonnement machine à quatre niveaux et rapport de pixels plafonné.**
Nul sur desktop, énorme sur le taux de rebond mobile.

### Ensuite — effort moyen, résultat visible

**5. Peinture automobile en couches.** La référence ouverte est
[demo-2025-car-paint](https://github.com/Faraz-Portfolio/demo-2025-car-paint) :
paillettes par bruit de Voronoï **3D** modulant rugosité et métallicité,
couleur des paillettes variant avec l'angle par Fresnel, et **peau d'orange**
perturbant les normales du vernis. Ce dernier détail est celui que 90 % des
configurateurs oublient et qui trahit le rendu trop propre. L'auteur a
abandonné les rayures, trop coûteuses.

**6. Remplacer notre rebond unique par une convergence tracée hors ligne.**
[three-gpu-pathtracer](https://github.com/gkjohnson/three-gpu-pathtracer)
(MIT) rend environ 10 ms par échantillon, soit deux secondes pour deux cents
échantillons. **À utiliser comme cuiseur de build, pas comme moteur de
runtime.** On garde un coût runtime nul et on gagne les rebonds multiples et
le color bleeding physique.

**7. Sondes en harmoniques sphériques L1** pour que le pré-calcul cesse de
sentir le statique quand la caméra bouge. Quatre coefficients, pas neuf.

**8. Fusionner le post-traitement en une passe de composite unique.** Coût
négatif ; c'est ce que font Active Theory et Aircord.

### À ne pas faire maintenant

**WebGPU et le SSGINode.** three.js embarque bien un SSGI natif depuis r181
— un portage du composant Unity SSRT3. Mais il est en espace écran : **ce qui
est hors champ ne rebondit pas, et l'algorithme invente au-delà de la
géométrie visible**. Notre cuisson par lancer de rayons contre un arbre
d'englobants capte le hors-écran ; on échangerait de la justesse contre du
coût. Son auteur écrit lui-même que « le SSGI est en général un effet
coûteux ». Ajouter à cela : Safari ne supporte WebGPU qu'à partir d'iOS 26,
Chrome Android depuis la version 151 seulement, Firefox pas par défaut — et
une à deux semaines de réécriture en TSL de notre post-traitement.

**Les radiance cascades.** La seule implémentation three.js sérieuse est
publiée **sans licence, tous droits réservés**. Juridiquement inutilisable.

---

## 5. Ce qui reste ouvert

Quatre recherches ont été interrompues par une limite de session et doivent
être relancées :

- **le sourcing de modèles avec habitacle** et le droit des marques
  automobiles — la seule chose qui bloque encore la démonstration Clio ;
- **le pipeline Apple chiffré** — coût réel d'une séquence d'images ;
- **le tour photographique à 360°** — protocole de prise de vue et lecteurs
  existants ;
- **le plan d'allègement** de 13 Mo vers 2,3 Mo — Draco, Meshopt, KTX2,
  décimation.

---

## En une phrase

Notre cuisson au chargement nous place déjà du bon côté de la ligne : les
studios primés ne calculent pas d'éclairage global en temps réel non plus, ils
**pré-calculent davantage et échelonnent mieux**. L'écart n'est ni le SSGI ni
WebGPU — c'est la résolution de notre cuisson, la richesse de nos matières, et
le poids de nos pages.
