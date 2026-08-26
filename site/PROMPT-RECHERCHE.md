# Prompt à soumettre à Claude Research

*(tout ce qui suit est à copier-coller tel quel)*

---

## Contexte

Je construis des sites vitrines pour des PME françaises (transporteurs,
artisans, commerces). La signature du produit : **un film qui se déroule au
défilement**. Le visiteur scrolle, une séquence d'images défile image par
image, en plein écran, avec du texte qui apparaît par-dessus. Une seule page,
trente écrans de haut. Référence du genre : velaarmon.com, les pages produit
d'Apple, les lauréats Awwwards à « scrollytelling ».

Je vends ça à des boîtes qui n'ont pas de budget d'agence. Contraintes non
négociables :

- **hébergement statique uniquement** (pas de serveur, pas de backend, pas de
  traitement à la demande — GitHub Pages / Cloudflare Pages / Netlify) ;
- **doit tenir sur un téléphone milieu de gamme en 4G** ;
- **une seule page HTML autonome**, pas de framework, pas de dépendance CDN ;
- le film est **généré** (modèles de génération vidéo par IA), pas filmé.

## Mon architecture actuelle, précisément

Un `<canvas>` 2D fixe en plein écran. Une séquence de N fichiers AVIF (nommés
`.jpg`, le navigateur reconnaît le format aux octets). Une fenêtre glissante :
au fur et à mesure du défilement on télécharge, on décode via
`createImageBitmap` (donc hors du fil principal), on garde une bande d'images
autour de la position courante, on purge le reste en appelant `close()`.
Le dessin se fait en « couvrir », avec un fondu entre les deux images qui
encadrent la position fractionnaire courante.

Deux séquences par site : une 16:9 pour les écrans larges, une 9:16 pour les
téléphones, choisie au chargement.

