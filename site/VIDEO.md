# La vidéo source du film — prompts complets

Le lecteur (`film.html`) ne fait pas de 3D. Il affiche une suite d'images que
le défilement parcourt en avant et en arrière. Tout le réalisme est donc décidé
**avant** : dans la vidéo. Ce fichier contient les prompts à coller tels quels,
et surtout la raison de chaque contrainte — parce que les contraintes ne
viennent pas du goût, elles viennent de la façon dont le lecteur consomme les
images.

## Ce qui rend une vidéo utilisable, et ce qui la disqualifie

| Contrainte | Pourquoi elle existe |
|---|---|
| **Un seul mouvement continu, aucune coupe** | Le défilement est une ligne. Une coupe au milieu devient un saut brutal que le visiteur déclenche lui-même, dans les deux sens. |
| **Vitesse rigoureusement constante** | Le visiteur impose sa propre vitesse. Toute accélération filmée s'ajoute à la sienne et se lit comme un à-coup. |
| **Aucun flou de mouvement** | Une image extraite est regardée **fixe**, parfois plusieurs secondes. Le flou de bougé, invisible à 24 i/s, devient une traînée figée et sale. Obturateur rapide, 1/1000 s. |
| **Exposition et balance des blancs verrouillées** | Une correction automatique en cours de plan fait respirer la luminosité. Au défilement, la page semble clignoter. |
| **Rien qui ne se lise que dans un sens** | On remonte la page. Une portière qui s'ouvre se refermera ; de la fumée qui monte redescendra. Tout ce qui a un sens physique évident se trahit à l'envers. |
| **Le sujet entier, avec de la marge** | Un bord de voiture qui touche le cadre à un moment du tour ne peut plus être recadré. |
| **Fond fixe, sol fixe** | Ce sont les seuls repères stables de l'image. S'ils bougent, tout bouge. |
| **Boucle fermée** (dernière image = première) | Un tour de 360° qui ne referme pas produit un saut à la fin du défilement. |
| **Ni personne, ni texte, ni plaque, ni logo** | Un visage change d'une image à l'autre. Un texte généré est illisible. Une plaque et un logo posent un problème juridique. |

**Durée.** Le lecteur veut 150 images. À 24 i/s, il faut **au moins 7 secondes**
utiles — visez 8 s, la longueur standard d'un plan Veo, qui donne 192 images et
laisse de la marge pour jeter le début et la fin.

---

# 1 — Le plan principal : le tour complet (paysage)

C'est celui qui porte le site. Générez-le en premier, jugez-le, et ne passez
aux autres que s'il est bon.

