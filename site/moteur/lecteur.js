/* ============================================================================
   LE LECTEUR — la source unique.

   Ce fichier était recopié dans chaque page. Mesuré avant de l'extraire : six
   versions différentes du même lecteur cohabitaient dans ce dépôt, divergeant
   de 8 à 13 % — les cinq refontes et la vitrine tournaient sur un moteur qui
   n'avait aucun des correctifs de fluidité, de cadrage ni de définition. Le
   dépôt le disait déjà lui-même : « un correctif de fluidité avait dû être
   porté trois fois de suite ».

   Il n'est PAS chargé par <script src>. La construction l'insère dans la page,
   à la place du marqueur <!--LECTEUR-->. Un site client tient sur une seule
   page : une requête de plus avant que le film ne démarre coûterait un
   aller-retour à chaque visite, pour un cache que personne ne réutiliserait.
   Une seule source, zéro requête : les deux à la fois.

   CE QUE LA PAGE DOIT FOURNIR, sous peine d'écran noir silencieux :

     window.SERIES     { clé: { chemin, images } } — déclaré AVANT le lecteur
     #toile            la toile du film
     #prologue         contenant des <section> : les actes
     #suite            les blocs révélés au défilement, OPAQUES
     #voile #etape #jauge #pct     l'écran d'attente

   Les clés de `window.SERIES` sont « accueil » et « accueil-etroit ». Ce sont
   des rôles, pas des noms de client : la première est servie aux toiles larges,
   la seconde sous 820 px.
   ============================================================================ */
/* ============================================================================
   Le prologue est un film déroulé par le défilement.

   Aucune 3D ici : une toile en deux dimensions, et le défilement décide quelle
   image y est peinte. Les images viennent de notre propre scène, calculée hors
   ligne. On échange le calcul chez le visiteur contre du transfert — et on
   gagne une qualité que le temps réel ne donnera jamais.

   Deux difficultés, deux réponses :

   1. La séquence entière est trop lourde pour être chargée d'un bloc. D'où la
      FENÊTRE GLISSANTE : on ne garde que les images proches de celle qu'on
      regarde, on précharge devant, on jette derrière.

   2. Décoder une image bloque le fil principal et fait saccader le défilement.
      D'où createImageBitmap, qui décode ailleurs et rend un objet que la toile
      dessine sans retravail.
   ============================================================================ */
/* ------------------------------------------- LES INTERRUPTEURS DE L'ADRESSE

   Ce lecteur a été réglé sur une machine SANS CARTE GRAPHIQUE. Tout ce qui
   dépend du GPU y est donc invisible : le coût d'une texture, la pression sur
   la mémoire graphique, le chemin de composition d'une toile opaque. Mesuré
   ici, la page tient 60 i/s en 1080p et 30 en 1440p — mais c'est le
   compositeur logiciel qui parle, et il ne dit rien d'un vrai PC.

   Deviner à distance ce qui coûte sur la machine d'un visiteur ne marche pas.
   On lui donne donc de quoi le MESURER, une hypothèse par interrupteur :

     ?diag=1        affiche cadence, régularité, retard du décodeur, mémoire
     ?molette=0     rend la molette au navigateur (coupe notre lissage)
     ?memoire=N     plafonne les images décodées à N mégaoctets
     ?alpha=1       toile transparente au lieu d'opaque

   Chacun isole une cause. Si `?memoire=192` fait repartir une machine qui
   ramait, c'est la mémoire graphique ; si c'est `?alpha=1`, c'est le chemin de
   composition ; si c'est `?molette=0`, c'est nous. Trois réponses qu'aucune
   mesure faite ici ne pouvait donner. */
const REGLAGES = new URLSearchParams(location.search);
const canvas = document.getElementById('toile');
/* alpha:false — la toile est opaque, le navigateur n'a pas à la composer avec
   ce qu'il y a dessous. desynchronized:true — on renonce à la synchronisation
   stricte avec le reste de la page, ce qui réduit la latence du geste.

   Les deux sont des PARIS sur le comportement du compositeur, pas des mesures :
   une toile opaque et plein écran peut aussi bien être promue en surcouche que
   retomber sur un chemin lent, et rien ici ne permet de trancher. D'où
   `?alpha=1`, qui laisse la machine du visiteur répondre. */
const ctx = canvas.getContext('2d', {
  alpha: REGLAGES.get('alpha') === '1',
  desynchronized: true,
});
const voile = document.getElementById('voile');
const jauge = document.getElementById('jauge');
const pct = document.getElementById('pct');
const etape = document.getElementById('etape');
const { min, max, round, abs, exp } = Math;
const borne = (v, a, b) => v < a ? a : (v > b ? b : v);

/* Deux tailles du MÊME montage.

   La note qui tenait ici affirmait que la série étroite était « un vrai
   montage », plusieurs plans ayant été tournés nativement en 9:16. C'était
   faux. Reconstruit ici un rognage centré 9:16 du maître et comparé image par
   image à la série étroite : écart médian 1,4 sur 255, soit le bruit de
   recompression JPEG. C'était un rognage, qui ne gardait que 32 % de la
   largeur du film — et le client a fini par le dire : « sur téléphone c'est
   trop zoomé ».

   La série téléphone est donc désormais le maître ENTIER, en 1440 px de large
   au lieu de 1920 : la toile du téléphone fait 585 x 810 pixels d'appareil,
   une image 1440x810 s'y pose sans agrandissement.

   Elle compte moins d'images que la large, et ce n'est pas une économie :
   sur un téléphone les actes font deux écrans au lieu de trois, ce qui met
   la course du prologue à 10 297 px contre 15 300. Deux tiers de la
   distance demandent deux tiers des images pour le même grain. La
   construction calcule ce partage toute seule. */
/* LES ÉLÉMENTS QUE LA PAGE DOIT FOURNIR, vérifiés nommément.

   Sans ce contrôle, une page à qui il en manque un plante sur un « Cannot read
   properties of null » quelque part au milieu du lecteur, et la toile reste à
   sa taille par défaut — 300 x 150, invisible sur un fond noir. C'est arrivé
   en écrivant la troisième page : `jauge` avait été posé comme CLASSE du
   conteneur alors que c'est l'IDENTIFIANT de la barre intérieure. Le message
   ne disait rien, et il a fallu comparer deux pages ligne à ligne.

   Le nom manquant est maintenant dit. */
{
  const requis = { toile: canvas, voile, jauge, pct, etape,
                   prologue: document.getElementById('prologue') };
  const absents = Object.keys(requis).filter(k => !requis[k]);
  /* ET LA TOILE DOIT AVOIR UNE BOÎTE. Une toile sans règle CSS reste à sa
     taille par défaut — 300 x 150 px, en position statique — et la page
     s'affiche vide sans une seule erreur. C'est exactement ce qui est arrivé
     en écrivant la troisième page : la règle `#toile` manquait au socle, les
     deux premiers sites en avaient chacun une copie, donc la page neuve n'en
     avait aucune. Le contrôle coûte deux lignes et supprime le pire mode de
     panne de ce lecteur. */
  const _b = canvas.getBoundingClientRect();
  if (getComputedStyle(canvas).position === 'static' &&
      _b.width === 300 && _b.height === 150) {
    throw new Error('#toile n\'a aucune règle CSS : elle est restée à sa ' +
      'taille par défaut de 300x150 en position statique, et la page ' +
      's\'afficherait vide. Le socle doit la fournir.');
  }
  if (absents.length) {
    throw new Error('le lecteur ne trouve pas #' + absents.join(', #') +
      ' — la page doit les fournir. Attention au nid : `jauge` est ' +
      "l'identifiant du <b> À L'INTÉRIEUR de .jauge, pas celui du conteneur.");
  }
}

const SEQUENCES = window.SERIES;
if (!SEQUENCES || !Object.keys(SEQUENCES).length) {
  /* Sans séries, la toile reste noire et RIEN ne le dit : c'est le pire mode
     de panne de ce lecteur, et il s'est produit trois fois dans ce dépôt.
     On le rend bruyant. */
  throw new Error('le lecteur n\'a pas trouvé window.SERIES — la page doit ' +
                  'déclarer ses séries avant de le charger');
}
/* La construction dépose les images ici ; sans elle on va les lire sur le
   disque. Le lecteur n'a pas à savoir lequel des deux. */
const SOURCES = (typeof window.__FILM === 'object' && window.__FILM) || null;

/* La série se choisit sur la largeur du CADRE, pas sur celle de la fenêtre :
   une mise en page peut n'accorder au film qu'une colonne d'un écran large, et
   y servir la grande série serait payer 1920 px pour en afficher 600.

   La toile n'a pas encore de taille au moment où ces lignes s'exécutent si le
   CSS ne lui en donne pas ; d'où le repli sur la fenêtre. */
const _cadre = canvas.getBoundingClientRect();
/* LE CHOIX DE SÉRIE — deux critères, dans cet ordre : la forme, puis le poids.

   Aucune règle simple ne suffit, parce que les films ne sont pas tous faits
   pareil, et c'est mesuré :

     Trans Gold      la série étroite est un RECADRAGE de la large. Écart
                     médian au rognage centré reconstruit : 1,4 sur 255, soit
                     le bruit de recompression. Les deux montrent donc le même
                     cadre, et seule la définition les sépare.
     la vitrine      la série étroite est un VRAI MONTAGE. Écart 43 à 54 sur
                     255 sur les quatre cinquièmes du film. Les deux montrent
                     des images différentes, composées pour leur format.

   Choisir par la largeur de la toile — juste pour le premier — servirait au
   second une image large là où un montage portrait l'attendait. Choisir par la
   forme seule — juste pour le second — ferait payer au premier 1920 px pour en
   afficher 600 sur un téléphone.

   D'où la règle en deux temps :

     1. LA FORME. On garde les séries dont le rapport est le plus proche de
        celui de la toile. Quand un film a été monté pour le portrait, c'est ce
        critère qui le trouve ; quand les deux séries ont le même rapport —
        Trans Gold — elles restent toutes les deux en lice et le second
        critère tranche.

     2. LE POIDS. Parmi elles, la PLUS PETITE qui couvre la toile sans
        agrandissement. Agrandir coûte le remplissage, qui est le poste le plus
        cher du lecteur : 184 ms l'image contre 1,3 en 1:1. Et servir plus
        large que nécessaire double la charge mobile pour un rendu identique.
        Si aucune ne suffit, la plus grande — mieux vaut un peu de flou qu'un
        agrandissement de toile.

   Chaque série déclare ses DEUX dimensions réelles, jamais un rapport. Écrit
   d'abord avec un rapport arrondi, le second critère se trompait de justesse :
   1440 / 1,778 donne 809,9, et la série de 810 px de haut était jugée trop
   courte pour une toile de 810 — le téléphone recevait alors la pellicule de
   1920, soit le double de la charge mobile. Un arrondi qui décide n'est pas un
   arrondi.

   Une série qui ne déclare pas ses dimensions reste choisie à l'ancienne, par
   la largeur de la toile : les pages non migrées continuent de fonctionner. */
