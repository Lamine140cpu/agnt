================================================================================
ULTRA MOTION — DOSSIER DE PROJET
Prototype « canette » : site produit en 3D temps réel, parcouru au scroll
================================================================================

Ce fichier contient, dans l'ordre :

  1. ce qu'est le projet et où il en est ;
  2. l'architecture de la page et le principe de la chorégraphie ;
  3. la configuration livrée (marque, objet, variantes) ;
  4. la liste des pièges déjà rencontrés et de leur solution ;
  5. ce qui reste à faire.

Puis, après ce commentaire, **la page elle-même** : un seul fichier HTML,
CSS et JavaScript compris. C'est le prototype complet.


--------------------------------------------------------------------------------
1. LE PROJET
--------------------------------------------------------------------------------

**Ultra Motion** est un constructeur de sites vitrines en 3D temps réel. L'idée
produit : l'utilisateur décrit son activité, et trois IA se relaient —

  • une première conversationnelle, qui creuse le besoin et rédige le contenu ;
  • une deuxième générative, qui produit les visuels (étiquettes, matières) ;
  • une troisième qui construit la page, comme celle-ci.

Le prototype ci-dessous est le premier des trois exemples de la vitrine : une
marque d'energy drink fictive, **HOLA ENERGY**. Le visiteur descend la page et
traverse une scène WebGL continue : les six saveurs défilent sur leur axe, la
caméra plonge dans celle qui est active pour lire les arguments imprimés sur la
canette, puis recule vers la FAQ et l'inscription.

La référence de mouvement est le site de Ciao Energy. Sa chorégraphie a été
relevée image par image puis reproduite dans son principe : même architecture
d'amortissement (environ 200 ms), même entrée décalée du texte (+500 ms).
**Rien n'est copié de leur marque** : ni nom, ni logotype, ni artwork, ni
texte. HOLA est une marque inventée pour la démonstration.

Aucun modèle 3D n'est téléchargé, aucune bibliothèque au-delà de three.js.
Toute la géométrie est construite au code, toute la typographie est tracée
dans un canvas au moment du rendu.

État : le prototype fonctionne, en 60 fps sur une machine de bureau.


--------------------------------------------------------------------------------
2. ARCHITECTURE
--------------------------------------------------------------------------------

**Le moteur ne contient aucun contenu de marque.** La page lit un objet
`CONFIG` — replié juste en dessous de ce commentaire — et en déduit tout : le
nombre d'écrans, les arrêts de caméra, les secteurs d'arguments, la palette.
Concevoir un autre site revient à réécrire ce seul objet et à déposer les
images correspondantes.

  index.html        le moteur, sans contenu de marque
  site.config.js    la description du site : le seul fichier à écrire
  vendor/           three.js r185 (module + core), vendorisé, aucun CDN
  assets/web/       étiquettes en 2528 px, environnement HDRI encodé en RGBE
  assets/fonts/     Anton et Archivo
  build_artifact.py replie tout dans un fichier unique (~8 Mo)
  export_source.py  produit ce fichier-ci, lisible

**La chorégraphie.** Le scroll ne déplace jamais directement la caméra ni les
canettes. Il échantillonne une piste de plans (`SHOTS`) — position et hauteur
de caméra, point visé, focale, écartement, échelle, inclinaison, balayage
vertical — et la boucle de rendu rattrape ces valeurs par interpolation à taux
constant :

    k = 1 - exp(-taux · dt)

indépendante du framerate. C'est ce retard, et lui seul, qui donne l'inertie :
rien ne s'arrête net, et le parallaxe souris s'additionne sans conflit. C'est
aussi l'architecture qu'emploie Ciao, relevée dans leur source.

Les actes, dans l'ordre : ouverture large → une saveur par écran, chacune
imposant sa couleur au fond → un écran de transition pour la plongée → un
argument par écran pendant que la canette pivote → recul vers la FAQ et
l'inscription.

**La canette.** Un profil de 24 points aux cotes d'une sleek 25 cl (Ø 58 mm,
133 mm) passé en `LatheGeometry` : dôme concave du fond, cercle d'appui,
épaule, rétreint du col, bord roulé. La languette est un tore aplati avec son
rivet. Le col, le fond et la languette sont du métal nu ; le manchon
d'étiquette est un **diélectrique** (`metalness` 0,12), parce que c'est de
l'encre imprimée sur de l'aluminium et non du métal.

**Les étiquettes.** Deux textures par saveur, composées dans un `<canvas>` à
2528 × 1696 : une face vitrine (aplat teinté, reflet longitudinal, logotype
Anton incliné en dégradé argent, goût à la verticale, mentions légales) et une
face arguments (les quatre bénéfices avec leur mention barrée). La typographie
est tracée au code, jamais contenue dans l'image source : elle reste nette à
n'importe quel grossissement, et renommer une saveur ne demande pas de
regénérer une texture.

**Le post-traitement** est écrit à la main — bloom et profondeur de champ, en
trois cibles de rendu — plutôt qu'avec `EffectComposer`, dont les passes sont
des modules d'extension qu'il faudrait vendoriser. L'alpha est conservé de bout
en bout pour que le halo de couleur en CSS reste visible derrière la scène.