```
Un tour de 360 degrés autour d'une berline compacte cinq portes, dans un studio photo automobile.

SUJET. Une voiture citadine cinq portes moderne, carrosserie gris anthracite métallisé propre et polie, jantes en alliage à cinq branches gris foncé, pneus noirs mats, vitres teintées sombres, phares à diodes éteints. Aucun badge, aucun logo, aucune marque, aucune plaque d'immatriculation : les emplacements sont lisses et vides. La voiture est immobile, roues droites, portières fermées, posée au centre exact d'un plateau tournant.

MOUVEMENT. La voiture pivote lentement sur elle-même, sur son axe vertical, à vitesse parfaitement constante, et accomplit exactement un tour complet de 360 degrés du début à la fin du plan. Le mouvement démarre déjà à sa vitesse de croisière et s'arrête net à la même vitesse : aucun démarrage progressif, aucun ralentissement final. La dernière image est identique à la première : le plan boucle. La caméra, elle, ne bouge pas d'un millimètre pendant tout le plan : hauteur fixe, distance fixe, focale fixe, aucun panoramique, aucun travelling, aucun zoom, aucun tremblement.

CAMÉRA. Objectif 50 mm, f/8, ISO 100, sur pied. Hauteur d'objectif à un mètre vingt du sol, soit un peu au-dessus de la ligne de capot, axe strictement horizontal — la voiture n'est vue ni en plongée ni en contre-plongée. Distance telle que la voiture occupe environ 70 % de la largeur du cadre au moment où elle est de profil, et reste entièrement visible avec une marge d'air nette sur les quatre côtés à chaque instant du tour, y compris de trois quarts. Mise au point sur le milieu de la voiture, nette de bout en bout, arrière-plan légèrement dégradé. Obturateur très rapide, 1/1000 s : chaque image extraite du plan doit être parfaitement nette, sans le moindre flou de mouvement, y compris sur les rayons des jantes.

LUMIÈRE. Studio automobile professionnel. Deux grandes rampes lumineuses continues et diffuses au plafond, parallèles à la voiture, qui dessinent sur la carrosserie deux longs reflets doux et étirés glissant sur les flancs à mesure que la voiture tourne. Un remplissage doux à hauteur d'homme sur les faces sombres. Lumière blanche neutre, 5500 K, rigoureusement identique du début à la fin. Exposition verrouillée, balance des blancs verrouillée : aucune variation de luminosité, de contraste ou de teinte pendant le plan.

DÉCOR. Cycloramas gris moyen neutre, mur et sol raccordés en courbe continue sans arête visible, uniforme, sans texture ni motif. Sol légèrement satiné qui renvoie un reflet sombre et flou de la voiture, jamais un miroir. Ombre portée douce et large sous la voiture, qui tourne avec elle. Le décor est absolument immobile et identique du début à la fin du plan.

RENDU. Prise de vue réelle, film publicitaire automobile, qualité commerciale. Colorimétrie neutre et fidèle, contraste maîtrisé, noirs profonds mais lisibles, hautes lumières des reflets contrôlées. Grain photographique très fin. 24 images par seconde, 8 secondes, format 16:9 horizontal, résolution maximale disponible.

INTERDIT. Coupe, changement de plan, fondu, mouvement de caméra, zoom, tremblement, accélération ou ralentissement du tour, flou de mouvement, flou de bougé, effet de vitesse, variation de lumière ou d'exposition, apparition ou disparition d'un objet, reflet d'équipe ou de matériel, personne, main, silhouette, texte, sous-titre, chiffre, logo, badge, marque, plaque d'immatriculation, filigrane, signature, portière ou coffre qui s'ouvre, roues qui tournent, fumée, poussière, eau, effet de particules, rendu 3D, image de synthèse, aspect jeu vidéo, couleurs saturées, HDR excessif.
```

**Pourquoi un plateau tournant et pas une caméra qui orbite.** Si la caméra
tourne autour de la voiture, tout bouge dans l'image : le fond, le sol,
l'ombre, la voiture. Le modèle a alors quatre choses à garder cohérentes, et
c'est le fond qui lâche en premier — il se met à ramper. Avec un plateau
tournant, le fond et le sol sont **cloués**, une seule chose bouge, et
l'instabilité éventuelle est confinée à la carrosserie. Visuellement le
résultat est le même ; techniquement il est bien plus sûr.

---

# 2 — Le plan portrait, pour les téléphones

**Ne recadrez pas le plan paysage.** Passer du 16:9 au 9:16 en gardant le
centre ne conserve que 32 % de la largeur : la voiture sort du cadre par les
deux côtés. C'est une composition à refaire, pas une découpe.

Même prompt que ci-dessus, avec ces trois paragraphes remplacés :

```
CAMÉRA. Objectif 50 mm, f/8, ISO 100, sur pied. Hauteur d'objectif à un mètre vingt du sol, axe strictement horizontal. Cadrage vertical : la voiture occupe environ 85 % de la largeur du cadre quand elle est de profil, centrée en hauteur, avec un large espace vide au-dessus d'elle et un espace plus court en dessous. Elle reste entièrement visible avec une marge d'air sur les quatre côtés à chaque instant du tour. Obturateur très rapide, 1/1000 s, netteté parfaite sur chaque image.

RENDU. Prise de vue réelle, film publicitaire automobile, qualité commerciale. Colorimétrie neutre et fidèle. Grain photographique très fin. 24 images par seconde, 8 secondes, format 9:16 vertical, résolution maximale disponible.
```

L'espace vide au-dessus n'est pas une faute de cadrage : c'est là que le texte
du site vient se poser.

---

# 3 — Les plans d'intérieur

L'intérieur ne se filme pas en tournant : on **avance**. Trois plans courts,
chacun autonome, chacun branché sur un acte du site.

## 3a — Entrée dans l'habitacle