const _cw = _cadre.width || innerWidth;
const _ch = _cadre.height || innerHeight;
const _dispo = Object.keys(SEQUENCES)
  .filter(k => !SOURCES || SOURCES[k]);
const _decrites = _dispo.filter(k => SEQUENCES[k].largeur && SEQUENCES[k].hauteur);

let NOM;
if (_decrites.length) {
  const rc = _cw / _ch;
  const ecart = k => Math.abs(Math.log((SEQUENCES[k].largeur / SEQUENCES[k].hauteur) / rc));
  const meilleur = Math.min(..._decrites.map(ecart));
  /* Le rapport se compare en LOGARITHME : sans cela, deux séries à 0,56 et
     1,78 face à une toile à 1,0 donneraient des écarts de 0,44 et 0,78, alors
     qu'elles sont à distance égale — l'une est deux fois plus haute que large,
     l'autre deux fois plus large que haute. */
  const memeForme = _decrites.filter(k => ecart(k) <= meilleur + 0.01);

  /* TROISIÈME CRITÈRE, découvert par le troisième site : une série doit avoir
     ASSEZ D'IMAGES pour la course de la page où elle est servie.

     La pellicule légère est taillée pour la course du téléphone. Sur une
     fenêtre de 900 px de large elle couvrait la toile et pesait moins, donc
     elle gagnait — mais la page y garde la course du bureau, et 527 images sur
     23 200 px font 44 px de défilement par image : le film saute. Le poids ne
     se juge pas seul, il se juge à densité tenue. */
  const _prol = document.getElementById('prologue');
  const _course = _prol ? Math.max(_prol.offsetHeight - innerHeight, 1) : 0;
  const _dmax = window.DENSITE_MAX || 40;
  const assez = k => !_course || !SEQUENCES[k].images ||
                     _course / SEQUENCES[k].images <= _dmax;

  const plafond = _cw < 820 ? 1.5 : 2;
  const besoinL = _cw * Math.min(devicePixelRatio || 1, plafond);
  const besoinH = _ch * Math.min(devicePixelRatio || 1, plafond);
  /* DEUX POUR CENT DE TOLÉRANCE, et ce n'est pas de la mollesse.

     Sans elle, une pellicule taillée exactement pour la toile la rate d'un
     quart de pixel. Mesuré : la toile du téléphone fait 64 svh de 844, soit
     540,156 points, donc 810,23 pixels d'appareil — et la série de 810 px de
     haut, calculée pour ce cas précis, était jugée trop courte. Le téléphone
     recevait alors la pellicule de 1920 : le double de la charge mobile, pour
     un quart de pixel.

     C'est la troisième fois qu'une décision au pixel près se trompe dans ce
     seul bloc — après le rapport arrondi à 1,778. Un ajustement exact ne
     survit ni aux hauteurs de fenêtre variables, ni aux barres du navigateur,
     ni au zoom. Deux pour cent d'agrandissement ne se voient pas ; recevoir la
     mauvaise série, si. */
  const couvre = k => SEQUENCES[k].largeur >= besoinL * 0.98 &&
                      SEQUENCES[k].hauteur >= besoinH * 0.98;
  const suffisantes = memeForme.filter(k => couvre(k) && assez(k));
  /* Si aucune ne tient les deux, on retombe sur celles qui couvrent, puis sur
     la forme seule : mieux vaut une image un peu trop grande qu'un film qui
     saute, et un film qui saute qu'une page vide. */
  const parmi = suffisantes.length ? suffisantes
              : (memeForme.filter(couvre).length ? memeForme.filter(couvre) : memeForme);
  NOM = parmi.reduce((a, b) =>
    (suffisantes.length ? SEQUENCES[a].largeur <= SEQUENCES[b].largeur
                        : SEQUENCES[a].largeur >= SEQUENCES[b].largeur) ? a : b);
} else {
  const etroit = _cw < 820;
  NOM = (etroit && (!SOURCES || SOURCES['accueil-etroit']))
    ? 'accueil-etroit' : 'accueil';
}
/* ============================================================================
   LE DÉBIT EST UN CRITÈRE, AU MÊME TITRE QUE LA DÉFINITION.

   Tout ce qui précède choisit la série la plus fine que la toile puisse
   afficher sans agrandissement. C'était juste tant qu'on supposait les images
   arrivées. Un visiteur mesuré a montré que non :

       fenêtre 1280 x 551, densité 1,5  ->  1920 px demandés
       série servie : 1200 images à 42,8 Ko  ->  15 Mbit/s à 1000 px/s
       ligne réelle : 10 Mbit/s
       résultat     : 79 % des trames n'avaient AUCUNE image à montrer

   Soixante images par seconde, et un film qui ne bouge pas. Le lecteur avait
   préféré la NETTETÉ au fait que le film se joue — et il ne pouvait pas faire
   autrement, rien ne lui disait ce qu'une série coûte à télécharger.

   La série légère de ce même site tenait dans 7 Mbit/s : 803 images au lieu de
   1200 — donc moins d'images par seconde à la même vitesse — et 29 Ko au lieu
   de 43. Elle serait un peu moins nette sur une image arrêtée. Elle serait
   SURTOUT visible en mouvement, ce qui n'était pas le cas de l'autre.

   On estime donc le débit disponible et on écarte les séries qu'il ne peut pas
   nourrir. Deux sources, et la seconde corrige la première :

     1. `navigator.connection.downlink`, tout de suite — une indication, pas une
        mesure : le navigateur la lisse sur l'historique récent et l'arrondit.
     2. le débit RÉELLEMENT obtenu pendant l'amorçage, qui remplace l'estimation
        avant que la page ne se révèle (voir `arbitrer`, plus bas).

   VITESSE DE RÉFÉRENCE : 1000 px/s. C'est un défilement franc et tenu, pas un
   geste de démonstration. Dimensionner sur un défilement lent reviendrait à
   dimensionner pour le cas où le défaut ne se voit pas.
   ============================================================================ */
const VITESSE_REF = 1000;

/** Ce qu'une série exige, en mégabits par seconde, à la vitesse de référence. */
function exigence(k, courseVue){
  const s = SEQUENCES[k];
  if (!s.octets || !s.images || !courseVue) return 0;
  const parImage = courseVue / max(s.images - 1, 1);
  return (VITESSE_REF / parImage) * s.octets * 8 / 1e6;
}

/**
 * Le débit qu'on croit avoir AVANT d'avoir rien téléchargé. `?debit=N` le
 * force, pour pouvoir éprouver la décision sans truquer le réseau.
 *
 * `downlink` N'EST PAS UNE MESURE, ET NE SERT PLUS ICI. Chrome le plafonne à
 * 10 Mbit/s pour limiter le pistage, l'arrondit, et le lisse sur l'historique
 * récent — si bien qu'il décrit les pages d'avant plutôt que la ligne du
 * moment. Éprouvé sur réseau LIBRE : il annonçait 1,55 Mbit/s quand le débit
 * réellement obtenu était 40,8. La page rétrogradait donc sur fibre.
 *
 * Ce n'était pas seulement faux, c'était IRRÉVERSIBLE : la rétrogradation
 * tombait avant le premier téléchargement, et rien ensuite ne remonte. Une
 * indication douteuse qui décide avant la mesure est pire qu'une absence
 * d'indication — celle-ci, au moins, laisse mesurer.
 *
 * Ne reste donc que ce qui est SÛR : `saveData`, qui n'est pas une estimation
 * mais une demande explicite du visiteur. Tout le reste attend l'amorçage.
 */
function debitEstime(){
  const force = parseFloat(REGLAGES.get('debit'));
  if (Number.isFinite(force) && force > 0) return force;
  if (navigator.connection && navigator.connection.saveData) return 2;
  return Infinity;                       // sans mesure, on ne dégrade pas
}

/**
 * Retient la série la plus fine que le débit puisse NOURRIR.
 *
 * Si aucune ne passe, on garde la plus légère : à ce moment-là le choix n'est
 * plus entre net et moins net, il est entre un film et un diaporama.
 */
function selonDebit(candidates, debit, courseVue){
  if (!isFinite(debit) || candidates.length < 2) return null;
  const tiennent = candidates.filter(k => {
    const e = exigence(k, courseVue);
    return !e || e <= debit;
  });
  if (tiennent.length)
    return tiennent.reduce((a, b) => SEQUENCES[a].largeur >= SEQUENCES[b].largeur ? a : b);
  return candidates.reduce((a, b) =>
    (exigence(a, courseVue) || Infinity) <= (exigence(b, courseVue) || Infinity) ? a : b);
}

{
  /* La course n'est pas encore mesurée ici — `mesurer()` tourne plus tard — mais
     le prologue existe déjà, ce qui suffit à l'estimer. */
  const _prol2 = document.getElementById('prologue');
  const _courseVue = _prol2 ? max(_prol2.offsetHeight - innerHeight, 1) : 0;
  const _debit = debitEstime();
  const _mieux = selonDebit(_dispo, _debit, _courseVue);
  if (_mieux && _mieux !== NOM && exigence(NOM, _courseVue) > _debit) NOM = _mieux;
}

/* `let` et non `const` : l'amorçage peut changer de série une fois le débit
   réel connu, et il le fait avant que la page ne se révèle. */
let SEQ = SEQUENCES[NOM];
/* Le compte écrit ci-dessus n'est qu'un défaut pour le mode disque : dès que
   la construction a injecté les images, c'est elle qui a raison. Sans ça, une
   série plus longue s'arrêterait avant la fin et le dernier tiers du
   défilement resterait figé sur la même image. */
if (SOURCES && SOURCES[NOM]) SEQ.images = SOURCES[NOM].length;

