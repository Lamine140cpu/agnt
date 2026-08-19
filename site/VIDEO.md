# La chorégraphie du film — prompts complets

Le lecteur (`film.html`) ne calcule rien. Il affiche une suite d'images que le
défilement parcourt dans les deux sens. Tout le spectacle est donc décidé
**avant**, dans les vidéos sources. Ce fichier contient la chorégraphie, les
prompts à coller tels quels, et la raison de chaque contrainte.

---

## Les trois lois

Elles ne viennent pas du goût. Elles viennent de la façon dont le défilement
consomme les images, et elles décident de tout le reste.

### 1. Réversible, pas immobile

Le visiteur remonte la page. Ce qui se joue à l'envers doit rester crédible.

- **Réversible, donc autorisé :** une portière qui s'ouvre (elle se referme),
  un éclaté qui se rassemble, une caméra qui avance puis recule, une roue qui
  tourne, un capot qui se lève. Ce sont des mécanismes. Remontés, ils se
  lisent comme des mécanismes.
- **Entropique, donc interdit :** fumée qui se dissipe, éclaboussure,
  poussière soulevée, étincelles, buée qui s'efface, papier qui brûle. Ça ne
  se remonte pas. L'œil sait que ça ne remonte pas.

### 2. Aucun flou de mouvement

Contre-intuitif pour de la vidéo, mais une image extraite est regardée
**fixe**, parfois plusieurs secondes. Le flou de bougé, invisible à 24 i/s,
devient une traînée sale figée. Obturateur 1/1000 s partout.

L'exception est la roue en rotation : figée au 1/1000, elle prend une position
de rayons différente à chaque image et **stroboscope** violemment au
défilement. Pour le plan de roulage, et pour lui seul, on demande une rotation
lente et continue avec un léger filé radial sur les rayons uniquement.

### 3. Le poids est linéaire

**46 Ko l'image livrée**, mesurés sur la première série (150 images →
6,9 Mo). Un plan de 8 s ramené à 40 images coûte donc **1,8 Mo**. Six plans
font 11 Mo, ce qui est la limite d'un fichier unique. Au-delà, il faut servir
les images depuis le disque au lieu de les embarquer — ce que le lecteur sait
déjà faire, mais qui n'est plus une démo qui tient dans un fichier.

**Six beats. Pas quinze.** C'est le vrai budget de la chorégraphie.

---

## Le chaînage : comment dépasser les huit secondes

Un plan généré fait 8 secondes. La chorégraphie en fait cinquante. On les
enchaîne, et la technique tient en une phrase :

> **La dernière image d'un plan devient l'image de départ du suivant.**

Les modèles vidéo acceptent une image de départ (image-to-video). On leur donne
la fin du plan précédent, et le nouveau plan reprend exactement là. Sans ça,
chaque plan repart d'une voiture *presque* identique — autre nuance de gris,
autres jantes, ombre décalée — et chaque jointure saute aux yeux.

La boucle de travail :

```
1. générer le plan 1
2. python3 film_raccord.py plan1.mp4          → plan1-fin.png
3. joindre plan1-fin.png au prompt du plan 2, générer
4. python3 film_raccord.py plan2.mp4          → plan2-fin.png
5. ... et ainsi de suite
```

Chaque prompt ci-dessous commence donc par une ligne de raccord, à garder
telle quelle **sauf pour le plan 1**.

---

# La chorégraphie — six beats

| # | Beat | Ce qu'il raconte | Risque |
|---|---|---|---|
| 1 | **Le tour** | l'objet, entier, sous tous ses angles | faible |
| 2 | **L'ouverture** | les cinq ouvrants se déploient ensemble | faible |
| 3 | **L'éclaté** | les panneaux s'écartent, la structure apparaît | moyen |
| 4 | **L'entrée** | la caméra pénètre dans l'habitacle | faible |
| 5 | **Le poste** | le tableau de bord, de très près | faible |
| 6 | **Le départ** | tout se referme, la voiture roule | **élevé** |

