# La continuité — cinq mondes, un seul mouvement

Le prologue du site n'est pas une suite d'exemples. C'est **un seul travelling
avant qui ne s'arrête jamais** et qui traverse cinq métiers : une villa, une
piscine, une voiture, un restaurant, et le plat qu'on y sert.

> **Le terrain de foot n'a pas été tourné.** Son prompt reste écrit plus bas
> pour le jour où on le voudra. La suite prend une autre direction : au lieu de
> quitter le restaurant pour un stade, on y entre — la cuisine, puis le burger
> qui se démonte. C'est plus juste, d'ailleurs : on finit sur le PRODUIT d'un
> des métiers, pas sur un sixième décor.

C'est ça, la démonstration. Pas « voici cinq sites », mais « voici cinq
commerces sur le même rail, et vous ne voyez pas la jointure ».

Deux fois, pourtant, il faut changer de monde pour de bon : le restaurant et
le stade ne sont pas chez la villa. Ces deux sauts ne se cachent pas, ils se
mettent en scène — voir **[Les passages](#les-passages)**.

---

## La 4K native, et la fin de l'agrandissement

La première série est sortie en 720p, puis a été agrandie en 4K par un outil
tiers. C'était une erreur, et elle se mesure : à taille égale, une image du
site de référence porte une variance de laplacien de 65, les nôtres de 13.
Cinq fois moins de détail. Un agrandisseur ne restitue rien — il fabrique un
détail plausible, et sur du feuillage ou de la pierre cela donne cet aspect
lisse et cireux qu'aucun réglage de livraison ne rattrape.

Veo sort en 4K native. Le réglage suffit, et il supprime tout un maillon de la
chaîne : plus d'agrandisseur, donc plus de détail inventé, plus de décalage de
cadence à corriger, plus d'outro à découper.

UN SEUL FORMAT, 16:9. Les six prompts l'ont toujours demandé ; si la première
série est sortie moitié en vertical, c'est que le format de sortie de Flow
était réglé sur portrait. En 16:9 et en 4K, la version téléphone se fabrique
par recadrage centré et fait encore 1215x2160 — le double de ce qu'affiche la
toile d'un téléphone. Il n'y a donc plus deux séries à générer, mais une
seule, à condition de composer pour les deux : d'où la consigne CADRE ajoutée
à chaque plan, qui réserve le tiers central au sujet.


## Les deux partis pris

### Personne à l'écran

Un modèle vidéo ne tient pas un visage d'une image à l'autre : il le
ré-invente, et au défilement — où l'on regarde chaque image fixe — ça se voit
immédiatement. Donc aucune personne, nulle part.

Plutôt que de subir cette contrainte, on l'assume : **tout est prêt, personne
n'est encore arrivé.** Les tables sont dressées, l'eau est lisse, le terrain
est tracé, les phares sont allumés. C'est une heure réelle, celle d'avant
l'ouverture, et elle est plus belle que la pleine affluence.

### Le jour tombe

La lumière progresse d'un plan au suivant : fin d'après-midi dans la villa,
soleil rasant sur la piscine, crépuscule sur la voiture, tombée de nuit au
restaurant, projecteurs sur le terrain. **À l'intérieur d'un plan, elle ne
bouge pas** — exposition verrouillée — mais d'un plan à l'autre elle avance.

Le visiteur qui descend voit le jour tomber. Celui qui remonte le voit se
lever. Les deux fonctionnent : c'est réversible, aucune entropie.

---

## Les trois lois, rappelées

Elles ne viennent pas du goût, mais de la façon dont le défilement consomme
les images.

| Loi | Pourquoi |
|---|---|
| **Réversible, pas immobile** | Le visiteur remonte. Une porte s'ouvre et se referme ; une fumée qui se dissipe, non. Interdits : fumée, vapeur, éclaboussure, poussière, particules. |
| **Aucun flou de mouvement** | Une image extraite est regardée *fixe*. Le flou invisible à 24 i/s devient une traînée sale figée. Obturateur 1/1000 s partout. |
| **Vitesse rigoureusement constante** | Le visiteur impose sa vitesse. Toute accélération filmée s'ajoute à la sienne et se lit comme un à-coup. |

---

## Le chaînage

Un plan généré fait 8 secondes ; la continuité en fait quarante. On les
enchaîne, et la technique tient en une phrase :

> **La dernière image d'un plan devient l'image de départ du suivant.**

Les modèles acceptent une image d'amorce. On leur donne la fin du plan
précédent, et le nouveau reprend exactement là. Sans ça, chaque plan repart
d'un décor *presque* identique et la jointure saute aux yeux.

```
1. générer le plan 1
2. python3 film_raccord.py plan1.mp4        → plan1-fin.png
3. joindre plan1-fin.png au prompt du plan 2, générer
4. python3 film_raccord.py plan2.mp4        → plan2-fin.png
5. ... et ainsi de suite jusqu'au plan 5
```

Chaque prompt ci-dessous commence par une ligne de raccord, **à garder telle
quelle sauf pour le plan 1**.

---

## Les passages

Les trois premiers plans forment un lieu réel : une villa, sa piscine, sa cour,
sa voiture. Le restaurant et le terrain, eux, n'y sont pas — et les y coller
bord à bord ne tiendrait pas debout. Une terrasse de restaurant qui jouxte la
cour d'une villa privée, puis un stade éclairé derrière le restaurant : le
visiteur ne le croira pas une seconde.

Plutôt que de mentir sur la géographie, on **assume le saut et on lui donne une
forme**. C'est le vieux truc du plan-séquence, celui de *1917* et de
*Birdman* : la caméra frôle une masse opaque — un tronc, un pilier, une haie —
qui remplit le cadre pendant une demi-seconde, et de l'autre côté on est
ailleurs.

Pourquoi ça marche particulièrement bien ici :

- **Rien ne peut trembler.** Une masse sombre et unie n'a pas de détail fin à
  ré-inventer. C'est même la seule chose qu'un modèle vidéo ne peut pas rater.
- **C'est réversible.** Remonté, le passage se lit exactement pareil.
- **Ça reste un travelling avant.** Aucune montée, aucune descente, aucune
  rotation : la hauteur constante qui tient toute la séquence n'est pas
  touchée.
- **Ça libère la géographie.** Le passage dit au visiteur « on change de
  monde ». Il n'a plus besoin que les lieux soient voisins, et c'est
  exactement ce qu'on veut démontrer.

### Où le placer : au DÉBUT du plan qui reçoit, jamais à la fin de celui qui donne

Contre-intuitif, et c'est le point technique qui décide de tout. Le chaînage
repose sur la dernière image d'un plan : si elle est noire, elle ne transmet
rien, et le plan suivant repart de zéro.

Le passage vit donc dans la **première seconde du plan d'arrivée** : il part du
raccord — une image pleine et lisible —, traverse la masse sombre, et débouche
sur le nouveau monde. Sa dernière image, elle, est de nouveau une vraie image
de décor, prête pour le raccord suivant.

### Ce qu'il ne faut pas faire

**Pas d'aigle, pas d'oiseau, pas d'animal.** Des ailes qui battent sont du
mouvement articulé rapide : à 1/1000 s chaque image fige une position
différente, et au défilement ça ne fait pas un vol, ça fait un stroboscope. Un
modèle qui redessine une silhouette d'oiseau d'une image à l'autre produit
exactement le frémissement qu'on passe le reste du document à éviter.

**Pas de montée ni de plongée.** Un envol impose une trajectoire verticale, et
la hauteur constante est ce qui rend la séquence lisible d'un bout à l'autre.

---

## Sur Google Flow

Flow tourne sur **Gemini Omni**, décrit par Google comme capable de « créer et
éditer des vidéos à partir de n'importe quelle référence, réelle ou générée ».
Une vidéo de référence y est donc un usage prévu. Ce qui change, et ce qui ne
change pas :

### Ce qui ne change pas

Les trois lois, les deux partis pris, les passages, et les prompts eux-mêmes.
Ils ne décrivent pas un outil, ils décrivent ce que le défilement peut
consommer — un flou de bougé reste une traînée figée quel que soit le modèle
qui l'a produit.

### Une vidéo de référence vaut mieux que trois photos

Pour la Golf, filmez-la. Dix secondes suffisent. Une vidéo donne au modèle la
voiture sous une infinité d'angles intermédiaires, avec un éclairage cohérent
et de vrais reflets qui glissent — trois photos ne donnent que trois instants
sans lien entre eux, et c'est au modèle d'inventer ce qu'il y a entre.

**Le piège de la vidéo de référence : le mouvement de caméra déteint.** Si vous
filmez en tournant autour de la voiture, le modèle a de bonnes chances de
reproduire cette orbite au lieu de notre travelling latéral verrouillé. Deux
précautions :

1. **Filmez la voiture depuis un point fixe**, ou en marchant le long du flanc
   — c'est-à-dire déjà le mouvement qu'on veut.
2. **Dites-le dans le prompt** : la référence donne le véhicule, pas la caméra.
   La ligne est déjà prévue dans le plan 3, il suffit de remplacer
   « photographies » par « vidéo ».

### Le raccord d'un plan à l'autre

Si Flow propose de prolonger un plan existant plutôt que de repartir d'une
image — cherchez une commande de continuation ou d'extension —, **prenez-la**.
Elle reprend l'état réel du plan, mouvement compris, là où une image fixe ne
transmet qu'un instant. Le passage de `film_raccord.py` devient alors inutile,
et les jointures cessent d'être un risque.

Attention cependant : une continuation a tendance à **prolonger l'action en
cours**. Or nos plans changent délibérément de programme à chaque fois. C'est
précisément ce que les passages résolvent : frôler un cyprès donne à la
continuation une raison motivée de changer de monde.

Si la continuation n'existe pas ou ne convainc pas, la méthode d'image de
raccord reste valable telle quelle.

### Les en-têtes, selon votre mode

Les plans 4 et 5 ci-dessous sont écrits pour la **prolongation** : Flow tient
déjà le plan précédent, il n'y a plus d'image à joindre. Leur premier
paragraphe s'appelle `CONTINUITÉ`.

Si vous repartez d'une image de raccord au lieu de prolonger, remplacez ce
paragraphe par la ligne habituelle :

```
L'image jointe est la première image de ce plan. Reprends exactement le même lieu, la même lumière, la même hauteur de caméra, et poursuis le mouvement sans le moindre à-coup.
```

Et si vous joignez un plan déjà généré comme **référence de registre** — pour
que l'étalonnage et le grain restent les mêmes d'un bout à l'autre — ajoutez ce
paragraphe juste après `CONTINUITÉ`, et **seulement dans ce cas** :

```
RÉFÉRENCE DE REGISTRE. La vidéo jointe est un plan antérieur de la même séquence. Elle ne donne ni le décor, ni le sujet, ni le mouvement de caméra : uniquement le rendu — étalonnage, contraste, densité des noirs, grain, netteté, comportement de l'objectif. Le décor et l'action de ce plan-ci sont ceux décrits ci-dessous, et eux seuls.
```

Sans cette précision, un modèle à qui l'on donne une vidéo de voiture pour un
plan de restaurant essaiera d'y remettre la voiture.

### Deux détails à ne pas rater

**L'audio.** Veo 3.1 génère du son nativement. On n'en a aucun usage — le
prologue est une suite d'images muettes — et `film_video.py` l'ignore. S'il
existe une option pour ne pas en produire, elle fait gagner du temps.

**Le format portrait.** Flow propose un outil de redimensionnement vers
n'importe quel rapport. Ça mérite d'être essayé pour la série `etroit` : un
recadrage intelligent vaut mieux qu'un rognage centré, qui ne garde que 32 %
de la largeur et fait sortir le sujet du cadre. Sans garantie — une
composition pensée en 16:9 reste une composition pensée en 16:9.

---

## Le budget

**51 Ko l'image dans la page finale**, mesuré sur la construction : 160 images
donnent 6,0 Mo de WebP, qui font une page de 8,34 Mo une fois passées en
base64. C'est ce chiffre-là qui compte, pas le poids du WebP seul.

| images | page |
|---|---|
| 200 | ~10,4 Mo |
| 220 | ~11,4 Mo |
| 240 | ~12,4 Mo |

Au-delà de 15,5 Mo la page ne tient plus dans un fichier unique et il faut
servir les images depuis le disque — ce que le lecteur sait faire, mais qui
n'est plus une démonstration autonome.

**Le budget porte sur le nombre total d'images, pas sur le nombre de plans.**
Cinq plans de 44 images et six plans de 37 coûtent exactement la même chose.
Ajouter un beat ne coûte donc rien en poids : seulement une génération de plus
et une jointure de plus à réussir.

---

# Plan 1 — La villa

```
Un seul plan continu de huit secondes, sans aucune coupe, qui avance dans le séjour d'une villa contemporaine vers une grande baie vitrée ouverte.

MOUVEMENT. La caméra avance en ligne droite, à vitesse rigoureusement constante du début à la fin, sans jamais s'interrompre, sans accélérer ni ralentir. Elle part du fond du séjour et progresse vers la baie vitrée grande ouverte, qu'elle atteint sans la franchir : à la dernière image, l'ouverture occupe presque tout le cadre et l'on découvre au-delà une terrasse et le bord d'une piscine. Aucune rotation, aucun panoramique, aucun zoom, aucun tremblement, aucun mouvement latéral. Rien ne bouge dans la scène : ni rideau, ni feuillage, ni eau.

SUJET. Séjour d'une villa contemporaine, vaste et sobre. Sol en pierre claire à grands carreaux, murs blanc cassé, plafond haut. Un canapé d'angle en lin sable, une table basse en travertin, un grand tapis en laine écrue. Une bibliothèque basse en chêne clair contre le mur de gauche. Un olivier en pot de terre cuite. Baie vitrée à cadre noir fin, grande ouverte, donnant sur une terrasse en pierre. AUCUNE PERSONNE, aucune silhouette, aucun animal. Aucun objet de marque, aucun écran allumé, aucun texte lisible nulle part.

CAMÉRA. Objectif 24 mm, f/5.6, ISO 100, sur rail motorisé parfaitement stabilisé, axe strictement horizontal à un mètre soixante du sol, verticales parfaitement redressées. Nette de bout en bout. Obturateur très rapide, 1/1000 s : chaque image doit être parfaitement nette, sans le moindre flou de bougé.

LUMIÈRE. Fin d'après-midi. Lumière naturelle chaude entrant par la baie, en biais, posant de longs rectangles lumineux sur le sol en pierre. Aucune lampe allumée. Ombres douces et longues. Exposition et balance des blancs VERROUILLÉES du début à la fin : aucune variation de luminosité, de contraste ou de teinte, y compris quand la baie très claire remplit le cadre.

CADRE. Le sujet essentiel reste dans le TIERS CENTRAL de l'image, en largeur. Le site montre ce plan en entier sur ordinateur, mais sur téléphone il n'en garde qu'une bande verticale centrale : tout ce qui compte doit y tenir. Les bords gauche et droit ne portent que du décor, jamais le sujet.

RENDU. Prise de vue réelle, film d'architecture, qualité commerciale. Colorimétrie neutre et fidèle, contraste doux, hautes lumières de la baie légèrement soutenues comme sur une vraie photographie. Grain photographique très fin. 30 images par seconde, 8 secondes, format 16:9 horizontal, résolution 3840x2160, 4K NATIVE (réglage de sortie au maximum, aucun agrandissement ultérieur), débit élevé, aucune compression agressive.

INTERDIT. Coupe, changement de plan, fondu, transition, saut, rotation de caméra, panoramique, zoom, tremblement, accélération, ralentissement, flou de mouvement, flou de bougé, variation d'exposition, personne, silhouette, main, animal, reflet d'équipe, texte, chiffre, logo, marque, enseigne, filigrane, signature, rideau qui bouge, feuillage agité, fumée, vapeur, poussière, particules, rendu 3D, image de synthèse, aspect jeu vidéo, couleurs saturées, HDR excessif.
```

---

# Plan 2 — La piscine

```
L'image jointe est la première image de ce plan. Reprends exactement la même villa, la même lumière, la même hauteur de caméra, et poursuis le mouvement sans le moindre à-coup.

Un seul plan continu de huit secondes, sans aucune coupe, qui franchit la baie vitrée et glisse au-dessus d'une piscine.

MOUVEMENT. La caméra poursuit son avance en ligne droite, à la même vitesse rigoureusement constante que le plan précédent : elle franchit l'ouverture, traverse la terrasse en pierre, et continue au-dessus de la piscine en gardant exactement la même hauteur. À la dernière image elle est parvenue au bord opposé du bassin, et l'on découvre au-delà une cour en gravier clair. Aucune rotation, aucune plongée, aucun zoom, aucun tremblement. La surface de l'eau est parfaitement lisse et immobile, comme un miroir : aucune vague, aucune ride, aucun clapot.

SUJET. Terrasse en pierre claire prolongeant la villa, puis une piscine à débordement rectangulaire, eau turquoise très calme, margelles en pierre. Deux transats en teck et toile écrue, alignés, vides. Un parasol fermé. Massifs de lavande et d'oliviers taillés en bordure. Au fond, une cour en gravier clair fermée par une murette basse, avec deux jardinières en pierre plantées de cyprès étroits, et au-delà une oliveraie. AUCUNE PERSONNE, aucune silhouette, aucun animal, aucun objet flottant. Aucune marque, aucun texte lisible.

CAMÉRA. Objectif 24 mm, f/5.6, ISO 100, sur rail motorisé stabilisé, axe strictement horizontal à un mètre soixante du sol, verticales redressées. Nette de bout en bout. Obturateur 1/1000 s, chaque image parfaitement nette, y compris les reflets sur l'eau.

LUMIÈRE. Soleil rasant de fin de journée, venant de la droite, dorant la pierre et allumant un long reflet étiré sur l'eau immobile. Aucune lampe allumée. Exposition et balance des blancs VERROUILLÉES : aucune variation entre l'intérieur sombre et l'extérieur lumineux au moment du franchissement — l'image ne doit ni s'éclaircir ni s'assombrir en sortant.

CADRE. Le sujet essentiel reste dans le TIERS CENTRAL de l'image, en largeur. Le site montre ce plan en entier sur ordinateur, mais sur téléphone il n'en garde qu'une bande verticale centrale : tout ce qui compte doit y tenir. Les bords gauche et droit ne portent que du décor, jamais le sujet.

RENDU. Prise de vue réelle, film d'architecture, qualité commerciale. Colorimétrie neutre et fidèle, contraste doux, grain très fin. 30 images par seconde, 8 secondes, format 16:9 horizontal, résolution 3840x2160, 4K NATIVE (réglage de sortie au maximum, aucun agrandissement ultérieur), débit élevé.

INTERDIT. Coupe, fondu, transition, rotation de caméra, plongée, zoom, tremblement, changement de vitesse, flou de mouvement, variation d'exposition au passage de la baie, vague, ride, clapot, remous, éclaboussure, reflet qui rampe, personne, silhouette, animal, oiseau, texte, chiffre, logo, marque, filigrane, feuillage agité par le vent, fumée, vapeur, particules, rendu 3D, image de synthèse.
```

---
# Plan 3 — La voiture

**La voiture doit être déjà là, et il faut le dire.**

C'est le piège de ce plan, et il ne vient pas de la formulation. L'image de
raccord montre une cour vide : demander à la caméra d'« atteindre une voiture »
revient à demander au modèle de faire apparaître un objet absent, alors qu'on
lui interdit par ailleurs toute apparition. Il ne peut que patiner.

La formulation qui marche : **la voiture est garée dans la cour depuis le
début, hors du champ initial ou trop loin pour se distinguer, et c'est la
caméra qui s'en approche.** Rien n'apparaît, on avance.

**Décrivez ce que l'image contient vraiment.** Le modèle a le raccord sous les
yeux, mais le nommer verrouille ce qu'il doit conserver. Une cour en gravier
avec deux jardinières en pierre n'est pas une allée bordée de cyprès, et
l'écart suffit à lui faire redessiner le décor.

**Ce plan prend deux sortes d'images jointes, et il faut le lui dire.**

Le raccord (la dernière image du plan 2) donne le *lieu et la lumière*. Les
photos de la Golf donnent le *véhicule*. Un modèle qui reçoit trois images
sans consigne les mélange : il peut prendre la Golf comme décor de départ, ou
repeindre la villa en rouge. La première ligne du prompt sépare les rôles.

**Quelles photos joindre.** Trois suffisent, et leur cadrage compte plus que
leur nombre :

1. **le profil strict**, voiture entière, c'est le plan qu'on va filmer ;
2. **le trois-quarts avant**, qui donne la calandre, le bandeau lumineux et
   le liseré rouge ;
3. **un détail de flanc** — jante, bas de caisse, poignée — pour la matière.

**Extérieur seulement — pas de photo d'habitacle.** La caméra reste dehors et
les vitres sont teintées : l'intérieur n'apparaît à aucun moment. Une
référence que le modèle ne peut satisfaire nulle part, il essaie quand même de
la placer — il détient les vitres, ou il fait dériver la caméra vers
l'habitacle en plein milieu du travelling, ce qui casse la continuité.

Prises par temps couvert si possible : une photo en plein soleil impose ses
ombres au plan, et elles ne coïncideront pas avec la lumière du raccord.

**Le raccord se prend avec `film_raccord.py`, pas en capture d'écran.** Une
capture est rognée par l'interface et rééchantillonnée ; le script lit la
dernière image lisible du fichier, à sa définition d'origine. Sur un raccord,
cet écart de définition se voit.

**Ce qui doit être absent se décrit dans `SUJET`, pas dans `INTERDIT`.** Leçon
payée deux fois : le badge d'abord, la plaque ensuite. Une négation en fin de
liste pèse peu ; la même consigne formulée positivement dans la description du
sujet — « les emplacements de plaque sont lisses, vides et unis » — tient
beaucoup mieux. Un modèle rend ce qu'on lui décrit, il n'efface pas ce qu'on
lui refuse.

**Ne décrivez pas la voiture en détail dans le prompt.** C'est le réflexe
naturel et c'est l'erreur : un paragraphe de description entre en concurrence
avec les photos, et le modèle arbitre au hasard. Le prompt nomme le modèle,
pose deux ou trois repères vérifiables, et laisse les images faire le reste.

```
IMAGES JOINTES — deux rôles distincts, à ne pas confondre.

La première image jointe est L'IMAGE DE DÉPART de ce plan : elle donne le lieu, le cadrage, la hauteur de caméra et la lumière. Le plan commence exactement sur elle et poursuit le mouvement sans le moindre à-coup.

Les autres références jointes — photographies ou vidéo — sont des RÉFÉRENCES DU VÉHICULE. Elles ne sont pas le décor et ne donnent ni le cadrage, ni le mouvement de caméra, ni la lumière : elles servent uniquement à reproduire fidèlement cette voiture précise — sa forme, ses proportions, sa couleur, ses jantes, ses optiques, ses détails. Reproduis-la exactement telle qu'elle apparaît sur ces photos, sans rien inventer ni styliser.

Un seul plan continu de huit secondes, sans aucune coupe, qui quitte la piscine et longe une voiture garée sur l'allée.

MOUVEMENT. La caméra poursuit son avance en ligne droite, à la même vitesse rigoureusement constante que le plan précédent, sur le même axe et à la même hauteur : elle quitte le bord du bassin, franchit la terrasse dallée, et traverse la cour en gravier. Une voiture y est garée de profil DEPUIS LE DÉBUT, sur la droite de la cour : elle est déjà en place à la première image, simplement lointaine et partiellement masquée par la jardinière en pierre. Rien n'apparaît, rien ne surgit, rien n'entre dans le champ : c'est la caméra qui s'approche, et la voiture qui grandit dans le cadre à mesure. La caméra la rejoint, la longe du capot jusqu'à l'arrière, et la dépasse. À la dernière image, la voiture est derrière nous et la caméra fait face au mur de pierre sèche d'un mas, qui ferme la cour et se rapproche de l'objectif. Aucune rotation, aucun zoom, aucun tremblement. La voiture est absolument immobile : roues droites, portières fermées, aucune roue qui tourne, aucune suspension qui travaille.

SUJET. Une Volkswagen Golf 8 GTI rouge, exactement celle des photographies de référence jointes. Compacte cinq portes. Ses proportions, sa teinte rouge, le dessin de ses jantes, la forme de ses optiques et tous ses détails doivent correspondre aux photographies — c'est le même véhicule, vu sous un autre angle et dans une autre lumière, pas une interprétation. Trois repères à vérifier : le bandeau lumineux horizontal qui traverse la calandre d'un phare à l'autre, le liseré rouge qui la souligne sur toute sa largeur, et les étriers de frein rouges derrière les jantes. Carrosserie propre et polie, vitres teintées, phares allumés, blancs et constants. Portières fermées. Les emplacements de plaque d'immatriculation, devant comme derrière, sont LISSES, VIDES ET UNIS : pas de plaque, pas de support, pas de cadre, aucun caractère, aucun chiffre, aucune lettre, aucun symbole. C'est un véhicule de présentation non immatriculé. Elle est garée de profil sur la droite d'une cour en gravier clair.

DÉCOR — celui de l'image de départ, à conserver strictement. Une terrasse dallée en pierre claire au premier plan, prolongée par une cour en gravier beige ratissé. Deux jardinières basses en pierre sèche encadrent la cour, chacune plantée d'un cyprès étroit. Massifs de lavande argentée sur les côtés. Une murette basse en pierre ferme la cour au fond, et au-delà s'étend une oliveraie aux troncs noueux et aux feuillages gris-vert, puis des collines boisées à l'horizon. Aucun autre bâtiment, aucun mobilier, aucune clôture qui n'y soit déjà. AUCUNE PERSONNE.

CAMÉRA. Objectif 35 mm, f/5.6, ISO 100, sur rail motorisé stabilisé, axe strictement horizontal à un mètre soixante du sol, verticales redressées. La voiture reste entièrement visible dans le cadre pendant tout le passage, avec une marge d'air nette au-dessus et en dessous. Nette de bout en bout. Obturateur 1/1000 s : carrosserie parfaitement nette sur chaque image, sans le moindre flou de bougé.

LUMIÈRE. Exactement celle de l'image de départ, sans la modifier, et non celle des photographies de référence : fin de journée, soleil bas et chaud, longues ombres portées en travers de la pierre et du gravier, feuillages dorés. Même direction de lumière, mêmes ombres, même température. Sur la carrosserie, cette lumière rasante court le long du flanc en un long reflet étiré. Le rouge reste franc et lisible, ni orangé par le couchant ni assombri. Aucune ombre dure, aucun reflet ponctuel qui saute. Exposition et balance des blancs VERROUILLÉES du début à la fin.

CADRE. Le sujet essentiel reste dans le TIERS CENTRAL de l'image, en largeur. Le site montre ce plan en entier sur ordinateur, mais sur téléphone il n'en garde qu'une bande verticale centrale : tout ce qui compte doit y tenir. Les bords gauche et droit ne portent que du décor, jamais le sujet.

RENDU. Prise de vue réelle, film publicitaire automobile, qualité commerciale. Colorimétrie neutre, contraste doux, noirs profonds mais lisibles. Grain très fin. 30 images par seconde, 8 secondes, format 16:9 horizontal, résolution 3840x2160, 4K NATIVE (réglage de sortie au maximum, aucun agrandissement ultérieur), débit élevé, netteté jusque dans les textures fines : rayons de jantes, nid d'abeille de la calandre, grain du gravier.

INTERDIT. Coupe, fondu, transition, rotation de caméra, zoom, tremblement, changement de vitesse, flou de mouvement, flou de bougé, voiture qui apparaît, surgit ou entre dans le champ, voiture qui roule ou se gare, décor redessiné ou différent de l'image de départ, cyprès ou jardinières déplacés, véhicule différent de celui des photographies, proportions modifiées, teinte modifiée, jantes inventées, carrosserie trois portes, break, berline, plaque d'immatriculation, roue qui tourne, portière qui s'ouvre, suspension qui travaille, variation d'exposition, personne, silhouette, animal, texte, chiffre, enseigne, filigrane, fumée, poussière soulevée, gerbe, particules, rendu 3D, image de synthèse, aspect jeu vidéo.
```

**Si votre outil n'accepte qu'une seule image jointe** — c'est le cas de
plusieurs interfaces — il faut choisir, et le bon choix n'est pas évident :

- **garder le raccord** préserve la continuité, mais la Golf ne sera qu'une
  approximation décrite en mots ;
- **garder la photo de la Golf** donne la bonne voiture, mais le plan 3 ne
  raccorde plus au plan 2 et la jointure sautera.

Prenez le raccord. Une jointure qui saute se voit à chaque descente ; une
jante approximative, presque jamais. Et si la voiture doit absolument être
exacte, la solution propre est de la **filmer** : huit secondes de travelling
le long du flanc, et le même pipeline tourne sans changer une ligne.

# Plan 4 — Le restaurant

Le premier passage. La caméra longe le mur de pierre du mas, il remplit le
cadre une demi-seconde, et de l'autre côté c'est le restaurant.

*Écrit pour la prolongation. Si vous repartez d'une image de raccord, voir
[Les en-têtes, selon votre mode](#les-en-têtes-selon-votre-mode).*

> **Adapté au raccord réel.** Le plan 3 devait finir sur un cyprès proche : il
> a fini sur une cour ensoleillée face à un mas en pierre, avec la Golf sortant
> du champ à gauche. Deux conséquences. La masse du passage devient le **mur du
> mas**, qui est là et qui est bien meilleur — une façade en pierre est large,
> mate et uniforme, exactement ce qu'il faut. Et la lumière de départ est celle
> du plein jour, pas d'un crépuscule : le déclin se fait donc **entièrement
> pendant le passage**, ce qui est le seul moment où l'exposition a le droit de
> bouger.

```
CONTINUITÉ. Ce plan prolonge le plan précédent sans aucune coupe et sans aucun raccord visible : même lieu, même hauteur de caméra, même axe, même vitesse. Reprends le mouvement exactement là où il s'arrête, sans à-coup, sans repartir, sans réinitialiser le cadrage, sans revenir en arrière.

Un seul plan continu de huit secondes, sans aucune coupe, qui longe le mur d'un mas en pierre et débouche sur une terrasse de restaurant dressée.

MOUVEMENT. Le plan se déroule en trois temps enchaînés, à vitesse rigoureusement constante du début à la fin, sans jamais s'arrêter ni ralentir.

Premier temps, environ deux secondes : la caméra poursuit son avance en ligne droite à travers la cour de gravier, vers le mas en pierre. Elle s'approche de son mur et le longe de très près, à quelques centimètres de l'objectif. La pierre chaude occupe progressivement le cadre par la gauche.

Deuxième temps, environ une demi-seconde : le mur occupe TOUT le cadre. L'image est entièrement remplie par cette pierre sèche beige, mate, dont on voit le grain et les joints, sans détail net, sans ciel, sans trouée. Elle n'est pas noire : elle est claire, chaude et texturée.

Troisième temps, le reste du plan : le mur se dégage par la droite et découvre une terrasse de restaurant couverte, où la caméra pénètre et qu'elle traverse en glissant dans l'allée centrale, entre deux rangées de tables dressées. À la dernière image elle atteint le fond de la salle, où se dresse tout près de l'objectif un large pilier de pierre sombre, sur la gauche du cadre.

Aucune rotation, aucun panoramique, aucun zoom, aucun tremblement, aucun changement de hauteur. Le passage le long du mur n'est ni un fondu, ni une coupe, ni une transition ajoutée : c'est un mur réel que la caméra longe. Rien d'autre ne bouge : ni nappe, ni bougie, ni feuillage, ni store.

SUJET. Terrasse de restaurant couverte, charpente en bois clair, sol en tomettes. Deux rangées de tables carrées en chêne massif, entièrement dressées et parfaitement alignées : nappes en lin écru, assiettes en grès mat, verres à pied, couverts alignés, une petite bougie éteinte au centre de chaque table. Chaises en bois cintré et cannage. Guirlande d'ampoules à filament allumées le long de la charpente, lumière chaude et constante. Un bar en zinc sur la gauche, bouteilles alignées sans étiquette lisible. AUCUNE PERSONNE, aucune silhouette, aucun serveur, aucune main. Aucune enseigne, aucun menu lisible, aucune marque, aucun texte, aucune ardoise, aucun chiffre.

CAMÉRA. Objectif 24 mm, f/4, ISO 200, sur rail motorisé stabilisé, axe strictement horizontal, verticales parfaitement redressées. Nette de bout en bout, y compris le grain de la pierre au moment où elle frôle l'objectif. Obturateur 1/1000 s, chaque image parfaitement nette.

LUMIÈRE. Le jour tombe PENDANT le passage le long du mur, et à aucun autre moment. Avant le mur : plein jour lumineux, ciel bleu franc, pierre chaude, exactement la lumière du plan précédent, inchangée. Après le mur : la nuit est tombée, le ciel est bleu profond au-delà de la terrasse, et la guirlande d'ampoules chaudes éclaire l'intérieur, déjà allumée et rigoureusement constante. Une fois la terrasse atteinte, l'exposition et la balance des blancs sont VERROUILLÉES et ne bougent plus. Aucune flamme, aucune bougie allumée, aucune source qui vacille.

CADRE. Le sujet essentiel reste dans le TIERS CENTRAL de l'image, en largeur. Le site montre ce plan en entier sur ordinateur, mais sur téléphone il n'en garde qu'une bande verticale centrale : tout ce qui compte doit y tenir. Les bords gauche et droit ne portent que du décor, jamais le sujet.

RENDU. Prise de vue réelle, film de restaurant haut de gamme, qualité commerciale. Colorimétrie chaude mais fidèle, contraste doux, hautes lumières des ampoules contrôlées. Grain très fin. 30 images par seconde, 8 secondes, format 16:9 horizontal, résolution 3840x2160, 4K NATIVE (réglage de sortie au maximum, aucun agrandissement ultérieur), débit élevé.

INTERDIT. Coupe, fondu au noir, fondu enchaîné, transition ajoutée, effet de volet, rotation de caméra, panoramique, zoom, changement de hauteur, tremblement, changement de vitesse, arrêt, flou de mouvement, retour dans la cour, voiture visible ou ramenée dans le champ, mur qui s'écarte tout seul, image entièrement noire, variation de lumière avant ou après le mur, personne, silhouette, serveur, main, animal, oiseau, flamme, bougie allumée, ampoule qui vacille, nappe qui bouge, store agité, texte, menu, chiffre, prix, enseigne, logo, marque, étiquette lisible, plaque d'immatriculation, filigrane, fumée, vapeur de plat, particules, rendu 3D, image de synthèse.
```

---

# Annexe — Le terrain de foot, non tourné

Écrit avant que la suite ne prenne une autre direction, et gardé tel quel : le
dispositif y est valable, seul le décor change. Le pilier de pierre du fond de
salle remplit le cadre, et de l'autre côté c'est le stade.

**Il ne s'enchaîne plus après le restaurant** — c'est la cuisine qui prend
cette place. Pour l'employer, il faudrait le mettre après le burger, ou refaire
le plan 4 pour qu'il finisse sur un pilier.

```
CONTINUITÉ. Ce plan prolonge le plan précédent sans aucune coupe et sans aucun raccord visible : même lieu, même hauteur de caméra, même axe, même vitesse, même lumière. Reprends le mouvement exactement là où il s'arrête, sans à-coup, sans repartir, sans réinitialiser le cadrage, sans revenir en arrière.

Un seul plan continu de huit secondes, sans aucune coupe, qui passe derrière un pilier de pierre et débouche sur un terrain de football éclairé.

MOUVEMENT. Le plan se déroule en trois temps enchaînés, à vitesse rigoureusement constante, sans jamais s'arrêter ni ralentir — sauf sur la toute dernière seconde, précisée plus bas.

Premier temps, environ une seconde et demie : la caméra poursuit son avance en ligne droite et frôle le large pilier de pierre sombre, à quelques centimètres de l'objectif. La pierre envahit progressivement le cadre par la gauche.

Deuxième temps, environ une demi-seconde : le pilier occupe TOUT le cadre. L'image est entièrement remplie par cette pierre sombre et mate, dont on voit le grain, sans détail net, sans trouée. Elle n'est pas noire, elle est gris-brun très sombre et texturée.

Troisième temps : le pilier se dégage par la droite et découvre un terrain de football éclairé, où la caméra glisse au-dessus de la pelouse en gardant exactement la même hauteur, jusqu'au rond central. Sur la dernière seconde elle ralentit régulièrement et s'immobilise. À la dernière image le cadre est calme et stable, centré sur le rond central, avec une large zone de pelouse unie et sans détail au centre de l'image.

Aucune rotation, aucun panoramique, aucun zoom, aucun changement de hauteur, aucun tremblement. Le passage derrière le pilier n'est ni un fondu, ni une coupe, ni une transition ajoutée : c'est un objet réel que la caméra longe.

SUJET. Un terrain de football en herbe, fraîchement tondu, avec ses bandes de tonte alternées bien nettes et son marquage blanc impeccable. Le rond central, le point de penalty, les lignes de touche. Un but avec ses filets blancs tendus au fond. Un ballon blanc posé, immobile, sur le point central. Gradins vides et sombres au-delà. AUCUNE PERSONNE, aucun joueur, aucune silhouette, aucun animal. Aucun panneau publicitaire, aucune enseigne, aucun logo, aucun texte, aucun maillot, aucun numéro.

CAMÉRA. Objectif 24 mm, f/4, ISO 400, sur rail motorisé stabilisé, axe strictement horizontal, verticales redressées. Nette de bout en bout, y compris le grain de la pierre au moment où elle frôle l'objectif. Obturateur 1/1000 s, chaque image parfaitement nette, y compris les brins d'herbe et les mailles du filet.

LUMIÈRE. La nuit tombe pendant le passage derrière le pilier et non avant : à l'entrée on est encore dans la lumière chaude du restaurant, à la sortie il fait nuit noire et quatre mâts de projecteurs éclairent le terrain d'une lumière blanche franche et rigoureusement constante, qui pose de larges nappes claires sur la pelouse et dessine les bandes de tonte. Ciel noir. Une fois le terrain atteint, l'exposition et la balance des blancs sont VERROUILLÉES et ne bougent plus. Aucun projecteur qui s'allume, s'éteint ou clignote.

CADRE. Le sujet essentiel reste dans le TIERS CENTRAL de l'image, en largeur. Le site montre ce plan en entier sur ordinateur, mais sur téléphone il n'en garde qu'une bande verticale centrale : tout ce qui compte doit y tenir. Les bords gauche et droit ne portent que du décor, jamais le sujet.

RENDU. Prise de vue réelle, film sportif, qualité commerciale. Colorimétrie neutre, verts justes et non saturés, blancs des lignes contrôlés, noirs profonds dans les gradins. Grain très fin. 30 images par seconde, 8 secondes, format 16:9 horizontal, résolution 3840x2160, 4K NATIVE (réglage de sortie au maximum, aucun agrandissement ultérieur), débit élevé, netteté jusque dans la texture de la pelouse.

INTERDIT. Coupe, fondu au noir, fondu enchaîné, transition ajoutée, effet de volet, rotation de caméra, panoramique, zoom, changement de hauteur, tremblement, flou de mouvement, retour dans le restaurant, table ou voiture ramenée dans le champ, pilier qui s'écarte tout seul, image entièrement noire, projecteur qui clignote, ballon qui roule ou bouge, filet agité, personne, joueur, silhouette, arbitre, animal, oiseau, maillot, numéro, texte, chiffre, score, panneau publicitaire, enseigne, logo, marque, filigrane, fumée, fumigène, poussière, particules, rendu 3D, image de synthèse, aspect jeu vidéo.
```

---

---

# Plan 5 — La cuisine

Le troisième passage, et le premier qui serve un produit plutôt qu'un décor :
la caméra quitte la salle, longe le pilier de pierre, et se retrouve sur le
plan de travail d'une cuisine.

*Écrit pour la prolongation, comme le plan 4.*

> **Le passage se fait sur le pilier, pas sur un menu.** L'idée de départ était
> de traverser une carte fermée. Vérification faite sur l'image de raccord
> réelle : **il n'y a aucun menu sur les tables.** Le demander reviendrait à
> faire apparaître un objet absent — exactement l'erreur qui bloquait le plan 3.
>
> L'image contient mieux. Un large pilier de pierre se dresse à gauche, tout
> près de l'objectif, déjà là dès la première image. Il est mat, texturé, sans
> détail fin à ré-inventer : c'est la surface de passage idéale, et elle existe.
>
> **Et il n'y a pas de « zoom rapide ».** Pas par principe : par arithmétique.
> À dix-sept pixels de défilement par image, un mouvement rapide écarte tant
> deux images consécutives que ni le fondu ni le flot optique ne savent les
> relier — mesuré, la limite est un écart de 18, et le passage le long de la
> Golf était déjà à 23. L'impression de vitesse doit venir du sujet qui
> grossit, jamais de la caméra qui accélère.

```
CONTINUITÉ. Ce plan prolonge le plan précédent sans aucune coupe et sans aucun raccord visible : même lieu, même hauteur de caméra, même axe, même vitesse. Reprends le mouvement exactement là où il s'arrête, sans à-coup, sans repartir, sans réinitialiser le cadrage, sans revenir en arrière.

Un seul plan continu de huit secondes, sans aucune coupe, qui longe un pilier de pierre et débouche sur un plan de travail de cuisine.

MOUVEMENT. Le plan se déroule en trois temps enchaînés, à vitesse rigoureusement constante du début à la fin, sans jamais accélérer, ralentir ni s'arrêter.

Premier temps, environ deux secondes : la caméra poursuit son avance en ligne droite dans l'allée centrale, entre le comptoir à gauche et les tables dressées à droite, et s'approche du large pilier de pierre qui se dresse sur la gauche du cadre. Elle le frôle à quelques centimètres. La pierre envahit progressivement le cadre par la gauche.

Deuxième temps, environ une demi-seconde : le pilier occupe TOUT le cadre. L'image est entièrement remplie par cette pierre chaude et mate, dont on voit le grain et les joints, sans détail net, sans trouée. Elle n'est pas noire : elle est beige, chaude et texturée.

Troisième temps, le reste du plan : le pilier se dégage par la droite et découvre un plan de travail de cuisine professionnelle, vu à hauteur du plan. La caméra avance encore et s'immobilise en douceur devant une planche en chêne huilé, au centre du cadre, sur laquelle est posé un burger entier. À la dernière image le cadre est stable, centré sur le burger, qui occupe environ la moitié de la hauteur.

Aucune rotation, aucun panoramique, aucun zoom, aucun changement de hauteur, aucun tremblement. Le passage le long du pilier n'est ni un fondu, ni une coupe, ni une transition ajoutée : c'est un objet réel, déjà présent dans l'image de départ, que la caméra frôle.

SUJET. Un burger de restaurant, entier, posé sur une planche en chêne huilé. Pain brioché doré parsemé de graines de sésame, légèrement écrasé sur le dessus comme un vrai pain qu'on vient d'assembler. On devine sur la tranche, de haut en bas : la sauce, une tranche de cheddar fondue qui déborde, un steak haché épais aux bords irréguliers et à la croûte grillée, une feuille de sucrine, deux rondelles de tomate. Autour : un plan de travail en inox brossé, propre et vide, quelques ustensiles alignés au fond, une crédence en carrelage blanc. AUCUNE PERSONNE, aucune main, aucun cuisinier. Aucune étiquette, aucune marque, aucun texte, aucune ardoise.

CAMÉRA. Objectif 50 mm, f/4, ISO 400, sur rail motorisé stabilisé, axe strictement horizontal, verticales redressées. Nette de bout en bout, y compris le grain du cuir au moment où il frôle l'objectif. Obturateur 1/1000 s, chaque image parfaitement nette.

LUMIÈRE. La lumière change PENDANT le passage le long du pilier, et à aucun autre moment. Avant : la lumière chaude et tamisée de la salle, exactement celle du plan précédent, inchangée. Après : l'éclairage d'une cuisine, blanc neutre, franc et régulier, venant du haut, sans ombre dure. Une fois la cuisine atteinte, l'exposition et la balance des blancs sont VERROUILLÉES et ne bougent plus.

CADRE. Le sujet essentiel reste dans le TIERS CENTRAL de l'image, en largeur. Le site montre ce plan en entier sur ordinateur, mais sur téléphone il n'en garde qu'une bande verticale centrale : tout ce qui compte doit y tenir. Les bords gauche et droit ne portent que du décor, jamais le sujet.

RENDU. Prise de vue réelle, film culinaire haut de gamme, qualité commerciale. Colorimétrie neutre et fidèle, couleurs justes et non sursaturées. Grain très fin. 30 images par seconde, 8 secondes, format 16:9 horizontal, résolution 3840x2160, 4K NATIVE (réglage de sortie au maximum, aucun agrandissement ultérieur), débit élevé, netteté jusque dans les textures fines : graines de sésame, croûte du steak, grain du pain.

INTERDIT. Coupe, fondu au noir, fondu enchaîné, transition ajoutée, rotation de caméra, panoramique, zoom, changement de hauteur, tremblement, accélération, ralentissement, flou de mouvement, pilier qui s'écarte tout seul, retour dans la salle, table ou chaise ramenée dans le champ, texte, carte, menu lisible, caractère, chiffre, prix, image entièrement noire, personne, main, cuisinier, animal, flamme, vapeur, fumée, buée, gouttes qui coulent, particules, plastique, couleurs fluorescentes, enseigne, logo, marque, filigrane, rendu 3D, image de synthèse.
```

---

# Plan 6 — Le burger

Le mécanisme. La caméra ne bouge plus : c'est le sujet qui se démonte.

*Écrit pour la prolongation.*

> **Un éclaté est parfaitement réversible** — il se remonte comme il s'est
> défait, exactement comme les portières du beat qu'on avait écrit pour la
> voiture. C'est un mécanisme, pas une entropie. Ce qui reste interdit, c'est
> ce qui accompagne d'ordinaire une image de burger : vapeur, fumée, sauce qui
> coule, gouttes qui tombent. Tout ça ne se remonte pas.
>
> Le mouvement **n'est pas terminé à la dernière image** : les couches
> s'écartent encore. Un mouvement qui s'achève invite à s'arrêter ; un
> mouvement en cours invite à continuer.

```
CONTINUITÉ. Ce plan prolonge le plan précédent sans aucune coupe et sans aucun raccord visible : même burger, même planche, même cuisine, même lumière, même cadrage. Reprends exactement là où il s'arrête.

Un seul plan continu de huit secondes, sans aucune coupe, où un burger se démonte en l'air, couche par couche.

MOUVEMENT. La caméra est RIGOUREUSEMENT FIXE du début à la fin : aucune avance, aucun recul, aucune rotation, aucun panoramique, aucun zoom, aucun tremblement. C'est le sujet seul qui bouge.

Depuis le burger entier, les couches se séparent et s'écartent verticalement, EN MÊME TEMPS, à vitesse rigoureusement constante et linéaire du début à la fin : le pain du haut monte, la sauce reste posée sur sa face intérieure, la tranche de cheddar suit, puis le steak, puis la feuille de sucrine, puis les rondelles de tomate, le pain du bas restant seul sur la planche. Chaque élément monte en ligne droite, garde son orientation exacte, ne tourne pas sur lui-même, ne se déforme pas, ne rétrécit pas. Ils flottent, suspendus, sans support ni fil. Un léger décalage latéral entre les étages permet de les voir tous. Le mouvement n'est pas terminé à la dernière image : les couches s'écartent encore.

SUJET. Le même burger que le plan précédent, sur la même planche en chêne huilé. Pain brioché doré aux graines de sésame, sauce beige mouchetée d'herbes et de cornichon étalée sur la face intérieure grillée du pain du haut, tranche de cheddar orangé entièrement fondue et figée en pleine coulée, steak haché épais aux bords irréguliers et à la croûte brun foncé marquée par la plancha, feuille de sucrine croquante aux bords ondulés, deux rondelles de tomate cœur de bœuf épaisses dont on voit les graines et la chair. AUCUNE PERSONNE, aucune main. Aucune étiquette, aucune marque, aucun texte.

CAMÉRA. Objectif 50 mm, f/8, ISO 400, sur pied, rigoureusement fixe. Tout est net, de la couche la plus proche à la plus lointaine. Obturateur 1/1000 s, chaque image parfaitement nette, sans le moindre flou de bougé.

LUMIÈRE. Exactement celle du plan précédent, inchangée : éclairage de cuisine blanc neutre venant du haut, franc et régulier, sans ombre dure. Chaque couche détachée porte sa propre ombre douce, cohérente avec cette source. Exposition et balance des blancs VERROUILLÉES du début à la fin.

CADRE. Le sujet essentiel reste dans le TIERS CENTRAL de l'image, en largeur. Le site montre ce plan en entier sur ordinateur, mais sur téléphone il n'en garde qu'une bande verticale centrale : tout ce qui compte doit y tenir. Les bords gauche et droit ne portent que du décor, jamais le sujet.

RENDU. Prise de vue réelle, photographie culinaire professionnelle en lévitation, qualité commerciale. Colorimétrie neutre et fidèle, couleurs justes et non sursaturées. Grain très fin. 30 images par seconde, 8 secondes, format 16:9 horizontal, résolution 3840x2160, 4K NATIVE (réglage de sortie au maximum, aucun agrandissement ultérieur), débit élevé, netteté jusque dans les textures fines : graines de sésame, mie du pain, croûte du steak, graines de la tomate.

INTERDIT. Coupe, fondu, transition ajoutée, mouvement de caméra, rotation, panoramique, zoom, tremblement, flou de mouvement, couche qui tourne sur elle-même, couche qui se déforme ou change de taille, couche qui sort du cadre, explosion, projection, éclat, écartement saccadé ou à vitesse variable, support, fil, socle, vapeur, fumée, buée, sauce qui coule ou goutte, jus qui tombe, miette qui vole, particules, variation d'exposition, personne, main, animal, texte, chiffre, étiquette, logo, marque, filigrane, plastique, couleurs fluorescentes, rendu 3D, image de synthèse.
```

---

# Juger, avant de me les envoyer

Regardez chaque plan **deux fois** :

1. **En lecture normale.** Ce qui vous gêne ici sera pire au défilement : la
   scrutation d'une image fixe est bien plus sévère que la lecture à 24 i/s.
2. **Image par image, à la flèche**, sur un détail fin et répétitif — les
   mailles d'un filet, les bandes de tonte, le gravier, les rayons d'une
   jante. C'est là que l'incohérence apparaît en premier.

Les quatre échecs :

- **Le frémissement.** Les détails fins vibrent sans que rien ne bouge. Le
  modèle ré-invente le détail à chaque image. Irrécupérable, à refaire.
- **Le décor qui respire.** Une pièce change discrètement de proportions
  pendant le plan. Invisible en lecture normale, d'où l'image par image.
- **La jointure qui saute.** Deux plans consécutifs ne raccordent pas :
  l'image de départ n'a pas été jointe, ou pas respectée. Régénérez le second.
- **Quelqu'un apparaît.** Une silhouette au fond, un reflet dans une vitre.
  À refaire : au défilement, elle changera de visage à chaque image.

---

# Le montage

Les cinq plans se donnent **dans l'ordre**, sur une seule ligne. Les images
sont réparties au prorata de la durée de chaque plan, donc la vitesse reste
constante d'un bout à l'autre :

```
python3 film_video.py villa.mp4 piscine.mp4 voiture.mp4 restaurant.mp4 cuisine.mp4 burger.mp4 960 1280 accueil
python3 build_ultra.py 78 1280 artefact
```

Avant de monter, passez chaque plan au diagnostic — il signale les coupes et
le gel de fin que les modèles produisent presque toujours :

```
python3 film_video.py villa.mp4 profil
```

et rognez au besoin : `villa.mp4@0-180`.