/* Le type déclaré doit être le vrai. L'écrire en dur marchait tant que le
   navigateur reniflait les octets — rien ne l'y oblige, et un navigateur
   strict rejette alors le lot entier, donc une page noire. */
function typeDe(u){
  if (u[0] === 0xFF && u[1] === 0xD8) return 'image/jpeg';
  if (u[8] === 0x57 && u[9] === 0x45 && u[10] === 0x42 && u[11] === 0x50) return 'image/webp';
  if (u[4] === 0x66 && u[5] === 0x74 && u[6] === 0x79 && u[7] === 0x70) return 'image/avif';
  if (u[0] === 0x89 && u[1] === 0x50) return 'image/png';
  return 'application/octet-stream';
}

/* Décoder le base64 à la main coûte cher : `atob` rend une chaîne, et la
   recopier octet par octet dans un tableau fait quarante mille tours de boucle
   par image, sur le fil principal. En rafale — la fenêtre glissante en demande
   une vingtaine d'un coup — c'est ce qui faisait tomber le défilement à onze
   images par seconde sur téléphone.

   `fetch` sur une adresse `data:` fait le même travail dans le navigateur, en
   code natif et hors du fil principal. On garde l'ancienne voie en repli : une
   politique de sécurité stricte peut refuser `fetch` sur `data:`, et mieux vaut
   une page lente qu'une page vide. */
/* Les douze premiers octets suffisent à reconnaître un format : on ne décode
   pas les quarante mille autres pour ça. */
function entete(str){
  const b = atob(str.slice(0, 24));
  const u = new Uint8Array(12);
  for (let k = 0; k < 12 && k < b.length; k++) u[k] = b.charCodeAt(k);
  return u;
}

function depuisBase64(str){
  const b = atob(str), u = new Uint8Array(b.length);
  for (let k = 0; k < b.length; k++) u[k] = b.charCodeAt(k);
  return new Blob([u], { type: typeDe(u) });
}

let fetchData = true;
function source(i){
  if (SOURCES && SOURCES[NOM]) {
    const str = SOURCES[NOM][i];
    if (fetchData) {
      /* Le type se lit dans les octets, il ne se suppose pas : la
         construction peut produire du WebP comme de l'AVIF, et un navigateur
         strict rejette un lot mal étiqueté. */
      return fetch('data:' + typeDe(entete(str)) + ';base64,' + str)
        .then((r) => r.blob())
        .catch(() => { fetchData = false; return depuisBase64(str); });
    }
    return Promise.resolve(depuisBase64(str));
  }
  return fetch(`${SEQ.chemin}${String(i + 1).padStart(4, '0')}.jpg`)
    .then((r) => { if (!r.ok) throw new Error(r.status); return r.blob(); });
}

/* Repli pour les navigateurs sans createImageBitmap — Safari ne l'a qu'à partir
   de la version 15. Sans lui, TOUTES les images échouaient et la page se
   révélait sur une toile vide. Un <img> décode sur le fil principal et se voit
   au défilement, mais un site lent vaut mieux qu'un site noir. */
function decoder(blob){
  if (typeof createImageBitmap === 'function') return createImageBitmap(blob);
  return new Promise((ok, non) => {
    const im = new Image(), url = URL.createObjectURL(blob);
    im.onload = () => { URL.revokeObjectURL(url); ok(im); };
    im.onerror = () => { URL.revokeObjectURL(url); non(new Error('décodage')); };
    im.src = url;
  });
}

const cache = new Map();
const encours = new Set();
let dessinee = -1, echecs = 0;

/* Rend vrai si un décodage a réellement été lancé — c'est ce qui permet à la
   fenêtre de compter ce qu'elle dépense. */
function charger(i){
  if (i < 0 || i >= SEQ.images || cache.has(i) || encours.has(i)) return false;
  encours.add(i);
  lire(i);
  return true;
}

/* Ce que le réseau a réellement livré. `navigator.connection.downlink` est une
   indication lissée sur l'historique récent ; ces deux compteurs-là sont ce qui
   est arrivé sur CETTE page, à CE moment. */
let octetsRecus = 0, imagesRecues = 0;

async function lire(i){
  try {
    const blob = await source(i);
    octetsRecus += blob.size || 0; imagesRecues++;
    const im = await decoder(blob);
    /* La première image décodée révèle ce que coûte vraiment une image en
       mémoire — la construction peut servir n'importe quelle définition, la
       page n'a pas à la connaître d'avance. */
    if (!octetsImage) {
      octetsImage = im.width * im.height * 4;
      filmL = im.width; filmH = im.height;
      reglerFenetre();
      /* La toile a été taillée avant qu'on sache ce que mesure le film. On la
         retaille maintenant : c'est de là que vient le dessin au rapport 1:1. */
      redimensionner();
    }
    cache.set(i, im);
  }
  catch (e) { echecs++; }
  encours.delete(i);
}

/* La fenêtre glissante. On demande ce qui vient, on tolère un peu de ce qui
   précède — le défilement se remonte — et on libère le reste.

   LE CHARGEMENT NE DOIT PAS DÉPENDRE DU RYTHME D'AFFICHAGE. C'était le cas :
   deux décodages lancés par image RENDUE. Tant que la page tourne à soixante
   images par seconde, cela fait cent vingt lancements par seconde et personne
   ne le remarque. Mais dès que le rendu ralentit — une grande toile, une
   machine chargée, un téléphone — le chargement ralentit avec lui, donc les
   images manquent, donc le lecteur repose la voisine, et l'on croit que c'est
   le décodeur qui sature alors que c'est l'affichage qui l'affame. Une boucle
   qui s'auto-entretient, et qui punit exactement les machines déjà lentes.

   On plafonne donc le nombre de décodages EN VOL, pas le nombre de lancements
   par trame. Le chargeur reste saturé quel que soit le rythme d'affichage, et
   le fil principal reste protégé — c'était le but du plafond d'origine.

   VINGT-QUATRE ET NON HUIT, et le chiffre est mesuré. Le débit du chargeur
   vaut le nombre en vol divisé par la latence d'une image : à 300 ms l'image,
   huit en vol ne donnent que vingt-sept chargements par seconde. Or un
   défilement de mille pixels par seconde en consomme trente. Un déficit de dix
   pour cent seulement — mais il ne coûte pas dix pour cent d'absences, il en
   coûte quatre-vingt-quinze : le retard s'accumule sans jamais se résorber, et
   le chargeur finit par toujours réclamer l'image qu'on vient de dépasser. Il
   faut donc de la MARGE, pas l'équilibre. */
const EN_VOL = 24;

/* ----------------------------------------- la fenêtre se mesure en PIXELS

   Elle était écrite en NOMBRE D'IMAGES : vingt-quatre en avance, trente-huit
   gardées. Tant que la séquence comptait cinq cent quatre-vingts images
   c'était cohérent — vingt-quatre images valaient six cents pixels de course.
   En doublant la densité, les mêmes vingt-quatre images ne valent plus que
   trois cents pixels : la même page se serait retrouvée avec deux fois moins
   d'avance, et un défilement rapide l'aurait dépassée. Plus d'images aurait
   rendu la page MOINS sûre, ce qui est exactement l'inverse du but.

   On règle donc la fenêtre en distance de défilement, et le nombre d'images
   s'en déduit. La densité peut alors changer sans que rien d'autre bouge.

   Sept cents pixels d'avance : à trois mille pixels par seconde — un geste
   franc sur un pavé tactile — c'est près d'un quart de seconde de marge, et
   le fondu au plus proche couvre le reste. */
const AVANCE = 700, RECUL = 240, MEMOIRE = 1100;

/* Le plafond mémoire, lui, ne se compte pas en pixels de course mais en
   octets. Une image décodée n'est plus compressée : elle occupe largeur ×
   hauteur × 4 octets, soit neuf cents kilo-octets en 640×360 mais TROIS
   MÉGAOCTETS ET DEMI en 1280×720, et huit en 1920×1080. La purge se déclenche
   à deux fois `oubli`, donc c'est ce double qu'il faut borner.

   Quatre-vingt-seize mégaoctets partout était un réglage fait pour des images
   de neuf cents kilo-octets, et il est devenu absurde en montant en
   définition : il ne laissait plus tenir que treize images de part et d'autre.
   Un téléphone doit rester prudent — il ferme l'onglet sans prévenir — mais
   quatre-vingt-seize mégaoctets étaient trop stricts même pour lui : à 8 Mo
   l'image il n'en gardait que SIX, soit deux cents pixels d'avance. Cent
   quarante-quatre, avec une série servie à sa vraie taille, en gardent
   dix-neuf.

   SUR ORDINATEUR, LE BUDGET SUIT LA MACHINE. Une constante ne peut pas être
   juste à la fois pour un portable d'entrée de gamme et pour une tour : trop
   basse elle gâche la fluidité, trop haute elle fait tuer l'onglet. En 2560 px
   une image décodée pèse 14,1 Mo et il en faut une vingtaine d'avance, soit
   cinq cent soixante mégaoctets — ce qu'une machine de huit gigaoctets porte
   sans broncher, et qu'une machine de deux ne doit surtout pas tenter.
   `deviceMemory` rend la mémoire vive en gigaoctets, arrondie et plafonnée à
   huit par la norme ; on en prend soixante-dix mégaoctets par gigaoctet. Le
   navigateur qui ne connaît pas cette propriété — Safari, Firefox — est
   supposé être sur un ordinateur de bureau ordinaire, donc huit. */
/* CE QUE CE BUDGET COÛTE VRAIMENT, mesuré sur les pages en ligne : la toile
   garde entre 293 et 419 Mo d'images décodées selon la page et l'écran. C'est
   énorme, et ce n'est pas de la mémoire vive ordinaire — `createImageBitmap`
   rend des objets que le navigateur pose en MÉMOIRE GRAPHIQUE. Une carte
   intégrée, qui partage la mémoire du système et dispose d'un budget de
   textures bien plus étroit, doit alors en éjecter et les recharger à chaque
   trame. C'est un mode de panne qui ressemble exactement à « ça rame », et
   qu'AUCUNE mesure faite sur la machine de développement ne pouvait montrer :
   sans carte graphique, tout tient en mémoire vive sans pression.

   `?memoire=N` permet donc de le vérifier là où ça compte — sur la machine du
   visiteur. Le plancher de 48 Mo garde de quoi tenir la fenêtre glissante. */
