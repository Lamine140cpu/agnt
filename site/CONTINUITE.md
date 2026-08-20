# La continuité — cinq mondes, un seul mouvement

Le prologue du site n'est pas une suite d'exemples. C'est **un seul travelling
avant qui ne s'arrête jamais** et qui traverse cinq métiers : une villa, une
piscine, une voiture — dehors puis dedans —, un restaurant, un terrain de foot.

C'est ça, la démonstration. Pas « voici cinq sites », mais « voici cinq
commerces sur le même rail, et vous ne voyez pas la jointure ».

---

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

Un plan généré fait 8 secondes ; la continuité en fait quarante-huit. On les
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
5. ... et ainsi de suite jusqu'au plan 6
```

Chaque prompt ci-dessous commence par une ligne de raccord, **à garder telle
quelle sauf pour le plan 1**.

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
Six plans de 37 images coûtent exactement ce que coûtaient cinq plans de 44.
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

RENDU. Prise de vue réelle, film d'architecture, qualité commerciale. Colorimétrie neutre et fidèle, contraste doux, hautes lumières de la baie légèrement soutenues comme sur une vraie photographie. Grain photographique très fin. 24 images par seconde, 8 secondes, format 16:9 horizontal, résolution 1920x1080 minimum, débit élevé, aucune compression agressive.

INTERDIT. Coupe, changement de plan, fondu, transition, saut, rotation de caméra, panoramique, zoom, tremblement, accélération, ralentissement, flou de mouvement, flou de bougé, variation d'exposition, personne, silhouette, main, animal, reflet d'équipe, texte, chiffre, logo, marque, enseigne, filigrane, signature, rideau qui bouge, feuillage agité, fumée, vapeur, poussière, particules, rendu 3D, image de synthèse, aspect jeu vidéo, couleurs saturées, HDR excessif.
```

---

# Plan 2 — La piscine

```
L'image jointe est la première image de ce plan. Reprends exactement la même villa, la même lumière, la même hauteur de caméra, et poursuis le mouvement sans le moindre à-coup.

Un seul plan continu de huit secondes, sans aucune coupe, qui franchit la baie vitrée et glisse au-dessus d'une piscine.

MOUVEMENT. La caméra poursuit son avance en ligne droite, à la même vitesse rigoureusement constante que le plan précédent : elle franchit l'ouverture, traverse la terrasse en pierre, et continue au-dessus de la piscine en gardant exactement la même hauteur. À la dernière image elle est parvenue au bord opposé du bassin, et l'on découvre au-delà une allée en gravier clair. Aucune rotation, aucune plongée, aucun zoom, aucun tremblement. La surface de l'eau est parfaitement lisse et immobile, comme un miroir : aucune vague, aucune ride, aucun clapot.

SUJET. Terrasse en pierre claire prolongeant la villa, puis une piscine à débordement rectangulaire, eau turquoise très calme, margelles en pierre. Deux transats en teck et toile écrue, alignés, vides. Un parasol fermé. Massifs de lavande et d'oliviers taillés en bordure. Au fond, une allée en gravier clair bordée de cyprès. AUCUNE PERSONNE, aucune silhouette, aucun animal, aucun objet flottant. Aucune marque, aucun texte lisible.

CAMÉRA. Objectif 24 mm, f/5.6, ISO 100, sur rail motorisé stabilisé, axe strictement horizontal à un mètre soixante du sol, verticales redressées. Nette de bout en bout. Obturateur 1/1000 s, chaque image parfaitement nette, y compris les reflets sur l'eau.

LUMIÈRE. Soleil rasant de fin de journée, venant de la droite, dorant la pierre et allumant un long reflet étiré sur l'eau immobile. Aucune lampe allumée. Exposition et balance des blancs VERROUILLÉES : aucune variation entre l'intérieur sombre et l'extérieur lumineux au moment du franchissement — l'image ne doit ni s'éclaircir ni s'assombrir en sortant.

RENDU. Prise de vue réelle, film d'architecture, qualité commerciale. Colorimétrie neutre et fidèle, contraste doux, grain très fin. 24 images par seconde, 8 secondes, format 16:9 horizontal, résolution 1920x1080 minimum, débit élevé.

INTERDIT. Coupe, fondu, transition, rotation de caméra, plongée, zoom, tremblement, changement de vitesse, flou de mouvement, variation d'exposition au passage de la baie, vague, ride, clapot, remous, éclaboussure, reflet qui rampe, personne, silhouette, animal, oiseau, texte, chiffre, logo, marque, filigrane, feuillage agité par le vent, fumée, vapeur, particules, rendu 3D, image de synthèse.
```