Chiffres réels d'un site en production :
- 791 images 1920 × 1080 en AVIF q45 → **34 Mo** au total, ~42 ko l'image ;
- plus 527 images 720 × 1280 pour la version téléphone ;
- densité de défilement : **33 pixels de scroll par image** (à 1000 px/s de
  défilement, cela fait 30 changements d'image par seconde) ;
- page HTML : 70 ko, 22 ko en gzip.

## Ce que j'ai déjà mesuré — inutile d'y revenir

Mesures faites au navigateur (Chromium), machine au repos, **sans carte
graphique** (conteneur Linux 4 cœurs). Valeurs absolues pessimistes, rapports
valides.

**Décodage et dessin, image 1920 × 1080 :**

| opération | durée |
|---|---|
| requête HTTP, cache froid | 16,7 ms |
| requête HTTP, cache chaud | 7,9 ms |
| décodage AVIF q45 (42 ko) | 62,8 ms |
| décodage WebP q82 (90 ko) | 44,0 ms |
| décodage JPEG q82 (156 ko) | 49,2 ms |
| `drawImage` au rapport 1:1 | 1,3 ms |
| `drawImage` en agrandissant vers 3200 × 1800, filtre « high » | 184 ms |

**Vidéo contre séquence d'images, à qualité mesurée (PSNR contre les sources) :**

| | poids | PSNR |
|---|---|---|
| 791 fichiers AVIF q45 | 34 Mo | 39,9 dB |
| VP9 CRF 30, GOP 12 | 29 Mo | 38,1 dB |

Le saut à une position quelconque dans la vidéo : 6,3 ms en moyenne, 37 ms au
pire. Le débit en lecture accélérée : 20 images/s en décodage logiciel.

**Conclusions déjà tirées, à ne pas rejouer :**

1. Passer à la vidéo `<video>` ne rapporte que 15 % de poids et fait perdre
   l'accès image par image (on ne peut pas préparer une fenêtre glissante).
2. WebCodecs `VideoDecoder` est disponible partout (Safari 26+) mais impose de
   démultiplexer le MP4 soi-même et de décoder depuis l'image-clé précédente.
3. `createImageBitmap(blob, {resizeWidth})` redimensionne **après** le
   décodage : ça ne l'accélère pas (17,7 ms → 24-37 ms), ça ne réduit que la
   mémoire.
4. Garder les octets compressés en mémoire pour ne re-décoder qu'au lieu de
   re-télécharger économise 8 ms sur 70. Marginal.
5. WebP décode 30 % plus vite qu'AVIF mais pèse 2,1× plus.
6. `OffscreenCanvas` + `Worker` n'a plus d'objet : le décodage était déjà hors
   fil principal et le dessin coûte 1,3 ms.
7. `alpha:false` et `desynchronized:true` sont déjà posés sur le contexte.
8. Le plafond de densité de pixels doit être borné à la définition du film,
   sinon on agrandit pour rien (c'est ce qui faisait tomber la page à 4 i/s).
9. Hébergement : GitHub Pages impose `cache-control: max-age=600`, donc le
   film est re-téléchargé à chaque visite espacée. Je sais qu'il faut changer
   d'hébergeur.

## L'historique, qui explique ma question

Avant cette architecture, je faisais de la **3D temps réel** : modèles glTF
compressés (Draco, meshopt), éclairage par image d'environnement, puis des
gaussian splats. Ça ne tenait pas la route sur téléphone et la qualité visuelle
plafonnait très en dessous de ce que je voulais.

Je suis « tombé » sur la séquence d'images en cherchant autre chose. Le saut
de qualité a été énorme. **Je suis convaincu qu'il existe un autre saut du même
ordre que je ne connais pas**, parce que je ne sais pas quoi chercher. Les
optimisations incrémentales de mon architecture actuelle, je sais les faire.

---

# Ce que je te demande

Ne me confirme pas ce que je fais déjà. **Cherche ce que je ne connais pas.**
Sois exhaustif, cite tes sources, donne des chiffres et des dates, et distingue
clairement ce qui est disponible aujourd'hui en production de ce qui est
expérimental ou derrière un drapeau.

## 1. Le primitif est-il le bon ?

Une séquence d'images pré-rendues est-elle encore, en 2026, la bonne
représentation pour « un mouvement continu, ultra-défini, piloté par le
défilement, sur hébergement statique » ? Quelles autres représentations existent
aujourd'hui et où en est chacune :

- représentations neuronales / implicites d'une séquence, décodées côté client ;
- 3D Gaussian Splatting en 2026 — les formats compressés récents, le poids réel
  d'une scène, les performances sur téléphone (j'ai abandonné il y a un moment,
  le domaine a peut-être bougé) ;
- une vidéo rendue comme **texture WebGL/WebGPU** plutôt que dessinée sur un
  canvas 2D, avec l'échantillonnage piloté par le défilement ;
- un rendu procédural / shader qui n'aurait aucun asset à télécharger ;
- toute autre approche que je n'ai pas nommée.

Pour chacune : poids réel, tenue sur téléphone, compatibilité navigateurs,
et surtout **ce que ça coûte à produire**.

## 2. Les pistes que je soupçonne sans les connaître

Confirme, infirme, chiffre :

- **`ImageDecoder` de WebCodecs** — permet-il de lire un AVIF ou WebP **animé**
  image par image avec accès aléatoire ? Si oui, un seul fichier au lieu de 791,
  avec la compression inter-image ET l'accès direct : ce serait exactement ce
  qui me manque. Quel est le coût réel d'un accès aléatoire ? Quel support ?
- **Textures compressées GPU** (Basis Universal, KTX2, ASTC, BC7) : transcodage
  rapide, la carte graphique garde la texture compressée, l'empreinte mémoire
  tombe d'un facteur 4 à 8 par rapport à du RGBA décodé. Est-ce viable pour une
  séquence de plusieurs centaines d'images ? Quel poids sur le réseau comparé à
  de l'AVIF ? Qui l'a déjà fait ?
- **Interpolation d'images côté client** : livrer une image sur quatre et
  synthétiser les intermédiaires dans le navigateur (façon RIFE / FILM) via
  WebGPU ou WASM. Faisable en temps réel en 2026 ? À quel coût ? Y a-t-il des
  implémentations web publiées ?
- **Super-résolution côté client** : livrer du 960 px et remonter à 1920 avec un
  petit réseau en shader WebGPU, ou avec des techniques temporelles type DLSS
  (accumulation entre trames successives). Existe-t-il des implémentations web ?
- **Codecs progressifs** : JPEG XL en décodage progressif, AVIF en couches —
  afficher immédiatement une version grossière et l'affiner. Où en est le
  support navigateur réellement, en 2026 ?
- **Compression inter-image sans perdre l'accès aléatoire** : dictionnaire
  Brotli partagé entre toutes les images de la séquence (`Compression
  Dictionary Transport`), ou un schéma image-clé + résidus décodés sur GPU.
  Ça existe ? Quelqu'un l'a fait pour ce cas d'usage ?
- **Animations pilotées par le défilement en CSS natif**
  (`animation-timeline: scroll()`) : peut-on les combiner avec un canvas pour
  sortir la synchronisation du fil principal ?

## 3. L'état de l'art réel

Démonte techniquement les sites qui font ça le mieux aujourd'hui. Pas des
articles de blog génériques — **regarde ce que font réellement les sites**, et
si possible cite le code ou les requêtes réseau :

- Apple (pages produit à séquence défilante) : combien d'images, quel format,
  quelle définition, quelle stratégie de préchargement, en 2026 ;
- velaarmon.com ;
- les lauréats Awwwards / FWA récents en « scrollytelling » ;
- les studios qui publient leur outillage (Active Theory, Lusion, Locomotive,
  Studio Freight / Lenis, 14islands…) ;
- les bibliothèques dédiées à ce cas : que valent-elles, et surtout **quelles
  décisions techniques prennent-elles que je ne prends pas ?**

## 4. La perception, pas la technique

- À partir de combien de changements d'image par seconde l'œil ne distingue-t-il
  plus rien de plus, sur un mouvement de caméra lent ? Je travaille à 30, est-ce
  du gaspillage ou est-ce insuffisant ?
- Le fondu entre deux images voisines suffit-il à masquer une cadence basse, et
  jusqu'où ? Y a-t-il des travaux publiés là-dessus ?
- Quelle est la limite réelle de perception de la définition sur un téléphone
  tenu à bout de bras ? Est-ce que du 1440 px sert à quelque chose face à du
  1080 px, en mouvement ?
- Y a-t-il des techniques de dithering temporel ou de flou directionnel qui
  permettraient de livrer **beaucoup moins d'images** sans que ça se voie ?

## 5. La production, qui est ma vraie limite

Le film est généré par des modèles image-vers-vidéo. Mon problème : produire
plusieurs plans qui s'enchaînent **sans rupture visuelle** et qui gardent la
cohérence d'un sujet (un camion avec une livrée précise, par exemple) d'un plan
à l'autre.

- Où en sont, en 2026, le contrôle de trajectoire de caméra et la cohérence de
  sujet dans les modèles de génération vidéo ? Quels modèles, quelles méthodes ?
- Y a-t-il de meilleures manières que le chaînage naïf (dernière image d'un plan
  = première image du suivant) ?
- Quel est l'état de l'agrandissement vidéo par IA aujourd'hui, et à quel
  moment de la chaîne faut-il le placer ?

## 6. Enfin, le doute utile

**Le film défilant est-il seulement la bonne idée pour ces clients ?** Un
transporteur routier veut être appelé par quelqu'un qui cherche « transporteur
palette Aulnay ». Que disent les données publiées sur ce qui convertit
réellement sur un site vitrine de PME locale — vitesse de chargement, longueur
de page, position du téléphone, référencement local ? Est-ce que trente écrans
de film aident ou nuisent ? Si les données disent que ça nuit, dis-le-moi
franchement, avec les sources.

---

## Forme de la réponse attendue

- Chaque affirmation technique adossée à une source datée.
- Des chiffres : poids, millisecondes, compatibilité navigateur avec versions.
- Une distinction nette entre « disponible en production », « derrière un
  drapeau », « article de recherche sans implémentation ».
- Pour chaque piste retenue : ce qu'elle coûterait à mettre en œuvre, et
  comment je peux la **tester en une journée** pour trancher.
- À la fin : ton classement personnel des pistes, de la plus prometteuse à la
  moins, avec le raisonnement.

Si une de mes conclusions ci-dessus est fausse, dis-le et montre pourquoi.