const _memArg = parseInt(REGLAGES.get('memoire'), 10);
const MEMOIRE_MAX = (Number.isFinite(_memArg) && _memArg > 0
  ? borne(_memArg, 48, 1024)
  : (innerWidth < 820 ? 144
     : min(560, round((navigator.deviceMemory || 8) * 70)))) * 1048576;
let octetsImage = 0;

function reglerFenetre(){
  const parImage = course / max(SEQ.images - 1, 1);
  SEQ.arriere = borne(round(RECUL   / parImage),  2,  40);
  let oubli   = borne(round(MEMOIRE / parImage), 10, 200);
  if (octetsImage) oubli = min(oubli, max(round(MEMOIRE_MAX / octetsImage / 2), 8));
  SEQ.oubli = oubli;
  /* PRÉCHARGER PLUS LOIN QUE CE QU'ON GARDE N'A AUCUN SENS, et c'était le cas :
     à 1280 px, `avant` valait 66 images quand `oubli` en gardait 13. Le lecteur
     décodait cinquante images par-dessus la limite de purge, qui les jetait
     aussitôt — il travaillait à plein régime pour la poubelle, et l'image
     demandée manquait quand même neuf fois sur dix. Le plafond mémoire commande
     donc les deux : on ne demande jamais au-delà de ce qui survivra. */
  SEQ.avant = min(borne(round(AVANCE / parImage), 6, 120), oubli);
}

function fenetre(centre){
  for (let d = 0; d <= SEQ.avant && encours.size < EN_VOL; d++) {
    charger(centre + d);
    if (d <= SEQ.arriere && encours.size < EN_VOL) charger(centre - d);
  }
  if (cache.size > SEQ.oubli * 2) {
    for (const i of cache.keys())
      if (abs(i - centre) > SEQ.oubli) { cache.get(i).close?.(); cache.delete(i); }
  }
}

/* Dessin en « couvrir » : l'image remplit la toile sans se déformer, quitte à
   déborder. Recalculé à chaque dessin, la fenêtre pouvant changer. */
/* Deux cadrages, choisis par la page avec `data-cadrage` sur la toile.

   « couvrir » (par défaut) remplit l'écran et rogne ce qui dépasse. C'est le
   réflexe, et il coûte deux choses : entre 10 et 20 % de l'image selon
   l'appareil — mesuré 82 % montrés sur iPhone, 80 % sur un Android haut — et
   ces pixels-là sont TÉLÉCHARGÉS avant d'être jetés.

   « contenir » montre l'image entière. La place qui reste n'est pas une barre
   noire subie : l'image est calée en HAUT, et la bande du bas devient la zone
   de texte. Sur un téléphone 393 x 852 elle fait 153 px, ce qui est exactement
   ce qu'il faut pour un titre et une ligne.

   Et c'est moins cher, ce qui est contre-intuitif : on dessine moins de pixels.
   Mesuré sur la toile d'un téléphone, moyenne sur 24 images :

       contenir                              5,78 ms
       couvrir (l'ancien)                    7,46 ms
       contenir + fond flouté par ctx.filter 49,77 ms   <- le réflexe à éviter

   Le fond flouté façon lecteur vidéo coûte donc près de sept fois le dessin.
   Si on en voulait un, il faudrait passer par une petite toile agrandie
   (11,7 ms), jamais par le filtre du contexte. */
function poser(im){
  const cw = canvas.width, ch = canvas.height;
  if (canvas.dataset.cadrage === 'contenir') {
    const k = min(cw / im.width, ch / im.height);
    const l = im.width * k, h = im.height * k;
    const x = (cw - l) / 2;
    ctx.fillStyle = canvas.dataset.fond || '#07090B';
    ctx.fillRect(0, 0, cw, ch);
    /* La bande du bas est le PROLONGEMENT de l'image, pas une barre noire : on
       y étire la dernière ligne de pixels. La jonction disparaît, la couleur
       suit le film — un ciel bleu donne une bande bleue, un quai sombre une
       bande sombre — et ça ne coûte qu'un tracé d'une ligne de haut. Sans ça,
       le raccord se voyait comme une marche derrière le texte. */
    if (h < ch) ctx.drawImage(im, 0, im.height - 1, im.width, 1, x, h - 1, l, ch - h + 1);
    if (l < cw) {
      ctx.drawImage(im, 0, 0, 1, im.height, 0, 0, x + 1, h);
      ctx.drawImage(im, im.width - 1, 0, 1, im.height, x + l - 1, 0, cw - x - l + 1, h);
    }
    ctx.drawImage(im, x, 0, l, h);
    window.__IMAGE = im;
    return;
  }
  const k = max(cw / im.width, ch / im.height);
  ctx.drawImage(im, (cw - im.width * k) / 2, (ch - im.height * k) / 2,
                im.width * k, im.height * k);
  /* L'image posée est publiée : une mise en page peut vouloir y puiser sa
     couleur. Échantillonner huit pixels sur huit coûte 0,021 ms — c'est
     mesuré, et c'est trois centièmes du budget d'une trame. */
  window.__IMAGE = im;
}

function dessiner(i){
  const im = cache.get(i);
  if (!im) return false;
  poser(im);
  dessinee = i;
  return true;
}

/* Le fondu entre deux images voisines.

   C'est ce qui change tout sur téléphone. La série étroite compte moins
   d'images que la large — elle s'ajoute au poids de l'autre — et à une
   soixantaine d'images pour quatre écrans de défilement, chaque image tient
   une trentaine de pixels. Arrondir à l'image la plus proche fait donc voir
   les marches.

   On dessine plutôt les DEUX images qui encadrent la position courante, la
   seconde par-dessus la première avec l'opacité de la fraction. Le défilement
   devient continu au lieu d'être quantifié, et ça ne coûte qu'un second tracé
   — pas un octet de plus au chargement.

   `dessinee` passe à -1 : la position varie en continu, on ne peut plus se
   contenter de comparer un numéro d'image pour savoir s'il faut redessiner. */
/* À défaut de l'image demandée, la plus proche déjà décodée.

   Sans ce repli, une image pas encore prête ne dessinait rien : la toile
   gardait l'image précédente, et le défilement semblait se bloquer alors qu'il
   avançait. On préfère montrer une voisine — décalée d'une ou deux images,
   invisible en mouvement — que de figer l'écran. C'est ce que fait
   velaarmon.com, et c'est ce qui fait qu'on ne les voit jamais buter. */
function auPlusProche(i){
  const im = cache.get(i);
  if (im) return im;
  for (let d = 1; d < SEQ.images; d++) {
    const a = cache.get(i - d); if (a) return a;
    const b = cache.get(i + d); if (b) return b;
  }
  return null;
}

let posee = -1;
/* ------------------------------------------------ SE POSER SUR UNE IMAGE

   Le fondu enchaîné existe pour masquer le pas entre deux images pendant le
   mouvement. À L'ARRÊT il devient un défaut : la page tient un mélange à
   parts égales de deux vues distantes de trente-trois pixels de travelling,
   et le résultat est un DÉDOUBLEMENT — un bord de lettre en devient deux.
   Vérifié sur le logo d'un client : le « D » sort franc sur une image seule
   et fantomatique sur le mélange.

   On mesure donc la vitesse, en images par trame, et l'on ramène la position
   affichée vers l'image entière la plus proche à mesure qu'elle tombe. Au
   repos l'accroche vaut un : une seule image est posée, sans aucun mélange.
   Au-delà du seuil elle vaut zéro et le fondu reprend tous ses droits.

   Le seuil est en images par trame et non en pixels par seconde, pour rester
   juste quelle que soit la densité de la séquence : un quart d'image par
   trame, soit une quinzaine d'images par seconde, ce qui correspond à un
   défilement lent et délibéré. Au-dessus, l'oeil ne distingue plus le
   dédoublement de toute façon.

   L'accroche est lissée dans le temps, sinon elle vacillerait entre deux
   trames et l'image tressauterait au lieu de se poser. */
const SEUIL_ACCROCHE = 0.25;
let posPrec = -1, accroche = 0;

function fondu(brut){
  if (posPrec >= 0) {
    const vitesse = abs(brut - posPrec);
    const vise = vitesse >= SEUIL_ACCROCHE ? 0 : 1 - vitesse / SEUIL_ACCROCHE;
    accroche += (vise - accroche) * 0.25;
  }
  posPrec = brut;
  const pos = brut + (Math.round(brut) - brut) * accroche;
  const bas = borne(Math.floor(pos), 0, SEQ.images - 1);
  const haut = borne(bas + 1, 0, SEQ.images - 1);
  const t = pos - bas;
  const a = auPlusProche(bas);
  if (!a) return;
  ctx.globalAlpha = 1;
  poser(a);
  const b = cache.get(haut);
  if (b && cache.has(bas) && t > 0.01) { ctx.globalAlpha = t; poser(b); ctx.globalAlpha = 1; }
  posee = pos;
  window.__ACCROCHE = accroche;
  dessinee = -1;
  /* Point d'observation. `posee` vit dans cette fermeture, donc de l'extérieur
     rien ne permet de savoir si l'image affichée AVANCE réellement pendant un
     défilement — or c'est toute la question : `auPlusProche` ne bloque jamais,
     il repose la voisine disponible, et un décodage trop lent se traduit non
     par une erreur mais par une image qui se répète. Sans ce témoin, la
     fluidité est invisible à la mesure et ne peut donc pas être défendue.
     Deux propriétés au lieu d'une : ce qu'on VOULAIT afficher et ce qu'on a
     vraiment posé — leur écart est exactement le retard du décodeur. */
  window.__VOULUE = pos;
  window.__POSEE = cache.has(bas) ? bas : -1;
}

/* Ce que mesure une image du film, connu dès le premier décodage, et le
   facteur de réduction que la mesure de fluidité fera varier. */
let filmL = 0, filmH = 0, echelle = 1;