Générez dans l'ordre. Si un beat rate, les suivants sont perdus — ils partent
de son image de fin.

---

## Beat 1 — Le tour

```
Un tour de 360 degrés autour d'une voiture citadine, dans un studio photo automobile.

SUJET. Une voiture citadine cinq portes moderne, carrosserie gris anthracite métallisé propre et polie, jantes en alliage à cinq branches gris foncé, pneus noirs mats, vitres teintées sombres, phares à diodes éteints. Aucun badge, aucun logo, aucune marque, aucune plaque d'immatriculation : les emplacements sont lisses et vides. La voiture est immobile, roues droites, portières fermées, posée au centre exact d'un plateau tournant.

MOUVEMENT. La voiture pivote sur elle-même, sur son axe vertical, à vitesse parfaitement constante, et accomplit exactement un tour complet de 360 degrés du début à la fin du plan. Le mouvement démarre déjà à sa vitesse de croisière et s'arrête net à la même vitesse : aucun démarrage progressif, aucun ralentissement final. La dernière image est identique à la première : le plan boucle. Les proportions de la voiture sont rigoureusement constantes pendant tout le tour — même longueur, même hauteur, même empattement, même dessin de jantes. La caméra ne bouge pas d'un millimètre : hauteur fixe, distance fixe, focale fixe, aucun panoramique, aucun travelling, aucun zoom, aucun tremblement.

CAMÉRA. Objectif 50 mm, f/8, ISO 100, sur pied. Hauteur d'objectif à un mètre vingt du sol, un peu au-dessus de la ligne de capot, axe strictement horizontal — la voiture n'est vue ni en plongée ni en contre-plongée. Distance telle que la voiture occupe environ 65 % de la largeur du cadre quand elle est de profil, et reste entièrement visible avec une marge d'air nette sur les quatre côtés à chaque instant du tour. Mise au point sur le milieu de la voiture, nette de bout en bout. Obturateur très rapide, 1/1000 s : chaque image du plan doit être parfaitement nette, sans le moindre flou de mouvement, y compris sur les rayons des jantes.

LUMIÈRE. Studio automobile professionnel. Deux grandes rampes lumineuses continues et diffuses au plafond, parallèles à la voiture, qui dessinent sur la carrosserie deux longs reflets doux et étirés glissant sur les flancs à mesure qu'elle tourne. Un remplissage doux à hauteur d'homme sur les faces sombres. Lumière blanche neutre, 5500 K, rigoureusement identique du début à la fin. Exposition verrouillée, balance des blancs verrouillée : aucune variation de luminosité, de contraste ou de teinte pendant le plan.

DÉCOR. Cyclorama gris moyen neutre, mur et sol raccordés en courbe continue sans arête visible, uniforme, sans texture ni motif. Sol légèrement satiné qui renvoie un reflet sombre et flou de la voiture, jamais un miroir. Ombre portée douce et large sous la voiture, qui tourne avec elle. Le décor est absolument immobile et identique du début à la fin.

RENDU. Prise de vue réelle, film publicitaire automobile, qualité commerciale. Colorimétrie neutre et fidèle, contraste maîtrisé, noirs profonds mais lisibles, hautes lumières des reflets contrôlées. Grain photographique très fin. 24 images par seconde, 8 secondes, format 16:9 horizontal, résolution maximale disponible.

INTERDIT. Coupe, changement de plan, fondu, mouvement de caméra, zoom, tremblement, accélération ou ralentissement du tour, flou de mouvement, flou de bougé, variation de lumière ou d'exposition, apparition ou disparition d'un objet, changement de proportions du véhicule, reflet d'équipe ou de matériel, personne, main, silhouette, texte, sous-titre, chiffre, logo, badge, marque, plaque d'immatriculation, filigrane, signature, portière qui s'ouvre, fumée, poussière, eau, particules, rendu 3D, image de synthèse, aspect jeu vidéo, couleurs saturées, HDR excessif.
```