---
# Plan 3 — La voiture, dehors

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

**Pas de photo d'intérieur dans ce plan-ci.** L'habitacle n'y apparaît jamais :
la caméra est dehors et les vitres sont teintées. Une référence que le modèle
ne peut satisfaire nulle part, il essaie quand même de la placer — il détient
les vitres, ou il fait dériver la caméra vers l'intérieur en plein milieu, ce
qui casse la continuité. Les photos d'habitacle vont au plan 4, qui est fait
pour elles.

Prises par temps couvert si possible : une photo en plein soleil impose ses
ombres au plan, et elles ne coïncideront pas avec le crépuscule demandé.

**Ne décrivez pas la voiture en détail dans le prompt.** C'est le réflexe
naturel et c'est l'erreur : un paragraphe de description entre en concurrence
avec les photos, et le modèle arbitre au hasard. Le prompt nomme le modèle,
pose deux ou trois repères vérifiables, et laisse les images faire le reste.

```
IMAGES JOINTES — deux rôles distincts, à ne pas confondre.

La première image jointe est L'IMAGE DE DÉPART de ce plan : elle donne le lieu, le cadrage, la hauteur de caméra et la lumière. Le plan commence exactement sur elle et poursuit le mouvement sans le moindre à-coup.

Les autres images jointes sont des PHOTOGRAPHIES DE RÉFÉRENCE DU VÉHICULE. Elles ne sont pas le décor et ne donnent ni le cadrage ni la lumière : elles servent uniquement à reproduire fidèlement cette voiture précise — sa forme, ses proportions, sa couleur, ses jantes, ses optiques, ses détails. Reproduis-la exactement telle qu'elle apparaît sur ces photos, sans rien inventer ni styliser.

Un seul plan continu de huit secondes, sans aucune coupe, qui quitte la piscine et longe une voiture garée sur l'allée.

MOUVEMENT. La caméra poursuit son avance en ligne droite, à la même vitesse rigoureusement constante que le plan précédent : elle quitte le bassin, traverse l'allée de gravier, atteint la voiture garée de profil et la longe du capot jusqu'à la portière conducteur, sans jamais tourner ni s'arrêter. Les portières avant sont grandes ouvertes et parfaitement immobiles : à la dernière image, la caméra est arrivée devant l'ouverture de la portière conducteur, qui occupe une grande partie du cadre, et l'on aperçoit l'habitacle au-delà. Aucune rotation, aucun zoom, aucun tremblement. La voiture est absolument immobile : roues droites, aucune roue qui tourne, aucune suspension qui travaille, et les portières ouvertes ne bougent pas.

SUJET. Une Volkswagen Golf 8 GTI rouge, exactement celle des photographies de référence jointes. Compacte cinq portes. Ses proportions, sa teinte rouge, le dessin de ses jantes, la forme de ses optiques et tous ses détails doivent correspondre aux photographies — c'est le même véhicule, vu sous un autre angle et dans une autre lumière, pas une interprétation. Trois repères à vérifier : le bandeau lumineux horizontal qui traverse la calandre d'un phare à l'autre, le liseré rouge qui la souligne sur toute sa largeur, et les étriers de frein rouges derrière les jantes. Carrosserie propre et polie, vitres teintées, phares allumés, blancs et constants. Les deux portières avant sont grandes ouvertes, immobiles, et ne bougent pas d'un degré pendant tout le plan. AUCUNE plaque d'immatriculation : les emplacements sont lisses et vides. Elle est garée de profil sur une allée de gravier clair bordée de cyprès. AUCUNE PERSONNE.

CAMÉRA. Objectif 35 mm, f/5.6, ISO 100, sur rail motorisé stabilisé, axe strictement horizontal à un mètre soixante du sol, verticales redressées. La voiture reste entièrement visible dans le cadre pendant tout le passage, avec une marge d'air nette au-dessus et en dessous. Nette de bout en bout. Obturateur 1/1000 s : carrosserie parfaitement nette sur chaque image, sans le moindre flou de bougé.

LUMIÈRE. Crépuscule commençant, celle de l'image de départ et non celle des photographies de référence. Ciel orangé bas à droite, lumière rasante et douce qui court le long du flanc en un long reflet étiré. Le rouge de la carrosserie reste franc et lisible, ni orangé par le couchant ni assombri. Aucune ombre dure, aucun reflet ponctuel qui saute. Exposition et balance des blancs VERROUILLÉES du début à la fin.

RENDU. Prise de vue réelle, film publicitaire automobile, qualité commerciale. Colorimétrie neutre, contraste doux, noirs profonds mais lisibles. Grain très fin. 24 images par seconde, 8 secondes, format 16:9 horizontal, résolution 1920x1080 minimum, débit élevé, netteté jusque dans les textures fines : rayons de jantes, nid d'abeille de la calandre, grain du gravier.

INTERDIT. Coupe, fondu, transition, rotation de caméra, zoom, tremblement, changement de vitesse, flou de mouvement, flou de bougé, véhicule différent de celui des photographies, proportions modifiées, teinte modifiée, jantes inventées, carrosserie trois portes, break, berline, plaque d'immatriculation, roue qui tourne, portière qui s'ouvre ou se referme pendant le plan, suspension qui travaille, variation d'exposition, personne, silhouette, animal, texte, chiffre, enseigne, filigrane, fumée, poussière soulevée, gerbe, particules, rendu 3D, image de synthèse, aspect jeu vidéo.
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

# Plan 4 — La voiture, dedans

C'est ici que vont vos photos d'habitacle.

**La caméra traverse la voiture, elle n'y entre pas pour en ressortir.** C'est
tout le problème résolu : la continuité est un travelling avant qui ne recule
jamais. Faire entrer la caméra puis la faire sortir par où elle est venue
imposerait une marche arrière, qui se lit comme une erreur au défilement. Elle
entre donc par la portière conducteur, traverse l'habitacle, et sort par la
portière passager — toujours vers l'avant, sans jamais tourner.

Joignez trois photos d'intérieur : **le poste de conduite de face**, **la vue
depuis la place conducteur vers la portière passager** (c'est l'axe qu'on va
filmer), et **un détail de matière** — surpiqûre, cuir du volant, tissu du
siège.

```
IMAGES JOINTES — deux rôles distincts, à ne pas confondre.