function redimensionner(){
  /* Sur un écran étroit on plafonne à 1,5 au lieu de 2. Une toile de 390 px
     rendue en 2 fait 780 x 1688 pixels à remplir ; en 1,5 elle en fait 585 x
     1266, soit 44 % de moins à chaque image. À la densité d'un téléphone, la
     différence ne se voit pas — la charge, elle, se sent. */
  /* LE LECTEUR NE POSSÈDE PLUS L'ÉCRAN, IL OBÉIT À LA MISE EN PAGE.

     Il lisait `innerWidth` et réécrivait `canvas.style.width` : la toile était
     donc forcée au plein écran, quoi qu'en dise la feuille de style. Tant que
     le film occupait tout, personne ne le voyait — mais cela interdisait toute
     mise en page où le film est ENCADRÉ, à côté du texte plutôt que dessous.
     Or c'est exactement ce qu'exige une direction artistique sur fond clair.

     On mesure donc la boîte que le CSS a réellement donnée à la toile. Le
     plein écran devient un cas particulier — celui où la règle dit inset:0 —
     au lieu d'être la seule possibilité. Mesuré : encadrer ne coûte rien
     (60 i/s dans les deux cas), là où un masque dégradé coûte 40 %. */
  const boite = canvas.getBoundingClientRect();
  const larg = boite.width  || innerWidth;
  const haut = boite.height || innerHeight;
  const plafond = larg < 820 ? 1.5 : 2;

  /* ON NE FABRIQUE JAMAIS UNE TOILE PLUS FINE QUE LE FILM.

     C'était le défaut le plus coûteux de tout le lecteur, et il ne se voyait
     nulle part. Un écran de bureau à densité 2 donnait une toile de 3200 x
     1800 ; le film mesure 1920 x 1080. On agrandissait donc chaque image de
     67 %, à chaque trame, pour n'ajouter AUCUNE information : les pixels
     supplémentaires sont inventés par l'interpolateur, pas lus dans le
     fichier. Mesuré ici, sur ce conteneur sans carte graphique, pour une
     image 1920 x 1080 :

         dessin vers 1920 x 1080 (rapport 1:1)   1,3 ms
         dessin vers 1600 x  900 (réduction)     5,7 ms  ·  27,5 ms en « high »
         dessin vers 3200 x 1800 (agrandissement) 22 ms  ·  184 ms en « high »

     Cent quatre-vingt-quatre millisecondes : cinq images par seconde. C'est
     exactement le « pas fluide du tout sur PC » qu'on n'arrivait pas à
     expliquer. Le décodeur n'y était pour rien.

     La règle est donc simple : la densité retenue est la plus grande qui
     laisse encore l'image COUVRIR la toile sans être agrandie. Le facteur de
     couverture vaut alors exactement 1, et `drawImage` recopie au lieu de
     rééchantillonner.

     ET ON NE POSE AUCUN PLANCHER À 1. C'était le reste du défaut, et il
     touchait précisément les écrans de bureau. Une fenêtre de 2560 px de large
     donne un rapport juste de 0,75 ; un plancher à 1 le remontait à 1, donc une
     toile de 2560 x 1440, donc un agrandissement, donc les 184 ms. Mesuré :
     6 images par seconde sur un écran 1440p, 10 sur un 1440p à 125 %. Tout
     écran plus large que le film retombait dans le trou qu'on croyait bouché.

     Une toile plus petite que la fenêtre n'est pas un défaut : l'élément est
     étiré par la FEUILLE DE STYLE, donc l'agrandissement est fait par le
     compositeur du navigateur — sur la carte graphique, et une seule fois par
     trame au lieu d'une fois par image dessinée. On ne perd rien : les pixels
     en trop étaient inventés de toute façon, l'information s'arrête à 1920.
     Le plancher réel est intrinsèque — la toile ne descend jamais sous la
     définition du film. */
  const juste = (filmL && filmH)
    ? min(filmL / larg, filmH / haut)
    : plafond;
  const dpr = min(devicePixelRatio || 1, plafond, juste) * echelle;

  canvas.width = round(larg * dpr);
  canvas.height = round(haut * dpr);

  /* La toile perd tous ses réglages quand on change sa taille : à replacer
     ici, jamais une seule fois au démarrage.

     « high » emploie un filtre à plusieurs passes, et il ne se justifierait
     qu'en agrandissant. Or la toile ne dépasse plus jamais la définition du
     film : il n'y a plus d'agrandissement à filtrer ici, seulement une copie
     ou une légère réduction. « high » ne coûterait donc que du temps — et
     c'est lui qui faisait tomber les écrans larges à six images par seconde. */
  ctx.imageSmoothingEnabled = true;
  ctx.imageSmoothingQuality = 'low';

  if (posee >= 0) fondu(posee); else if (dessinee >= 0) dessiner(dessinee);
}
addEventListener('resize', () => { redimensionner(); mesurer(); }, { passive: true });
/* Une requête de média peut changer la boîte de la toile sans que la fenêtre
   bouge — le film passe de la moitié droite à toute la largeur, par exemple.
   `resize` ne le verrait pas. */
if (typeof ResizeObserver === 'function') {
  let dernL = 0, dernH = 0;
  new ResizeObserver(() => {
    const b = canvas.getBoundingClientRect();
    if (round(b.width) === dernL && round(b.height) === dernH) return;
    dernL = round(b.width); dernH = round(b.height);
    redimensionner();
  }).observe(canvas);
}

/* Le film ne couvre que le prologue : au-delà, la suite du site est opaque et
   recouvre la toile. On mesure donc la progression sur le prologue seul, pas
   sur toute la page — sinon le film se terminerait bien après avoir disparu. */
const prologue = document.getElementById('prologue');
const actes = [...document.querySelectorAll('#prologue section')];

/* Les mesures de mise en page se prennent UNE fois, pas soixante fois par
   seconde.

   La boucle lisait `offsetHeight` du prologue et le rectangle de chacun des
   quatre actes à chaque image — cinq lectures qui forcent le navigateur à
   recalculer la mise en page avant de répondre. Sur un ordinateur ça passe
   inaperçu ; sur un téléphone c'est la première cause de saccade, parce que ce
   recalcul tombe pile dans le temps imparti à l'image. On mesure donc au
   chargement et au redimensionnement, et la boucle ne fait plus que de
   l'arithmétique. */
let course = 1, centres = [];
function mesurer(){
  course = max(prologue.offsetHeight - innerHeight, 1);
  const haut = prologue.offsetTop;
  centres = actes.map((a) => haut + a.offsetTop + a.offsetHeight / 2);
  /* La fenêtre du chargeur dépend de la course : elle se relit ici, et pas
     ailleurs, pour qu'un changement d'orientation la remette d'aplomb. */
  reglerFenetre();
}

function progression(){
  return borne(scrollY / course, 0, 1);
}

const lent = matchMedia('(prefers-reduced-motion: reduce)').matches;
let vise = 0, courant = 0, visePrec = 0, dernier = performance.now();

/* ------------------------------------------------- le défilement lissé
   La différence la plus visible avec les sites qu'on prend pour référence, et
   ce n'est pas leur séquence d'images : c'est qu'ils lissent LA POSITION DE
   DÉFILEMENT elle-même.

   Un cran de molette déplace la page d'une centaine de pixels d'un coup. Si
   l'on ne rattrape que le numéro d'image, la toile glisse doucement pendant
   que le TEXTE, lui, saute — et c'est ce décalage qu'on lit comme « moins
   fluide ». On déplace donc une cible, et la position réelle la rejoint à taux
   constant : tout bouge ensemble.

   Uniquement à la molette. Le tactile garde le défilement natif, avec son
   inertie propre que le système gère mieux que nous — c'est aussi le réglage
   par défaut de Lenis, la bibliothèque qu'ils emploient. Et rien du tout si le
   visiteur a demandé moins de mouvement : on ne s'interpose pas dans le
   défilement de quelqu'un qui a explicitement dit non.

   `?molette=0` dans l'adresse coupe le lissage et rend la molette au
   navigateur. C'est le seul moyen de trancher une question de RESSENTI sans
   être devant la machine : les deux versions se comparent en rechargeant. */
const _arg = new URLSearchParams(location.search).get('molette');
const molette = _arg !== '0' && !lent
  && matchMedia('(hover: hover) and (pointer: fine)').matches;
/* LE TEMPS DE RÉPONSE DU LISSEUR, en secondes. Ce n'est plus un taux de
   rattrapage : c'est la durée que met la page à rejoindre sa cible. */
const REPONSE = 0.14;
let cibleY = scrollY, lisseY = scrollY, vitesseY = 0;

/* La hauteur de la page, mesurée UNE fois.

   Elle était lue dans le gestionnaire de molette. `scrollHeight` force le
   navigateur à recalculer la mise en page de toute la page — trente écrans,
   des dizaines de sections — et cela à CHAQUE cran de molette, c'est-à-dire
   plusieurs fois par seconde pendant qu'on défile, sur le fil principal, juste
   à côté du dessin du film. C'est la seule dépense de tout le lecteur qui ne
   touchait que le PC : le tactile ne passe jamais par là. */
let basDePage = 0;
const mesurerHauteur = () => { basDePage = max(document.body.scrollHeight - innerHeight, 0); };
mesurerHauteur();
addEventListener('resize', mesurerHauteur, { passive: true });
addEventListener('load', mesurerHauteur);

if (molette) {
  addEventListener('wheel', (e) => {
    if (e.ctrlKey) return;                    // le zoom du navigateur reste au navigateur
    e.preventDefault();
    cibleY = borne(cibleY + e.deltaY * (e.deltaMode === 1 ? 18 : 1), 0, basDePage);
  }, { passive: false });
  /* Clavier, barre de défilement, ancres : tout ce qui déplace la page sans
     passer par la molette doit ramener la cible, sinon elle tirerait la page
     en arrière à la molette suivante. */
  addEventListener('scroll', () => {
    /* La vitesse se remet à zéro avec la position : sans ça, un saut d'ancre
       repart avec l'élan du geste précédent, et la page dépasse sa cible. */
    if (abs(scrollY - lisseY) > 2) { cibleY = scrollY; lisseY = scrollY; vitesseY = 0; }
  }, { passive: true });
}

