# HOLA ENERGY — site vitrine

Page unique pour une boisson énergisante, dans l'esprit des sites produit en
3D temps réel du secteur. Le scroll traverse une scène WebGL continue : les six
canettes défilent sur leur axe, la caméra plonge dans celle qui est active pour
lire les arguments imprimés sur le métal, puis recule vers la FAQ.

**La marque et le produit sont fictifs** — c'est une démo de design, pas le site
d'une entreprise existante.

## Aperçu

```bash
cd site && python3 -m http.server 8000
# http://localhost:8000
```

Un serveur est nécessaire : la scène est un module ES, que le navigateur refuse
de charger depuis `file://`.

## Arborescence

```
site/
  index.html            le site
  vendor/               three.js r185 (module + core)
  assets/labels/        artworks d'étiquettes, sources pleine résolution
  assets/web/           artworks remontés en 2528 px + environnement RGBE
  assets/fonts/         Anton et Archivo
  upscale_labels.py     régénère assets/web/label-*.jpg
  encode_env.py         convertit une HDRI Radiance en PNG RGBE
  build_artifact.py     produit une version d'un seul fichier dans dist/
```

## La chorégraphie

Le scroll ne déplace jamais directement la caméra ni les canettes. Il
échantillonne une **piste de plans** (`SHOTS`) — position et hauteur de caméra,
point visé, focale, écartement, échelle, inclinaison, balayage vertical — et la
boucle de rendu rattrape ces valeurs par interpolation à taux constant
(`1 - exp(-k·dt)`, indépendante du framerate). C'est ce retard qui donne
l'inertie : rien ne s'arrête net, et le parallaxe souris s'additionne sans
conflit.

Les actes, dans l'ordre : ouverture large, six saveurs (une par écran, chacune
imposant sa couleur au fond), plongée dans la canette, quatre arguments pendant
que la caméra remonte le long du métal, puis recul pour la FAQ et la
newsletter. Ajouter un plan revient à ajouter une entrée dans `SHOTS`.

## La canette

Aucun modèle 3D n'est téléchargé. La silhouette est un profil de 24 points aux
cotes d'une canette sleek 25 cl (Ø 58 mm, 133 mm) passé en `LatheGeometry` :
dôme concave du fond, cercle d'appui, épaule, rétreint du col, bord roulé. La
languette est un tore aplati, avec son rivet.

Le corps est en métal (`metalness` 0,85) : la couleur est imprimée sur
l'aluminium, elle n'est pas collée en papier.

## Les étiquettes

Deux textures par saveur, composées dans un `<canvas>` à 2528 × 1696 :

- **vitrine** — aplat teinté, reflet longitudinal, logotype Anton incliné
  rempli d'un dégradé argent, `ENERGY` en contour, goût à la verticale sur le
  flanc, mentions légales ;
- **arguments** — les quatre bénéfices empilés avec leur mention barrée, que la
  caméra remonte pendant la séquence.

La typographie est **tracée au code, jamais contenue dans l'image source** :
elle reste nette à n'importe quel grossissement, et renommer une saveur ne
demande pas de regénérer une texture. Les artworks de fruits ne servent plus
que de texture de fond à 16 %.

## Points d'implémentation à connaître

- **Couture du manchon** : `CylinderGeometry` place `u = 0` face caméra. Sans
  rotation, la couture tomberait au milieu du logotype — d'où le
  `sleeve.rotation.y = -π/2` qui amène `u = 0,25` de face.
- **Environnement** : une HDRI est indispensable, un JPEG plafonne à 1 et
  laisse le métal mou. Elle est encodée en RGBE — mantisse en haut, exposant en
  bas — plutôt que livrée en `.hdr`, ce qui éviterait de vendoriser
  `RGBELoader`. L'exposant n'est pas dans le canal alpha : un canvas 2D le
  prémultiplierait et détruirait les valeurs.
- **Taille du canvas** : `#webgl` doit garder ses `width`/`height` explicites.
  Un `<canvas>` est un élément remplacé — avec `inset:0` seul, il prend la
  taille de son buffer de dessin, soit le double de la fenêtre en DPR 2.
- **Reflets** : obtenus par duplication miroir des canettes sous un voile
  dégradé, pas par un rendu de réflexion.
- La page retombe sur un fond statique si le contexte WebGL est indisponible,
  et les animations sont neutralisées sous `prefers-reduced-motion`.

## Version d'un seul fichier

```bash
cd site && python3 build_artifact.py   # -> site/dist/index.html
```

three.js et les textures y sont repliés, sans aucune requête réseau. Le repli
n'est pas un `import` depuis une URL `data:` — une CSP stricte refuse ce schéma
pour les scripts. Les deux fichiers de la lib sont enveloppés chacun dans une
IIFE, sans quoi leurs noms minifiés de haut niveau entreraient en collision ;
leur `export {}` devient un `return {}`, et l'`import` du coeur devient une
déstructuration. Attention au `export {...} from "./three.core.min.js"` : c'est
une ré-exportation, elle ne crée pas de liaison locale.

## À brancher

Le formulaire newsletter valide l'adresse puis affiche une confirmation, sans
appel réseau. Pour le rendre réel, remplacer le corps du `submit` par un
`fetch` vers le service d'e-mailing choisi.