La première image jointe est L'IMAGE DE DÉPART de ce plan : elle donne le lieu, le cadrage, la hauteur de caméra et la lumière. Le plan commence exactement sur elle et poursuit le mouvement sans le moindre à-coup.

Les autres images jointes sont des PHOTOGRAPHIES DE RÉFÉRENCE DE L'HABITACLE. Elles ne donnent ni le cadrage ni la lumière : elles servent uniquement à reproduire fidèlement cet intérieur précis — sa planche de bord, son volant, ses sièges, ses matières, ses couleurs. Reproduis-le exactement tel qu'il apparaît sur ces photos, sans rien inventer ni styliser.

Un seul plan continu de huit secondes, sans aucune coupe, qui traverse l'habitacle d'une voiture d'une portière à l'autre.

MOUVEMENT. La caméra poursuit son avance en ligne droite, à la même vitesse rigoureusement constante que le plan précédent, et sur le même axe : elle franchit l'ouverture de la portière conducteur, passe devant le volant à hauteur des yeux d'un conducteur assis, traverse l'habitacle au-dessus de la console centrale, et ressort par l'ouverture de la portière passager. À la dernière image elle est de nouveau dehors, et l'on découvre au-delà une terrasse de restaurant couverte. Elle ne recule jamais, ne tourne jamais, ne pivote jamais, ne ralentit jamais. Aucun zoom, aucun tremblement. Rien ne bouge dans l'habitacle : ni volant, ni levier, ni aiguille, ni ceinture, ni portière.