function boucle(now){
  const dt = min((now - dernier) / 1000, 0.05); dernier = now;

  /* ------------------------------------- POURQUOI UN RESSORT ET NON UN TAUX

     Ce lisseur était un rattrapage du premier ordre :

         lisseY += (cibleY - lisseY) * (1 - exp(-14 * dt))

     et c'était LUI le « pas fluide sur PC ». Pas le décodeur, pas la taille de
     la toile, pas la carte graphique : mesuré à soixante images par seconde
     pleines, sur une molette parfaitement régulière et des trames régulières à
     16,7 ms, l'avance réelle de la page par trame donnait

         30, 24, 19, 15, 12,  30, 24, 19, 15, 12,  30, 24, 19, 15, 12 …

     Un cycle exact, d'amplitude 2,5 pour 1. Les rapports entre trames — 0,800
     0,792 0,789 0,800 — sont exp(-14 x dt) = 0,792 à trois décimales : c'est
     la réponse analytique du rattrapage, pas un aléa de machine.

     LA CAUSE EST DE FORME, PAS DE RÉGLAGE. Un rattrapage à taux fixe donne une
     vitesse PROPORTIONNELLE À L'ÉCART RESTANT. Une molette crantée n'envoie pas
     un flot continu : elle envoie des impulsions. Chaque cran creuse l'écart
     d'un coup — donc la vitesse saute — puis l'écart se referme
     géométriquement — donc la vitesse retombe. Le film accélère et ralentit à
     la cadence des crans, une douzaine de fois par seconde, ce qui est
     exactement la bande où l'oeil lit une irrégularité.

     ET DURCIR LA CONSTANTE AGGRAVE. C'est le contrôle qui interdit de croire à
     un simple réglage — trois variantes de la même page construite, mesurées :

         actuel (taux 14)          irrégularité 33 %   cycle  2,58 : 1
         taux durci à 40           irrégularité 80 %   cycle 17,00 : 1
         ressort amorti            irrégularité 11 %   cycle  1,28 : 1

     Le taux durci suit les impulsions plus fidèlement, donc il les restitue au
     lieu de les absorber : sept fois pire. La vitesse moyenne, elle, est la
     même dans les trois cas — on ne troque donc rien contre rien.

     LE RESSORT CRITIQUEMENT AMORTI règle ça par construction : la vitesse y
     est un ÉTAT, pas une conséquence de l'écart. Une impulsion sur la cible la
     COURBE au lieu de la créneler, et elle ne peut pas sauter. Même temps de
     réponse ressenti, cycle ramené à 1,28 pour 1.

     La forme employée est l'intégration semi-implicite habituelle : stable
     quel que soit `dt`, ce qui compte ici puisque `dt` varie d'une trame à
     l'autre dès que la machine peine. */
  if (molette && (abs(cibleY - lisseY) > 0.4 || abs(vitesseY) > 1)) {
    const om = 2 / REPONSE, x = om * dt;
    const e = 1 / (1 + x + 0.48 * x * x + 0.235 * x * x * x);
    const ecart = lisseY - cibleY;
    const tmp = (vitesseY + om * ecart) * dt;
    vitesseY = (vitesseY - om * tmp) * e;
    lisseY = cibleY + (ecart + tmp) * e;
    scrollTo(0, lisseY);
  }

  vise = progression() * (SEQ.images - 1);
  /* Le rattrapage. Sauter à l'image visée donne un défilement nerveux ; la
     rattraper à taux constant donne l'inertie d'une caméra.

     MAIS PAS DEUX FOIS. C'était la faute, et elle ne touchait que le PC.
     Quand le lissage de molette est actif, la position de défilement est DÉJÀ
     rattrapée à taux constant ; lui appliquer un second rattrapage empile deux
     retards du premier ordre. Mesuré sur la fenêtre du rapport, pour un cran
     de molette de 300 px :

         la page arrive à 90 % de sa cible    263 ms
         l'image arrive à 90 % de la sienne   444 ms

     Presque une demi-seconde entre le geste et l'image. Ce n'est pas un
     manque de fluidité — la page tourne à soixante images par seconde — c'est
     du RETARD, et aucun compteur d'images ne le dénonce. Sur téléphone il n'y
     a qu'un seul lissage, le tactile gardant son défilement natif : d'où
     « excellent sur téléphone, pâteux sur PC ».

     Quand la position est déjà lissée, l'image la suit donc EXACTEMENT. */
  courant = (lent || molette) ? vise
          : courant + (vise - courant) * (1 - exp(-9 * dt));
  const i = borne(round(courant), 0, SEQ.images - 1);
  fenetre(i);
  /* Un vingtième d'image : en deçà, le fondu ne se verrait pas et on
     économise deux tracés. */
  if (abs(courant - posee) > 0.05) fondu(courant);
  acteCourant();
  /* « EN MOUVEMENT » SE LIT SUR LE FILM, PAS SUR L'ÉCART AU RATTRAPAGE.
     Le témoin était `abs(vise - courant) > 0,05`. Or la ligne du dessus pose
     `courant = vise` dès que la molette est lissée — donc sur TOUT ordinateur.
     L'écart y valait zéro par construction, `jauger` recevait toujours faux, et
     la toile qui s'auto-règle n'a jamais mesuré une seule trame là où elle
     était censée servir. Elle ne tournait que sur téléphone, où le tactile
     laisse `courant` retarder sur `vise` — soit exactement l'inverse du but.
     On regarde donc si le film AVANCE, ce qui est vrai dans les deux modes. */
  const bouge = abs(vise - visePrec) > 0.01; visePrec = vise;
  jauger(now, bouge);
  regularite(scrollY, now);
  requestAnimationFrame(boucle);
}

/* ------------------------------------------------- la toile qui s'auto-règle

   Tout ce qui précède suppose qu'on sait ce que coûte un dessin sur la machine
   du visiteur. On ne le sait pas. Un écran 1440p ou 4K oblige forcément à
   agrandir la dernière étape — le film s'arrête à 1920 — et selon que cet
   agrandissement tombe sur une carte graphique ou sur le processeur, il est
   gratuit ou il coûte tout. Mesuré ici, sans carte graphique, sur une fenêtre
   de 2560 px : 60 images par seconde sans agrandissement, 21 avec.

   Plutôt que de deviner le matériel, on MESURE le résultat. Si le rendu tient
   moins de quarante-cinq images par seconde pendant que ça défile, on réduit
   la toile d'un cran ; si la marge revient, on la rend. Le visiteur d'une
   machine rapide garde la pleine définition, celui d'une machine lente garde
   la fluidité — et personne n'a à choisir à sa place.

   On ne juge QUE pendant le mouvement : à l'arrêt le navigateur ralentit de
   lui-même, et prendre ça pour de la lenteur ferait rétrécir la toile sans
   raison. */
let tPrec = 0, durees = [], tDernierReglage = 0, essai = null, rendu = '', dernierMedian = 0;

function jauger(now, enMouvement){
  if (!enMouvement) { tPrec = 0; durees.length = 0; return; }
  if (tPrec) durees.push(now - tPrec);
  tPrec = now;
  if (durees.length < 40) return;

  durees.sort((a, b) => a - b);
  const median = dernierMedian = durees[durees.length >> 1];
  durees.length = 0;

  /* 1,5 s entre deux décisions : retailler la toile efface son contenu et se
     voit. Mieux vaut un réglage sûr que trois hésitations. */
  if (now - tDernierReglage < 1500) return;

  /* ON VÉRIFIE QUE RÉDUIRE SERT À QUELQUE CHOSE.

     Première version : dès que ça ramait, on rétrécissait. Mesuré sur une
     fenêtre de 2560 px, la toile est tombée de 1920 x 1080 à 1002 x 564 — donc
     nettement plus floue — et la cadence n'a pas bougé d'une image : 21 par
     seconde avant, 21 après. Le coût n'était pas le dessin, c'était le
     compositeur qui repeint la fenêtre entière, et celui-là ne dépend pas de
     la taille de la toile.

     Une dégradation qui ne rapporte rien est une dégradation pure. On garde
     donc la mesure d'avant, et si le cran suivant n'améliore pas d'au moins
     un dixième, on revient en arrière et on cesse d'essayer. Mieux vaut une
     image nette à vingt images par seconde qu'une image floue à vingt. */
  if (essai) {
    const gagne = median < essai.avant * 0.9;
    if (!gagne) { echelle = essai.echelle; redimensionner(); rendu = 'stable'; }
    essai = null;
    tDernierReglage = now;
    return;
  }
  if (rendu === 'stable') return;

  if (median > 22 && echelle > 0.5) {                                      // < 45 i/s
    essai = { echelle, avant: median };
    echelle = max(0.5, echelle * 0.85);
  } else if (median < 13 && echelle < 1) {                                 // de la marge
    echelle = min(1, echelle * 1.12);
  } else return;

  tDernierReglage = now;
  redimensionner();
}

/* ------------------------------------------------------------- le témoin

   `?diag=1` affiche ce que la page mesure d'elle-même, sur la machine du
   visiteur. Rien de tout cela n'est devinable à distance : le conteneur qui a
   servi à régler ce lecteur n'a pas de carte graphique, et il plafonne donc à
   vingt images par seconde sur toute fenêtre plus large que le film, quelle
   que soit la taille de la toile. Impossible de savoir depuis ici si un PC
   donné souffre du dessin, du compositeur, du décodeur ou du lissage.

   Le témoin répond à la place : il donne la fenêtre, la toile, la densité, le
   temps médian d'une trame pendant le défilement, et le retard du décodeur.
   Ces cinq nombres suffisent à désigner le coupable.

   ET SURTOUT LA RÉGULARITÉ, qui est le seul chiffre à dire « pas fluide »
   quand la cadence, elle, est pleine. Une page peut tenir soixante images par
   seconde et sautiller quand même, si l'avance du film varie d'une trame à
   l'autre — c'était précisément le défaut du lisseur de molette, invisible à
   tout compteur d'images. On mesure donc l'écart-type de l'avance rapporté à
   sa moyenne, sur les trames où ça défile :

       moins de 10 %   fluide
       10 à 25 %       perceptible sur un mouvement lent
       plus de 25 %    c'est ce qu'on voit et qu'on appelle « pâteux » */
let avPrec = -1, tReg = 0, avances = [], derniereRegularite = 0;
function regularite(y, now){
  const d = y - avPrec, dt = now - tReg;
  const bouge = avPrec >= 0 && dt > 0 && d > 0.01;
  avPrec = y; tReg = now;
  /* UN ARRÊT VIDE L'ACCUMULATION. Sans ça, une série de mesures enjambe la
     pause entre deux gestes : elle compare la fin d'un ralentissement au début
     du suivant, et annonce un sautillement que personne ne voit. Mesuré : 39 %
     affichés là où le défilement continu en valait 10.

     Et l'on compte une VITESSE, pas une avance : les trames ne durent pas
     toutes pareil, et diviser par leur durée évite d'accuser le lecteur d'une
     irrégularité qui n'est que celle de l'horloge d'affichage. */
  if (!bouge) { avances.length = 0; return; }
  avances.push(d / dt);
  if (avances.length < 45) return;
  const moy = avances.reduce((a, b) => a + b, 0) / avances.length;
  const ec = Math.sqrt(avances.reduce((a, b) => a + (b - moy) ** 2, 0) / avances.length);
  derniereRegularite = moy > 0.0001 ? ec / moy : 0;
  avances.length = 0;
}