```
Un plan d'approche continu qui entre dans l'habitacle d'une voiture citadine moderne par la portière conducteur ouverte.

MOUVEMENT. La caméra avance en ligne droite, à vitesse rigoureusement constante, depuis l'extérieur de la portière conducteur ouverte jusqu'à une position située juste derrière le volant, à hauteur des yeux du conducteur. Le mouvement est parfaitement rectiligne et régulier du début à la fin, sans accélération, sans ralentissement, sans rotation, sans tremblement. Rien ne bouge dans la scène : ni portière, ni siège, ni volant, ni essuie-glace, ni aiguille.

SUJET. Intérieur d'une citadine cinq portes récente, propre et neuve. Sièges en tissu gris foncé à surpiqûres, volant à trois branches gainé de cuir noir, tableau de bord en plastique moulé gris anthracite mat, écran central éteint et noir, aérateurs ronds chromés, levier de vitesses manuel. Aucun logo, aucune marque, aucun texte lisible sur le volant, l'écran ou les cadrans. Habitacle vide : aucun objet personnel, aucune personne.

CAMÉRA. Objectif 24 mm, f/5.6, ISO 200, sur rail motorisé, verticales redressées, axe horizontal. Obturateur rapide, 1/500 s, chaque image parfaitement nette, aucun flou de mouvement.

LUMIÈRE. Lumière du jour douce et diffuse entrant par le pare-brise et les vitres latérales, ciel couvert, aucun soleil direct, aucune ombre dure. Exposition et balance des blancs verrouillées : aucune variation de luminosité entre l'extérieur et l'intérieur pendant l'entrée. Blanc neutre, 5500 K.

RENDU. Prise de vue réelle, film publicitaire automobile. Colorimétrie neutre, contraste doux, ombres de l'habitacle ouvertes et lisibles. Grain très fin. 24 images par seconde, 6 secondes, format 16:9 horizontal, résolution maximale.

INTERDIT. Coupe, fondu, rotation de caméra, zoom, tremblement, flou de mouvement, variation d'exposition, personne, main, texte, chiffre affiché, logo, marque, reflet de l'équipe dans le pare-brise, rendu 3D, image de synthèse.
```

## 3b — Le poste de conduite qui s'éclaire

Un plan fixe, mais **rien ne doit s'allumer** : le défilement l'éteindrait en
remontant. On filme donc un travelling latéral sur un tableau de bord déjà
allumé.

```
Un travelling latéral lent devant le tableau de bord d'une voiture citadine moderne.

MOUVEMENT. La caméra glisse latéralement de la droite vers la gauche, parallèlement au tableau de bord, à vitesse rigoureusement constante, sur environ soixante centimètres. Aucune rotation, aucune avance, aucun recul, aucun tremblement. Tout dans la scène est absolument immobile : aucune aiguille ne bouge, aucun voyant ne clignote, aucun affichage ne change.

SUJET. Le combiné d'instruments et la console centrale d'une citadine récente. Cadrans analogiques à aiguilles fines sur fond noir mat, cerclages chromés, rétroéclairage blanc froid déjà allumé et constant. Écran central allumé affichant uniquement un aplat de couleur sombre uni, sans texte ni icône. Plastiques gris anthracite mats, inserts satinés, molettes crantées. Aucun logo, aucune marque, aucun chiffre lisible.

CAMÉRA. Objectif 50 mm, f/2.8, ISO 400, sur rail motorisé. Faible profondeur de champ, mise au point fixe sur le plan des cadrans, avant-plan et arrière-plan doucement flous. Obturateur rapide, 1/500 s, netteté parfaite du sujet sur chaque image.

LUMIÈRE. Lumière du jour douce et diffuse par le pare-brise, complétée par le rétroéclairage constant des instruments. Aucune source qui varie. Exposition et balance des blancs verrouillées.

RENDU. Prise de vue réelle, film publicitaire automobile. Colorimétrie neutre, noirs profonds, reflets contrôlés sur les cerclages. Grain très fin. 24 images par seconde, 6 secondes, format 16:9 horizontal, résolution maximale.

INTERDIT. Coupe, fondu, zoom, rotation, tremblement, flou de mouvement, aiguille qui bouge, voyant qui s'allume ou clignote, affichage qui change, variation d'exposition, personne, main, texte, chiffre, logo, marque, rendu 3D, image de synthèse.
```

## 3c — La matière, de très près