**Pourquoi un plateau tournant et pas une caméra qui orbite.** Si la caméra
tourne, le fond, le sol, l'ombre et la voiture bougent tous les quatre : le
modèle a quatre choses à garder cohérentes et c'est le fond qui lâche en
premier, il se met à ramper. Avec un plateau, le décor est **cloué**, une
seule chose bouge, et l'instabilité éventuelle reste confinée à la
carrosserie. À l'écran, le résultat est identique.

---

## Beat 2 — L'ouverture

Le beat que le tour ne donne pas : la voiture se déploie. Purement mécanique,
donc parfaitement réversible.

```
L'image jointe est la première image de ce plan. Reprends exactement la même voiture, le même studio, la même lumière, le même cadrage, la même position.

Les ouvrants d'une voiture citadine se déploient simultanément, en silence, comme un mécanisme.

MOUVEMENT. Depuis la voiture entièrement fermée, les cinq ouvrants s'ouvrent EN MÊME TEMPS et à vitesse rigoureusement constante, du début à la fin du plan : les deux portières avant, les deux portières arrière, et le hayon. Les portières pivotent sur leurs charnières jusqu'à environ soixante-dix degrés, symétriquement à gauche et à droite. Le hayon se lève lentement vers l'arrière. Le capot reste fermé. Le mouvement est parfaitement continu, linéaire, sans à-coup, sans rebond, sans hésitation, et n'est pas terminé à la dernière image : les ouvrants sont encore en train de s'écarter. Tout le reste est absolument immobile : la caisse ne bouge pas, ne s'enfonce pas sur ses suspensions, les roues ne tournent pas, la voiture ne pivote pas. La caméra est rigoureusement fixe : aucun mouvement, aucun zoom, aucun tremblement.

SUJET. Même voiture citadine cinq portes gris anthracite métallisé que l'image jointe, vue de trois quarts avant gauche. Aucun badge, aucun logo, aucune plaque. À mesure que les portières s'écartent, on découvre l'intérieur : sièges en tissu gris foncé à surpiqûres, volant à trois branches gainé de cuir noir, tableau de bord gris anthracite mat, écran central éteint. Habitacle vide, propre, aucun objet, aucune personne. Le coffre découvert est vide et tapissé de gris.

CAMÉRA. Objectif 35 mm, f/8, ISO 100, sur pied, axe horizontal à un mètre vingt du sol. Cadrage assez large pour que les portières entièrement ouvertes tiennent dans le cadre avec de la marge sur les quatre côtés — la voiture ouverte est bien plus large que fermée, prévois cette place dès la première image. Nette de bout en bout. Obturateur 1/1000 s, aucune image floue.

LUMIÈRE. Identique à l'image jointe : deux rampes diffuses au plafond, remplissage doux, 5500 K, exposition et balance des blancs verrouillées. Aucune variation de luminosité pendant l'ouverture, y compris quand l'intérieur sombre entre dans le cadre.

DÉCOR. Identique à l'image jointe : cyclorama gris neutre, sol satiné, ombre portée douce. Absolument immobile.

RENDU. Prise de vue réelle, film publicitaire automobile, qualité commerciale. Colorimétrie neutre, grain très fin. 24 images par seconde, 8 secondes, format 16:9 horizontal, résolution maximale.

INTERDIT. Coupe, fondu, mouvement de caméra, zoom, tremblement, flou de mouvement, ouverture saccadée, rebond, ouvrant qui s'ouvre avant les autres, capot qui s'ouvre, voiture qui bouge ou pivote, roues qui tournent, suspension qui s'enfonce, variation d'exposition, personne, main, texte, chiffre, logo, marque, plaque, fumée, poussière, particules, rendu 3D, image de synthèse.
```

> **Astuce de cadrage.** La voiture portières ouvertes est presque deux fois
> plus large. Si le beat 1 la cadre trop serré, le beat 2 n'a plus la place et
> les portières sortent du champ. C'est pour ça que le beat 1 demande 65 % de
> la largeur et pas 70.

---

## Beat 3 — L'éclaté

Le beat le plus spectaculaire, et le plus fragile. À générer en deuxième si
vous ne devez en tester qu'un après le tour.