if (new URLSearchParams(location.search).get('diag') === '1') {
  const t = document.createElement('pre');
  t.style.cssText = 'position:fixed;left:8px;bottom:8px;z-index:99;margin:0;'
    + 'padding:9px 12px;background:rgba(0,0,0,.82);color:#7fe;font:11px/1.6 ui-monospace,monospace;'
    + 'border:1px solid #7fe4;border-radius:3px;pointer-events:none;white-space:pre';
  document.body.appendChild(t);
  setInterval(() => {
    const m = dernierMedian;
    t.textContent =
      `fenêtre    ${innerWidth} x ${innerHeight}   densité ${(devicePixelRatio||1).toFixed(2)}\n` +
      `toile      ${canvas.width} x ${canvas.height}   échelle ${echelle.toFixed(2)}\n` +
      `film       ${filmL} x ${filmH}   lissage ${ctx.imageSmoothingQuality}\n` +
      `trame      ${m ? m.toFixed(1) + ' ms  (' + Math.round(1000/m) + ' i/s)' : '—'}\n` +
      `régularité ${derniereRegularite ? (derniereRegularite * 100).toFixed(0) + ' %  ' +
         (derniereRegularite < 0.10 ? 'fluide'
          : derniereRegularite < 0.25 ? 'perceptible' : 'SAUTILLE') : '—'}\n` +
      /* On compare l'image POSÉE à l'image DEMANDÉE, toutes deux entières.
         La version précédente comparait un entier à la position fractionnaire :
         à l'arrêt sur l'image 296 la position vaut 296,99, et l'écart affichait
         « 1 image de retard » alors que l'image montrée était la bonne. Un
         témoin qui accuse à tort est pire que pas de témoin. */
      `décodeur   ${window.__POSEE < 0 ? 'IMAGE ABSENTE'
         : 'retard ' + abs(window.__POSEE - round(window.__VOULUE)) + ' image'}` +
      `   ${cache.size} en cache\n` +
      /* Ce que les images décodées occupent VRAIMENT. C'est le chiffre qui
         manquait : une image n'est plus compressée une fois décodée, et le
         navigateur la range en mémoire graphique. Sans ce relevé, on regarde
         une cadence sans savoir ce qui l'étouffe. */
      /* Le plafond affiché est le plafond EFFECTIF, pas celui demandé. La
         fenêtre glissante garde un plancher de huit images de part et d'autre
         — sans quoi le film sauterait — et ce plancher peut dépasser un budget
         très bas. Afficher le budget demandé donnait « 119 Mo de 96 Mo », un
         témoin qui se contredit et qu'on cesse aussitôt de croire. */
      `mémoire    ${octetsImage
         ? (cache.size * octetsImage / 1048576).toFixed(0) + ' Mo sur ' +
           (SEQ.oubli * 2 * octetsImage / 1048576).toFixed(0) + ' Mo max' : '—'}\n` +
      `molette    ${molette ? 'lissée' : 'native'}` +
      `   toile ${ctx.getContextAttributes?.().alpha ? 'transparente' : 'opaque'}`;
  }, 250);
}

/* ============================================================================
   `?test=1` — LE DIAGNOSTIC QUI SE LIT TOUT SEUL

   Le témoin `?diag=1` suppose qu'on sache lire sept lignes de chiffres pendant
   qu'on fait défiler d'une main. Éprouvé sur un vrai utilisateur : ça ne marche
   pas, et la question qui revient est « je regarde où ». Un instrument que
   personne ne sait lire ne mesure rien.

   Celui-ci fait le geste À LA PLACE du visiteur — il défile lui-même, à vitesse
   connue — puis rend UNE phrase qui nomme la cause, et un bouton qui copie le
   relevé. Rien à lire pendant qu'on scrolle, rien à photographier.

   IL EXISTE PARCE QUE LE DÉFAUT NE SE REPRODUIT PAS ICI. La machine qui a servi
   à écrire ce lecteur n'a pas de carte graphique et sert les images depuis le
   disque : ni le coût d'une texture, ni la latence d'un réseau n'y existent.
   Les quatre causes possibles se distinguent pourtant par des chiffres
   différents, et ces chiffres-là, seule la machine du visiteur les a.
   ============================================================================ */
if (REGLAGES.get('test') === '1') {
  const CIBLE = 1000;          // px par seconde : un défilement franc mais tenu
  const DUREE = 6000;          // ms de mesure, après amorçage

  const ecran = document.createElement('div');
  ecran.style.cssText =
    'position:fixed;inset:0;z-index:2147483647;background:rgba(6,9,13,.94);' +
    'display:flex;align-items:center;justify-content:center;padding:22px;' +
    'font:15px/1.6 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;color:#EAEFF5';
  ecran.innerHTML =
    '<div style="max-width:560px;width:100%">' +
    '<div id="t-etat" style="font-size:19px;font-weight:600;margin-bottom:14px">' +
    'Diagnostic en cours…</div>' +
    '<div style="height:6px;background:#20262F;border-radius:6px;overflow:hidden">' +
    '<div id="t-barre" style="height:100%;width:0;background:#E8A94A;transition:width .2s"></div>' +
    '</div>' +
    '<div id="t-sous" style="margin-top:11px;color:#93A0AE;font-size:13.5px">' +
    'Ne touche à rien, la page défile toute seule.</div></div>';
  document.body.appendChild(ecran);
  const etat = ecran.querySelector('#t-etat');
  const barre = ecran.querySelector('#t-barre');
  const sous = ecran.querySelector('#t-sous');

  const octetsFilm = () => performance.getEntriesByType('resource')
    .filter((r) => r.name.indexOf('/assets/film/') >= 0)
    .reduce((s, r) => s + (r.transferSize || r.encodedBodySize || 0), 0);

  (async function passer(){
    /* ON ATTEND QUE LE FILM SOIT LÀ. Mesurer pendant l'écran d'attente
       compterait le chargement initial comme un défaut de la machine, et
       accuserait toutes les connexions du monde. */
    const depart = performance.now();
    while (!voile.classList.contains('parti') && performance.now() - depart < 120000) {
      sous.textContent = 'Chargement du film…';
      await new Promise((r) => setTimeout(r, 200));
    }
    sous.textContent = 'Ne touche à rien, la page défile toute seule.';
    scrollTo(0, 0); cibleY = lisseY = 0; vitesseY = 0;
    await new Promise((r) => setTimeout(r, 1400));       // laisser l'avance se remplir

    const trames = [], vitesses = [];
    let absentes = 0, total = 0, prevT = 0, prevY = 0;
    const o0 = octetsFilm(), t0 = performance.now();

    await new Promise((fini) => {
      let dep = performance.now();
      (function pas(now){
        const dt = now - dep; dep = now;
        /* On pousse la CIBLE, pas la position : tout le chemin habituel —
           lisseur compris — reste donc exercé. */
        const av = CIBLE * dt / 1000;
        if (molette) cibleY = Math.min(cibleY + av, basDePage);
        else scrollTo(0, Math.min(scrollY + av, basDePage));

        if (prevT) {
          trames.push(now - prevT);
          const d = scrollY - prevY;
          if (d > 0.01) vitesses.push(d / (now - prevT));
          total++;
          if (window.__POSEE < 0) absentes++;
        }
        prevT = now; prevY = scrollY;

        const p = (now - t0) / DUREE;
        barre.style.width = Math.min(100, p * 100).toFixed(0) + '%';
        if (p < 1 && scrollY < basDePage - 4) requestAnimationFrame(pas);
        else fini();
      })(performance.now());
    });

    const secondes = (performance.now() - t0) / 1000;
    const mbit = ((octetsFilm() - o0) * 8) / secondes / 1e6;

    trames.sort((a, b) => a - b);
    const tr = trames[trames.length >> 1] || 0;
    const ips = tr ? Math.round(1000 / tr) : 0;
    const moy = vitesses.reduce((a, b) => a + b, 0) / (vitesses.length || 1);
    const ec = Math.sqrt(vitesses.reduce((a, b) => a + (b - moy) ** 2, 0) / (vitesses.length || 1));
    const reg = moy > 0.0001 ? ec / moy : 0;
    const trous = total ? absentes / total : 0;

    /* LE VERDICT, dans l'ordre où les causes se masquent l'une l'autre : un
       rendu qui ne suit pas rend tout le reste illisible, et un film qui
       n'arrive pas se lit comme un rendu lent alors que la page tourne bien. */
    let cause, quoi;
    if (ips && ips < 45) {
      cause = 'Le rendu ne suit pas';
      quoi = `Cette machine n'affiche que ${ips} images par seconde pendant le défilement. ` +
             `C'est l'affichage lui-même qui coûte, pas le film.`;
    } else if (trous > 0.15) {
      cause = 'Les images n\'arrivent pas assez vite';
      quoi = `${Math.round(trous * 100)} % des trames n'avaient aucune image à montrer. ` +
             `Le film a reçu ${mbit.toFixed(1)} Mbit/s ; il en faut environ 18 à cette vitesse ` +
             `de défilement. La page tourne bien (${ips} i/s), c'est le débit qui manque.`;
    } else if (reg > 0.25) {
      cause = 'Le défilement est irrégulier';
      quoi = `La cadence est pleine (${ips} i/s) mais la vitesse varie de ` +
             `${Math.round(reg * 100)} % d'une trame à l'autre.`;
    } else {
      cause = 'Cette machine tient le film';
      quoi = `${ips} images par seconde, régularité ${Math.round(reg * 100)} %, ` +
             `${Math.round(trous * 100)} % de trames sans image, ${mbit.toFixed(1)} Mbit/s reçus. ` +
             `Rien ici n'explique un ralentissement.`;
    }

    const releve =
      `cause      ${cause}\n` +
      `cadence    ${ips} i/s (${tr.toFixed(1)} ms par trame)\n` +
      `régularité ${Math.round(reg * 100)} %\n` +
      `images     ${Math.round(trous * 100)} % de trames sans image\n` +
      `débit      ${mbit.toFixed(1)} Mbit/s\n` +
      `mémoire    ${octetsImage ? (cache.size * octetsImage / 1048576).toFixed(0) : '?'} Mo tenus` +
      `${navigator.deviceMemory ? ', machine ' + navigator.deviceMemory + ' Go' : ''}\n` +
      `écran      ${innerWidth}x${innerHeight} densité ${(devicePixelRatio || 1).toFixed(2)}\n` +
      `toile      ${canvas.width}x${canvas.height}, film ${filmL}x${filmH}\n` +
      `série      ${NOM}, ${SEQ.images} images, ` +
      `${SEQ.octets ? (SEQ.octets / 1024).toFixed(0) + ' Ko/image, ' : ''}` +
      `${exigence(NOM, course).toFixed(1)} Mbit/s exigés\n` +
      `molette    ${molette ? 'lissée' : 'native'}\n` +
      `agent      ${navigator.userAgent}`;

    etat.textContent = cause;
    etat.style.color = cause.indexOf('tient') > 0 ? '#6FD3AC' : '#F0A93A';
    barre.parentElement.style.display = 'none';
    sous.innerHTML = '';
    const par = document.createElement('p');
    par.style.cssText = 'margin:0 0 15px;color:#C3CCD7';
    par.textContent = quoi;
    const zone = document.createElement('textarea');
    zone.readOnly = true; zone.value = releve; zone.rows = 11;
    zone.style.cssText =
      'width:100%;background:#10151C;color:#9FE8D0;border:1px solid #2A323D;border-radius:7px;' +
      'padding:11px;font:12px/1.6 ui-monospace,SFMono-Regular,Menlo,monospace;resize:vertical';
    const rangee = document.createElement('div');
    rangee.style.cssText = 'display:flex;gap:9px;margin-top:12px;flex-wrap:wrap';
    const bouton = (txt, fn) => {
      const b = document.createElement('button');
      b.textContent = txt;
      b.style.cssText =
        'padding:10px 17px;border-radius:7px;border:1px solid #3A434F;background:#1D242D;' +
        'color:#EAEFF5;font:600 13.5px system-ui,sans-serif;cursor:pointer';
      b.addEventListener('click', fn);
      return b;
    };
    rangee.append(
      bouton('Copier le relevé', async (e) => {
        zone.select();
        try { await navigator.clipboard.writeText(releve); } catch (_) { document.execCommand('copy'); }
        e.target.textContent = 'Copié';
      }),
      bouton('Fermer', () => ecran.remove()),
    );
    sous.append(par, zone, rangee);
  })();
}