SUJET. L'habitacle d'une Volkswagen Golf 8 GTI, exactement celui des photographies de référence jointes : même planche de bord, même volant, mêmes sièges, mêmes matières, mêmes couleurs, mêmes surpiqûres. C'est le même véhicule que le plan précédent, vu de l'intérieur. Habitacle propre et vide : aucun objet personnel, aucun bagage, aucune boisson, AUCUNE PERSONNE, aucune main. Les écrans sont allumés et affichent un aplat sombre uni, sans texte, sans icône, sans chiffre. Aucun logo lisible sur le volant ni ailleurs.

CAMÉRA. Objectif 24 mm, f/4, ISO 400, sur rail motorisé stabilisé, axe strictement horizontal, verticales redressées, aucune rotation. Nette de bout en bout. Obturateur 1/1000 s : chaque image parfaitement nette, sans le moindre flou de bougé.

LUMIÈRE. Crépuscule, celle du plan précédent et non celle des photographies de référence. Lumière douce et déclinante entrant par les deux ouvertures et par le pare-brise. Exposition et balance des blancs VERROUILLÉES du début à la fin : aucune variation de luminosité au passage du dehors clair vers l'habitacle sombre puis vers le dehors — l'intérieur reste ouvert et lisible, l'image ne clignote pas.

RENDU. Prise de vue réelle, film publicitaire automobile, qualité commerciale. Colorimétrie neutre, contraste doux, ombres de l'habitacle ouvertes et lisibles. Grain très fin. 24 images par seconde, 8 secondes, format 16:9 horizontal, résolution 1920x1080 minimum, débit élevé, netteté jusque dans les textures fines : grain du plastique, trame du tissu, surpiqûres.

INTERDIT. Coupe, fondu, transition, rotation de caméra, panoramique, zoom, marche arrière, tremblement, changement de vitesse, flou de mouvement, habitacle différent de celui des photographies, volant qui tourne, aiguille qui bouge, écran qui change, voyant qui s'allume ou clignote, ceinture qui pend et se balance, portière qui bouge, assombrissement à l'entrée dans l'habitacle, variation d'exposition, personne, main, silhouette, reflet d'équipe dans le pare-brise, texte, chiffre, logo, marque, filigrane, poussière, particules, rendu 3D, image de synthèse.
```

---

# Plan 5 — Le restaurant

```
L'image jointe est la première image de ce plan. Reprends exactement le même lieu, la même lumière, la même hauteur de caméra, et poursuis le mouvement sans le moindre à-coup.

Un seul plan continu de huit secondes, sans aucune coupe, qui entre sur une terrasse de restaurant dressée et la traverse.

MOUVEMENT. La caméra poursuit son avance en ligne droite, à la même vitesse rigoureusement constante : elle quitte la voiture, franchit les derniers mètres de gravier, pénètre sous la terrasse couverte et glisse dans l'allée centrale, entre deux rangées de tables dressées. À la dernière image elle atteint le fond de la salle, où une large ouverture donne sur un terrain de sport éclairé. Aucune rotation, aucun zoom, aucun tremblement. Rien ne bouge : ni nappe, ni bougie, ni feuillage, ni rideau.

SUJET. Terrasse de restaurant couverte, charpente en bois clair, sol en tomettes. Deux rangées de tables carrées en chêne massif, entièrement dressées et parfaitement alignées : nappes en lin écru, assiettes en grès mat, verres à pied, couverts alignés, une petite bougie éteinte au centre de chaque table. Chaises en bois cintré et cannage. Guirlande d'ampoules à filament allumées le long de la charpente, lumière chaude et constante. Un bar en zinc sur la gauche, bouteilles alignées sans étiquette lisible. AUCUNE PERSONNE, aucune silhouette, aucun serveur, aucune main. Aucune enseigne, aucun menu lisible, aucune marque, aucun texte.

CAMÉRA. Objectif 24 mm, f/4, ISO 200, sur rail motorisé stabilisé, axe strictement horizontal à un mètre soixante du sol, verticales parfaitement redressées. Nette de bout en bout. Obturateur 1/1000 s, chaque image parfaitement nette.

LUMIÈRE. Tombée de la nuit. Ciel bleu profond au-delà de la terrasse, guirlande d'ampoules chaudes à l'intérieur, déjà allumées et rigoureusement constantes. Aucune flamme, aucune bougie allumée, aucune source qui vacille ou varie. Exposition et balance des blancs VERROUILLÉES du début à la fin.