--------------------------------------------------------------------------------
3. CE QUE DÉCRIT LA CONFIGURATION
--------------------------------------------------------------------------------

    CONFIG = {
      brand   { name, accent, baseline, mention, menu }
      meta    { lang, title, description }
      theme   'light' | 'dark'
      artwork  préfixe des fichiers d'étiquette dans assets/web/
      object  { height, profile, label, tab, metal }
      items   [ { key, name, glow, tint, tagline }, … ]   une par écran
      claims  [ { title, crossed, body }, … ]             quatre au maximum
      faq     { title, items[] }
      signup  { … }
    }

`object.profile` est un profil de révolution, du centre du fond au centre du
couvercle. Décrire une bouteille, un pot ou un flacon revient à changer ces
points ; `object.tab` n'ajoute la languette que pour les canettes.

`claims` est plafonné à quatre : au-delà, les secteurs se chevauchent sur le
tour de la canette.


--------------------------------------------------------------------------------
4. PIÈGES RENCONTRÉS, ET LEUR SOLUTION
--------------------------------------------------------------------------------

Chacun de ces points a coûté un aller-retour. Ils valent d'être connus avant
de toucher au fichier.

• **Orange assombri = marron.** C'est la même couleur à luminosité près. Toute
  disparition doit donc désaturer avant d'éteindre — le halo en CSS comme la
  scène 3D, via un uniforme `desat` dans la passe de composition. Éteindre sans
  désaturer donnait une canette marron en fin de séquence.

• **Trop de reflets.** Le manchon était en `metalness` 0,85 : tout le corps
  renvoyait l'environnement, ce qui se cumulait aux dégradés déjà peints dans
  l'artwork. De l'encre imprimée est un diélectrique — 0,12.

• **Couture du manchon.** `CylinderGeometry` place `u = 0` face caméra ; sans
  rotation, la couture tombe au milieu du logotype. La coordonnée qui fait face
  à l'objectif vaut `0,25 − θ/2π` : composition et rotation dérivent de cette
  même formule.

• **Arguments répartis sur le tour, pas empilés.** Quatre blocs superposés
  tiennent tous dans le cadre à la fois, quel que soit le recul : on n'en isole
  jamais un. Un par secteur, et l'objet pivote.

• **Largeur du texte imprimé.** Une ligne plus large que l'arc réellement
  visible sort du cadre par les côtés, et reculer n'y change rien.

• **Environnement.** Une HDRI est indispensable : un JPEG plafonne à 1 et
  laisse le métal mou. Elle est encodée en RGBE — mantisse en haut de l'image,
  exposant en bas — plutôt que livrée en `.hdr`, ce qui éviterait de vendoriser
  `RGBELoader`. L'exposant n'est **pas** dans le canal alpha : un canvas 2D le
  prémultiplierait et détruirait les valeurs.

• **Taille du canvas.** `#webgl` doit garder ses `width`/`height` explicites en
  CSS. Un `<canvas>` est un élément remplacé : avec `inset:0` seul, il prend la
  taille de son buffer de dessin, soit le double de la fenêtre en DPR 2.

• **Cibles de post-traitement en pixels physiques**, pas en pixels CSS. Les
  allouer en CSS revenait à rendre la scène en 1× puis à l'étirer sur un canvas
  deux à trois fois plus fin — d'où un flou général inexplicable.

• **Reflets au sol** : obtenus par duplication miroir des canettes sous un
  voile dégradé, pas par un rendu de réflexion.

• **Plongée sur son propre écran.** Sans cet écran de transition, la caméra se
  rapprochait pendant que le titre de la dernière saveur était encore lisible.

• **Repli d'un seul fichier** : le repli de three.js n'est pas un `import`
  depuis une URL `data:` — une CSP stricte refuse ce schéma pour les scripts.
  Les deux fichiers de la lib sont enveloppés chacun dans une IIFE, sans quoi
  leurs noms minifiés de haut niveau entrent en collision ; leur `export {}`
  devient un `return {}`. Attention au `export {…} from "./three.core.min.js"` :
  c'est une ré-exportation, elle ne crée pas de liaison locale.

• **Accessibilité et repli** : la page retombe sur un fond statique si le
  contexte WebGL est indisponible, et les animations sont neutralisées sous
  `prefers-reduced-motion`.


--------------------------------------------------------------------------------
5. CE QUI RESTE À FAIRE
--------------------------------------------------------------------------------

• Le formulaire d'inscription valide l'adresse puis affiche une confirmation,
  sans appel réseau. Le brancher revient à remplacer le corps du `submit` par
  un `fetch` vers le service d'e-mailing retenu.

• Les artworks de fruits ne servent plus que de fond à 16 % : ils pourraient
  porter davantage si les sources étaient regénérées sans texte incrusté.

• Version mobile : la piste de plans est calée sur un format paysage.


--------------------------------------------------------------------------------
POUR FAIRE TOURNER LA PAGE
--------------------------------------------------------------------------------

Ce fichier-ci est la **source lisible** : il référence encore `./vendor/` pour
three.js et `./assets/` pour les images, et se sert donc depuis le dépôt.

    cd site && python3 -m http.server 8000    →  http://localhost:8000

Un serveur est nécessaire : la scène est un module ES, que le navigateur refuse
de charger depuis `file://`.

La version autonome — three.js et toutes les textures repliés, aucune requête
réseau, ouvrable d'un double-clic — se produit avec :

    python3 build_artifact.py index.html      →  site/dist/index.html (~8,4 Mo)

HOLA ENERGY est une marque et un produit **fictifs**, créés pour cette
démonstration.

================================================================================