/* ------------------------------------------------------- le repère de section

   Sur une page de trente écrans, savoir où l'on se trouve vaut mieux qu'un
   menu qui ne dit rien. Le lien de la section en vue reste souligné d'ambre.

   Un observateur d'intersection plutôt qu'un calcul à chaque défilement : le
   navigateur fait le travail hors du fil principal, et la page tourne déjà à
   soixante images par seconde qu'il ne faut pas dépenser ici. La marge basse
   de -55 % choisit la section dont le HAUT a franchi le milieu de l'écran,
   ce qui donne le même verdict que l'oeil. */
(function repere(){
  const liens = new Map();
  for (const a of document.querySelectorAll('.menu a')) {
    const cible = document.querySelector(a.getAttribute('href'));
    if (cible) liens.set(cible, a);
  }
  if (!liens.size || typeof IntersectionObserver !== 'function') return;
  let vues = new Set();
  const oeil = new IntersectionObserver((entrees) => {
    for (const e of entrees) e.isIntersecting ? vues.add(e.target) : vues.delete(e.target);
    let gagnant = null;
    for (const [cible] of liens)
      if (vues.has(cible)) gagnant = cible;      /* la plus basse des visibles */
    for (const [cible, a] of liens) a.classList.toggle('ici', cible === gagnant);
  }, { rootMargin: '0px 0px -55% 0px' });
  for (const [cible] of liens) oeil.observe(cible);
})();

/* L'apparition des blocs de la suite. Une seule fois : on cesse d'observer
   après, pour qu'un aller-retour ne fasse pas clignoter la page. */
const oeil = new IntersectionObserver((entrees) => {
  for (const e of entrees) if (e.isIntersecting) {
    e.target.classList.add('vu');
    oeil.unobserve(e.target);
  }
}, { rootMargin: '-12% 0px -12% 0px' });
document.querySelectorAll('#suite section, #suite .etape, #suite .metier, #suite .chiffre')
  .forEach((n) => oeil.observe(n));

/* L'acte en scène : le plus proche du centre de l'écran, et LUI SEUL.

   Un observateur d'intersection ne peut pas donner ça. Des sections pleine
   hauteur se recouvrent forcément dans la bande observée au moment de la
   charnière : deux actes s'y déclaraient visibles en même temps, leurs deux
   textes s'affichaient l'un sur l'autre et leurs deux voiles s'additionnaient
   jusqu'au noir. On désigne donc un seul gagnant, mesuré à chaque image. */
let enScene = -1;
function acteCourant(){
  const milieu = scrollY + innerHeight / 2;
  let gagnant = 0, meilleur = Infinity;
  for (let i = 0; i < centres.length; i++) {
    const d = abs(centres[i] - milieu);
    if (d < meilleur) { meilleur = d; gagnant = i; }
  }
  if (gagnant === enScene) return;
  if (enScene >= 0) actes[enScene].classList.remove('en-scene');
  actes[gagnant].classList.add('en-scene');
  enScene = gagnant;
}

/* ------------------------------------------------------------- le démarrage */
(async function demarrer(){
  redimensionner();
  mesurer();
  const amorce = min(16, SEQ.images);
  let faites = 0;
  /* `lire` et non `charger` : le plafond par image ne concerne que la fenêtre
     glissante. À l'amorçage il n'y a encore rien à afficher, donc rien à
     saccader — on décode aussi vite que possible. */
  const _t0 = performance.now();
  await Promise.all(Array.from({ length: amorce }, (v, i) => {
    encours.add(i);
    return lire(i).then(() => {
      const p = round(++faites / amorce * 100);
      jauge.style.width = p + '%';
      pct.textContent = p + ' %';
    });
  }));

  /* ------------------------------------------------------------ L'ARBITRAGE

     L'amorçage vient de télécharger seize images en parallèle : c'est une
     mesure du débit RÉEL, faite sur cette page et sur cette ligne. Elle vaut
     mieux que `downlink`, que le navigateur lisse et arrondit, et elle arrive
     encore à temps — la page n'est pas révélée.

     Si la série retenue ne peut pas être nourrie, on en change ICI, avant que
     le visiteur voie quoi que ce soit. Changer plus tard obligerait à vider un
     cache déjà rempli et se verrait à l'écran.

     ON MESURE LE RÉSEAU, PAS LE DÉCODAGE. Première version : octets reçus
     divisés par la durée totale de l'amorçage. Elle rétrogradait sur réseau
     LIBRE — parce que seize images décodées en parallèle prennent à peu près le
     même temps quelle que soit la ligne. La durée mesurée était celle du
     décodeur, et le débit qu'on en tirait était un plancher, pas une capacité.

     On lit donc les minutages du navigateur, qui séparent le transfert du
     reste : octets transférés sur la durée pendant laquelle des requêtes
     étaient réellement en vol.

     Le facteur 0,8 n'est pas de la prudence gratuite : l'amorçage tire seize
     images d'un coup sur une ligne au repos, ce qui flatte le débit par rapport
     à un défilement qui dure. Mieux vaut sous-estimer et servir une image un
     peu moins fine que surestimer et servir un diaporama. */
  const _mesureReseau = () => {
    let bas = Infinity, haut = 0, poids = 0, n = 0;
    for (const r of performance.getEntriesByType('resource')) {
      if (r.name.indexOf('/assets/film/') < 0 || !r.responseEnd) continue;
      const t = r.transferSize || r.encodedBodySize || 0;
      if (!t) continue;
      poids += t; n++;
      bas = min(bas, r.startTime); haut = max(haut, r.responseEnd);
    }
    const span = (haut - bas) / 1000;
    return (n >= 4 && span > 0.03) ? (poids * 8 / 1e6) / span * 0.8 : 0;
  };
  const _sec = (performance.now() - _t0) / 1000;
  const _reelMesure = _mesureReseau();
  if (_reelMesure > 0 && !SOURCES) {
    const _reel = _reelMesure;
    const _autre = selonDebit(_dispo, _reel, course);
    const _exig = exigence(NOM, course);
    if (_autre && _autre !== NOM && _exig > _reel) {
      const _av = NOM;
      NOM = _autre;
      SEQ = SEQUENCES[NOM];
      /* Tout ce qui a été décodé appartenait à l'AUTRE série : le garder
         mélangerait deux définitions sur la même toile. */
      for (const im of cache.values()) im.close?.();
      cache.clear(); encours.clear();
      octetsImage = 0; filmL = filmH = 0; dessinee = -1; posee = -1;
      reglerFenetre();
      console.info(`film : ${_av} -> ${NOM} — ${_exig.toFixed(1)} Mbit/s exigés, ` +
                   `${_reel.toFixed(1)} mesurés`);
      etape.textContent = 'Adaptation à votre connexion…';
      let refaites = 0;
      const amorce2 = min(16, SEQ.images);
      await Promise.all(Array.from({ length: amorce2 }, (v, i) => {
        encours.add(i);
        return lire(i).then(() => {
          const p = round(++refaites / amorce2 * 100);
          jauge.style.width = p + '%';
          pct.textContent = p + ' %';
        });
      }));
    }
  }

  /* Si rien n'a pu être décodé, on le DIT. La page se révélait autrefois quand
     même, sur une toile vide : le visiteur voyait un écran noir sans savoir si
     ça chargeait encore, si c'était cassé, ou si c'était voulu. */
  if (!cache.size) {
    etape.textContent = 'Séquence introuvable';
    return;
  }
  if (echecs) console.warn(`${echecs} image(s) non décodée(s)`);

  /* Publié pour la mise en page : une direction artistique peut vouloir
     afficher un relevé qui avance avec le film. Sans ce nombre, elle
     devrait recalculer la progression de son côté — et deux calculs de la
     même chose finissent toujours par diverger. */
  window.__IMAGES = SEQ.images;
  dessiner(0);
  requestAnimationFrame(boucle);
  voile.classList.add('parti');
})();