```
L'image jointe est la première image de ce plan. Reprends exactement la même voiture, le même studio, la même lumière, le même cadrage.

Les panneaux de carrosserie d'une voiture citadine s'écartent lentement dans l'espace, en vue éclatée de studio.

MOUVEMENT. Depuis la voiture portières ouvertes de l'image jointe, les éléments de carrosserie se détachent et s'écartent EN MÊME TEMPS, radialement, vers l'extérieur, à vitesse rigoureusement constante et linéaire du début à la fin : les portières s'éloignent latéralement, le capot monte et avance, le hayon monte et recule, le toit s'élève verticalement, les quatre roues s'écartent vers l'extérieur, les pare-chocs avancent et reculent. Chaque élément se déplace en ligne droite, garde son orientation exacte, ne tourne pas sur lui-même, ne se déforme pas, ne rétrécit pas. Ils flottent, suspendus, sans câble ni support. Le châssis, l'habitacle et les sièges restent parfaitement immobiles au centre. Le mouvement n'est pas terminé à la dernière image : les éléments s'écartent encore. La caméra est rigoureusement fixe.

SUJET. Même voiture citadine cinq portes gris anthracite métallisé que l'image jointe. Chaque panneau détaché montre sa tranche : tôle peinte à l'extérieur, apprêt gris mat et renforts à l'intérieur. Le châssis central révèle les sièges en tissu gris foncé, le volant, le tableau de bord. Aucun badge, aucun logo, aucune plaque, aucun texte sur aucune pièce.

CAMÉRA. Objectif 35 mm, f/8, ISO 100, sur pied, axe horizontal, rigoureusement fixe. Cadrage large : à la dernière image, tous les éléments écartés tiennent encore dans le cadre avec une marge nette. Tout est net, du panneau le plus proche au plus lointain. Obturateur 1/1000 s.

LUMIÈRE. Identique à l'image jointe : deux rampes diffuses au plafond, 5500 K, exposition et balance des blancs verrouillées. Chaque élément détaché porte sa propre ombre douce, cohérente avec les rampes.

DÉCOR. Cyclorama gris neutre identique, absolument immobile. Le sol satiné continue de renvoyer un reflet sombre et flou.

RENDU. Prise de vue réelle, film publicitaire automobile, vue éclatée de studio, qualité commerciale. Colorimétrie neutre, grain très fin. 24 images par seconde, 8 secondes, format 16:9 horizontal, résolution maximale.

INTERDIT. Coupe, fondu, mouvement de caméra, zoom, tremblement, flou de mouvement, élément qui tourne sur lui-même, élément qui se déforme ou change de taille, élément qui sort du cadre, explosion, projection, éclat, débris, écartement saccadé ou à vitesse variable, câble, support, socle, variation d'exposition, personne, main, texte, chiffre, logo, marque, plaque, fumée, poussière, étincelle, particules, rendu 3D, image de synthèse.
```

**Le mot à ne pas employer : « explosion ».** « Vue éclatée » est un terme de
schéma technique, mais les modèles entendent l'autre sens et vous rendent des
débris projetés — irréversible, donc inutilisable. D'où « s'écartent
radialement, en ligne droite, à vitesse constante » et le mot *explosion* mis
explicitement à l'index.

---

## Beat 4 — L'entrée