RENDU. Prise de vue réelle, film de restaurant haut de gamme, qualité commerciale. Colorimétrie chaude mais fidèle, contraste doux, hautes lumières des ampoules contrôlées. Grain très fin. 24 images par seconde, 8 secondes, format 16:9 horizontal, résolution 1920x1080 minimum, débit élevé.

INTERDIT. Coupe, fondu, transition, rotation de caméra, zoom, tremblement, changement de vitesse, flou de mouvement, variation d'exposition, personne, silhouette, serveur, main, animal, flamme, bougie allumée, ampoule qui vacille, nappe qui bouge, rideau agité, texte, menu, chiffre, prix, enseigne, logo, marque, étiquette lisible, filigrane, fumée, vapeur de plat, particules, rendu 3D, image de synthèse.
```

---

# Plan 6 — Le terrain

```
L'image jointe est la première image de ce plan. Reprends exactement le même lieu, la même lumière, la même hauteur de caméra, et poursuis le mouvement sans le moindre à-coup.

Un seul plan continu de huit secondes, sans aucune coupe, qui sort du restaurant et glisse au-dessus d'un terrain de football éclairé.

MOUVEMENT. La caméra poursuit son avance en ligne droite, à la même vitesse rigoureusement constante : elle franchit l'ouverture, quitte la terrasse et glisse au-dessus de la pelouse, en gardant exactement la même hauteur, jusqu'au rond central. Sur la dernière seconde, elle ralentit régulièrement et s'immobilise. À la dernière image le cadre est calme et stable, centré sur le rond central, avec une large zone de pelouse unie et sans détail au centre de l'image. Aucune rotation, aucun zoom, aucun tremblement.

SUJET. Un terrain de football en herbe, fraîchement tondu, avec ses bandes de tonte alternées bien nettes et son marquage blanc impeccable. Le rond central, le point de penalty, les lignes de touche. Un but avec ses filets blancs tendus au fond. Un ballon blanc posé, immobile, sur le point central. Gradins vides et sombres au-delà. AUCUNE PERSONNE, aucun joueur, aucune silhouette, aucun animal. Aucun panneau publicitaire, aucune enseigne, aucun logo, aucun texte, aucun maillot, aucun numéro.

CAMÉRA. Objectif 24 mm, f/4, ISO 400, sur rail motorisé stabilisé, axe strictement horizontal à un mètre soixante du sol, verticales redressées. Nette de bout en bout. Obturateur 1/1000 s, chaque image parfaitement nette, y compris les brins d'herbe et les mailles du filet.

LUMIÈRE. Nuit. Quatre mâts de projecteurs allumés, lumière blanche franche et rigoureusement constante, qui pose de larges nappes claires sur la pelouse et dessine les bandes de tonte. Ciel noir. Aucun projecteur qui s'allume, s'éteint ou clignote. Exposition et balance des blancs VERROUILLÉES du début à la fin.

RENDU. Prise de vue réelle, film sportif, qualité commerciale. Colorimétrie neutre, verts justes et non saturés, blancs des lignes contrôlés, noirs profonds dans les gradins. Grain très fin. 24 images par seconde, 8 secondes, format 16:9 horizontal, résolution 1920x1080 minimum, débit élevé, netteté jusque dans la texture de la pelouse.

INTERDIT. Coupe, fondu, transition, rotation de caméra, zoom, tremblement, flou de mouvement, variation d'exposition, projecteur qui clignote, ballon qui roule ou bouge, filet agité, personne, joueur, silhouette, arbitre, animal, maillot, numéro, texte, chiffre, score, panneau publicitaire, enseigne, logo, marque, filigrane, fumée, fumigène, poussière, particules, rendu 3D, image de synthèse, aspect jeu vidéo.
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
python3 film_video.py villa.mp4 piscine.mp4 voiture.mp4 habitacle.mp4 restaurant.mp4 terrain.mp4 220 1440 accueil
python3 build_ultra.py 78 1280 artefact
```

Avant de monter, passez chaque plan au diagnostic — il signale les coupes et
le gel de fin que les modèles produisent presque toujours :

```
python3 film_video.py villa.mp4 profil
```

et rognez au besoin : `villa.mp4@0-180`.