```
Un travelling latéral très lent sur la texture d'un siège automobile.

MOUVEMENT. La caméra glisse latéralement de la gauche vers la droite, parallèlement à la surface, à vitesse rigoureusement constante, sur environ trente centimètres, en gardant exactement la même distance à la matière. Aucune rotation, aucun changement de mise au point, aucun tremblement. La scène est parfaitement immobile.

SUJET. Gros plan sur l'assise d'un siège en tissu gris foncé à trame serrée, avec une couture double surpiquée beige qui traverse le cadre en diagonale. Fibres du tissu très lisibles, léger relief de la mousse sous la toile, grain de la matière net.

CAMÉRA. Objectif macro 100 mm, f/4, ISO 200, sur rail motorisé. Mise au point fixe sur le plan de la couture, très faible profondeur de champ, les bords du cadre doucement flous. Obturateur rapide, 1/500 s, netteté parfaite sur chaque image.

LUMIÈRE. Une seule grande source diffuse rasante venant de la gauche, qui révèle le relief du tissu et le volume de la couture. Ombres douces et longues dans la trame. Lumière blanche neutre 5500 K, constante. Exposition et balance des blancs verrouillées.

RENDU. Prise de vue réelle, photographie de matière, qualité commerciale. Colorimétrie neutre et fidèle, contraste doux, texture privilégiée. Grain très fin. 24 images par seconde, 6 secondes, format 16:9 horizontal, résolution maximale.

INTERDIT. Coupe, fondu, zoom, changement de mise au point, tremblement, flou de mouvement, variation de lumière, main, doigt, personne, texte, logo, marque, poussière volante, rendu 3D, image de synthèse.
```

---

# 4 — Juger la vidéo en dix secondes

Avant de me l'envoyer, regardez-la **deux fois** :

1. **En lecture normale.** Si quelque chose vous gêne ici, ce sera pire au
   défilement — la scrutation d'une image fixe est bien plus sévère que la
   lecture à 24 i/s.
2. **Image par image**, en avançant à la flèche, sur les rayons d'une jante.
   C'est le détecteur le plus fiable : les rayons sont fins, répétitifs et
   contrastés, et c'est là que l'incohérence se voit la première.

Les trois échecs à reconnaître :

- **Le frémissement.** Les détails fins — rayons, grilles, surpiqûres —
  vibrent d'une image à l'autre sans que rien ne bouge vraiment. Le modèle
  ré-invente le détail à chaque image. Irrécupérable : à refaire.
- **Le reflet qui rampe.** Les reflets glissent sur la carrosserie sans
  rapport avec la rotation, ou changent de forme. Souvent réparable en
  simplifiant la lumière décrite (une seule rampe au lieu de deux).
- **La silhouette qui respire.** La voiture change discrètement de longueur ou
  de hauteur pendant le tour. C'est le plus grave et le plus dur à voir en
  lecture normale — d'où l'image par image. À refaire, en insistant sur
  « proportions rigoureusement constantes, même véhicule du début à la fin ».

Si le tour de 360° ne boucle pas parfaitement, ce n'est pas grave : dites-le
moi, je coupe la séquence avant le saut. Il vaut mieux 140 images propres que
150 avec un raccord.

---

# 5 — Quand vous me l'envoyez

Deux commandes, dans cet ordre :

```
python3 film_video.py ta-video.mp4 150 1440 large
python3 build_film.py 72 1280
```

Le portrait, quand il existera :

```
python3 film_video.py ta-video-verticale.mp4 100 900 etroit
python3 build_film.py 72 1280
```

`film_video.py` répartit les prises sur toute la durée du fichier — il n'y a
donc rien à recouper avant de me l'envoyer, sauf si vous voulez jeter un début
ou une fin ratés.

---

# 6 — La limite qu'il faut dire au client

Cette voiture est **générée**. Elle n'a ni marque, ni plaque, ni badge, et
c'est délibéré : c'est une démonstration de mise en scène, pas l'annonce d'un
véhicule réel.

Pour un vrai loueur, la règle du dossier tient toujours — le décor, les
matières et l'ambiance peuvent être générés, **jamais le véhicule loué**.
Montrer une Clio générée à la place de celle qu'on loue, c'est une publicité
trompeuse, en plus du problème d'image de marque. Le jour où le client signe,
on filme sa voiture : un plateau tournant, huit secondes, et le même pipeline
tourne sans changer une ligne.