```
L'image jointe est la première image de ce plan. Reprends exactement la même voiture, la même lumière, le même décor.

Un plan d'approche continu qui entre dans l'habitacle d'une voiture citadine par la portière conducteur ouverte.

MOUVEMENT. Depuis la position de l'image jointe, tous les éléments de carrosserie reviennent à leur place et la voiture se reconstitue pendant que la caméra avance en ligne droite vers la portière conducteur ouverte, la franchit, et s'arrête juste derrière le volant, à hauteur des yeux du conducteur. Les deux mouvements sont simultanés, rigoureusement linéaires et à vitesse constante du début à la fin : aucune accélération, aucun ralentissement, aucune rotation de la caméra, aucun tremblement. À la dernière image la voiture est entièrement remontée, portière conducteur encore ouverte, et la caméra est en place derrière le volant.

SUJET. Intérieur d'une citadine cinq portes récente, propre et neuve. Sièges en tissu gris foncé à surpiqûres, volant à trois branches gainé de cuir noir, tableau de bord en plastique moulé gris anthracite mat, écran central éteint et noir, aérateurs ronds cerclés de satiné, levier de vitesses manuel. Aucun logo, aucune marque, aucun texte lisible sur le volant, l'écran ou les cadrans. Habitacle vide : aucun objet personnel, aucune personne.

CAMÉRA. Objectif 24 mm, f/5.6, ISO 200, sur rail motorisé, verticales redressées, axe horizontal, aucune rotation. Nette de bout en bout. Obturateur 1/1000 s, chaque image parfaitement nette.

LUMIÈRE. Les rampes du studio au-dessus, plus une lumière douce et diffuse entrant par le pare-brise et les vitres. Aucune ombre dure. Exposition et balance des blancs verrouillées : aucune variation de luminosité au passage de l'extérieur clair vers l'habitacle sombre — l'intérieur reste ouvert et lisible. Blanc neutre 5500 K.

RENDU. Prise de vue réelle, film publicitaire automobile. Colorimétrie neutre, contraste doux, ombres de l'habitacle ouvertes et lisibles. Grain très fin. 24 images par seconde, 8 secondes, format 16:9 horizontal, résolution maximale.

INTERDIT. Coupe, fondu, rotation de caméra, zoom, tremblement, flou de mouvement, remontage saccadé, élément qui se remet en place avant les autres, variation d'exposition, assombrissement à l'entrée dans l'habitacle, personne, main, silhouette, texte, chiffre affiché, logo, marque, reflet de l'équipe dans le pare-brise, fumée, particules, rendu 3D, image de synthèse.
```

---

## Beat 5 — Le poste

Rien ne doit **s'allumer** : le défilement l'éteindrait en remontant, et un
voyant qui s'éteint tout seul se lit comme une panne. On filme un tableau de
bord déjà allumé, et c'est la caméra qui bouge.

```
L'image jointe est la première image de ce plan. Reprends exactement le même habitacle, la même lumière.

Un travelling latéral lent devant le tableau de bord d'une voiture citadine.

MOUVEMENT. La caméra glisse latéralement de la droite vers la gauche, parallèlement au tableau de bord, à vitesse rigoureusement constante, sur environ soixante centimètres, en gardant exactement la même distance à la planche de bord. Aucune rotation, aucune avance, aucun recul, aucun changement de mise au point, aucun tremblement. Tout dans la scène est absolument immobile : aucune aiguille ne bouge, aucun voyant ne s'allume, ne s'éteint ni ne clignote, aucun affichage ne change, le volant ne tourne pas.

SUJET. Le combiné d'instruments et la console centrale d'une citadine récente. Cadrans analogiques à aiguilles fines sur fond noir mat, cerclages satinés, rétroéclairage blanc froid DÉJÀ allumé et parfaitement constant, aiguilles arrêtées à zéro. Écran central allumé affichant uniquement un aplat de couleur sombre uni, sans texte ni icône. Plastiques gris anthracite mats, inserts satinés, molettes crantées, grain du plastique très lisible. Aucun logo, aucune marque, aucun chiffre lisible.

CAMÉRA. Objectif 50 mm, f/2.8, ISO 400, sur rail motorisé. Faible profondeur de champ, mise au point FIXE sur le plan des cadrans, avant-plan et arrière-plan doucement flous. Obturateur 1/1000 s, netteté parfaite du sujet sur chaque image.

LUMIÈRE. Lumière du jour douce et diffuse par le pare-brise, complétée par le rétroéclairage constant des instruments. Aucune source qui varie. Exposition et balance des blancs verrouillées.

RENDU. Prise de vue réelle, film publicitaire automobile. Colorimétrie neutre, noirs profonds, reflets contrôlés sur les cerclages. Grain très fin. 24 images par seconde, 8 secondes, format 16:9 horizontal, résolution maximale.

INTERDIT. Coupe, fondu, zoom, rotation, tremblement, flou de mouvement, changement de mise au point, aiguille qui bouge, voyant qui s'allume ou s'éteint ou clignote, affichage qui change, volant qui tourne, variation d'exposition, personne, main, doigt, texte, chiffre, logo, marque, rendu 3D, image de synthèse.
```

---

## Beat 6 — Le départ

Le plan que vous vouliez, et le plus risqué. Deux dangers : le fond qui défile
donne au modèle beaucoup à inventer, et les rayons de roue figés
stroboscopent. Les deux ont une parade, écrite dans le prompt.

```
L'image jointe est la première image de ce plan. Reprends exactement la même voiture.

Une voiture citadine roule à vitesse constante, suivie par une caméra qui l'accompagne exactement à sa vitesse.

MOUVEMENT. La voiture roule en ligne droite à vitesse constante. La caméra l'accompagne latéralement, exactement à la même vitesse, à distance constante : la voiture reste donc RIGOUREUSEMENT IMMOBILE dans le cadre, à la même place, à la même taille, du début à la fin du plan. Seuls le sol et l'arrière-plan défilent. Les roues tournent lentement, régulièrement, dans le sens de la marche, avec un léger filé radial sur les rayons uniquement. Rien d'autre ne bouge : la caisse ne tangue pas, ne rebondit pas, la direction reste droite, les portières sont fermées, aucune suspension ne travaille.

SUJET. Même voiture citadine cinq portes gris anthracite métallisé que l'image jointe, vue de profil strict, entièrement dans le cadre avec une marge d'air nette devant, derrière, au-dessus et en dessous. Aucun badge, aucun logo, aucune marque, aucune plaque d'immatriculation. Phares à diodes allumés, blancs et constants. Carrosserie parfaitement nette et sans flou.

DÉCOR. Une route lisse et uniforme, asphalte gris foncé sans marquage au sol, sans nid-de-poule, sans texture marquée. L'arrière-plan est TOTALEMENT FLOU, réduit à un dégradé continu de gris-vert et de gris clair, sans aucun détail identifiable : ni arbre distinct, ni bâtiment, ni panneau, ni poteau, ni ligne d'horizon marquée. Le ciel est un aplat gris clair uniforme, couvert.

CAMÉRA. Objectif 85 mm, f/1.8, ISO 100, sur véhicule travelling parfaitement stabilisé, axe strictement horizontal à un mètre vingt du sol, aucune rotation, aucun zoom, aucun tremblement. Mise au point fixe sur le flanc de la voiture, très faible profondeur de champ. Obturateur 1/1000 s : la voiture est parfaitement nette sur chaque image, sans le moindre flou de bougé.

LUMIÈRE. Ciel couvert, lumière douce et diffuse, aucun soleil direct, aucune ombre dure, aucun reflet ponctuel qui se déplace. 5500 K. Exposition et balance des blancs verrouillées : aucune variation de luminosité pendant tout le plan.

RENDU. Prise de vue réelle, film publicitaire automobile, qualité commerciale. Colorimétrie neutre, contraste doux. Grain très fin. 24 images par seconde, 8 secondes, format 16:9 horizontal, résolution maximale.

INTERDIT. Coupe, fondu, mouvement de caméra, zoom, tremblement, dérive de la voiture dans le cadre, changement de taille ou de proportions du véhicule, flou de bougé sur la carrosserie, arrière-plan net ou détaillé, arbre ou bâtiment identifiable, marquage au sol, panneau routier, autre véhicule, accélération, freinage, virage, tangage, suspension qui travaille, variation d'exposition, effet de vitesse, traînée lumineuse, personne, main, texte, chiffre, logo, marque, plaque, fumée, poussière, gerbe d'eau, étincelle, particules, rendu 3D, image de synthèse, aspect jeu vidéo.
```

**Pourquoi l'arrière-plan doit être flou et vide.** S'il n'y a aucun détail
fin dans le fond, il n'y a rien qui puisse frémir. C'est la parade, et elle
est aussi la plus jolie : un fond réduit à un dégradé, c'est du 85 mm à
pleine ouverture, le langage exact du film publicitaire automobile. La
contrainte technique et le parti pris esthétique tombent au même endroit.

---

# Juger la chorégraphie

Avant de m'envoyer quoi que ce soit, regardez chaque plan **deux fois** :

1. **En lecture normale.** Ce qui vous gêne ici sera pire au défilement : la
   scrutation d'une image fixe est bien plus sévère que la lecture à 24 i/s.
2. **Image par image, à la flèche, sur les rayons d'une jante.** C'est le
   détecteur le plus fiable — fins, répétitifs, contrastés, c'est là que
   l'incohérence apparaît en premier.

Les quatre échecs, et ce qu'on en fait :

- **Le frémissement.** Les détails fins vibrent d'une image à l'autre sans que
  rien ne bouge. Le modèle ré-invente le détail à chaque image. Irrécupérable,
  à refaire.
- **La silhouette qui respire.** La voiture change discrètement de longueur ou
  de hauteur. Le plus grave, et invisible en lecture normale — d'où l'image
  par image. À refaire en insistant sur « proportions rigoureusement
  constantes ».
- **Le reflet qui rampe.** Les reflets glissent sans rapport avec le
  mouvement. Souvent réparable en simplifiant la lumière décrite : une seule
  rampe au lieu de deux.
- **La jointure qui saute.** Deux plans consécutifs ne raccordent pas. Ça veut
  dire que l'image de départ n'a pas été jointe, ou pas respectée. Régénérez
  le second en la joignant.

Si un tour ne boucle pas parfaitement, ce n'est pas grave : dites-le moi, je
coupe avant le saut. Mieux vaut 140 images propres que 150 avec un raccord.

---

# Le montage

Les plans se donnent **dans l'ordre**, sur une seule ligne. Les images sont
réparties au prorata de la durée de chaque plan, donc la vitesse reste
constante d'un bout à l'autre de la chorégraphie :

```
python3 film_video.py tour.mp4 ouverture.mp4 eclate.mp4 entree.mp4 poste.mp4 depart.mp4 240 1440 large
python3 build_film.py 72 1280
```

240 images pour six plans, soit 40 par beat, soit environ 11 Mo livrés.
`film_video.py` annonce le poids estimé à la fin : si le chiffre dépasse, il
suffit de redemander moins d'images.

Le portrait est une **composition à refaire**, pas un recadrage : passer du
16:9 au 9:16 en gardant le centre ne conserve que 32 % de la largeur, et la
voiture sort du cadre des deux côtés. Quand les plans verticaux existeront :

```
python3 film_video.py tour-v.mp4 ouverture-v.mp4 ... 150 900 etroit
python3 build_film.py 72 1280
```

Pour le vertical, gardez les mêmes prompts en remplaçant le paragraphe de
cadrage : la voiture occupe environ 85 % de la largeur, centrée en hauteur,
avec un large espace vide au-dessus. Cet espace n'est pas une faute de
cadrage — c'est là que le texte du site vient se poser.

---

# La limite qu'il faut dire au client

Cette voiture est **générée**. Elle n'a ni marque, ni plaque, ni badge, et
c'est délibéré : c'est une démonstration de mise en scène, pas l'annonce d'un
véhicule réel.

Pour un vrai loueur, la règle du dossier tient toujours — le décor, les
matières et l'ambiance peuvent être générés, **jamais le véhicule loué**.
Montrer une Clio générée à la place de celle qu'on loue est une publicité
trompeuse, en plus du problème d'image de marque. Le jour où le client signe,
on filme sa voiture : un plateau tournant, huit secondes par beat, et le même
pipeline tourne sans changer une ligne.

L'éclaté, lui, reste générable dans tous les cas : personne ne loue une
voiture en pièces détachées, donc personne ne peut être trompé.
