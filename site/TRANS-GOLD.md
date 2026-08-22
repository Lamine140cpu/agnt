# Trans Gold — la continuité

Premier client réel. Transport de marchandises et logistique, depuis 2017,
France et Europe. Deux véhicules : un ensemble tracteur + semi-remorque
fourgon pour la longue distance, un porteur à caisse pour la livraison.

Six plans de huit secondes, chaînés, qui racontent une livraison de bout en
bout : l'aube sur la route, le flanc du camion, ce qu'il y a dedans, la
distance, le dernier kilomètre, la palette posée.

---

## LA LIVRÉE EST GÉNÉRÉE, ET C'EST UN CHOIX ASSUMÉ

Deux méthodes étaient possibles. Elles sont notées ici pour mémoire, parce que
si un défaut apparaît plus tard on saura d'où il vient.

**La méthode écartée : camions blancs, logo composé après coup.** Les
véhicules sortent entièrement blancs, et le logo vectoriel est posé par calcul
géométrique sur les surfaces planes. Avantage : le logo est identique sur les
1 440 images, net et correctement orthographié. Inconvénient : du travail en
plus, et elle exige le fichier vectoriel.

**La méthode retenue : la livrée est générée avec le reste.** Le modèle
travaille à partir des images de référence du client, donc il RECOPIE le logo
au lieu de l'inventer — ce qui est très différent d'une génération à partir de
texte seul, et rend la première image fidèle.

Le risque connu porte sur la SUITE des images. Un modèle redessine le logo à
chaque image, et rien ne garantit qu'il le redessine identique : les petites
lignes de texte peuvent se déformer d'une image à l'autre. Sur une vidéo lue à
trente images par seconde cela ne se voit pas ; sur un site qui s'arrête sur
une image et la tient, cela peut se voir. Les images de référence fournies
portent déjà « TRAN$ GOLD » sur une vignette.

**Ce qu'il faut donc vérifier dès le premier plan rendu**, avant d'en générer
cinq autres : extraire les images 1, 60, 120, 180 et 240, les poser côte à
côte, et regarder si le logo est le même sur les cinq. Dix secondes de
contrôle qui évitent de découvrir le problème à la livraison.

Si la livrée tient, il n'y a rien à faire de plus. Si elle dérive, la méthode
écartée reste disponible, et seul le temps de génération aura été perdu.

**Les plaques d'immatriculation, elles, restent vides dans tous les cas.** Ce
n'est pas une question de style : un numéro inventé par un modèle a de bonnes
chances de correspondre à un véhicule réel appartenant à quelqu'un d'autre.
On décrit donc des emplacements lisses et unis — un véhicule de présentation.

## UN SEUL CAMION À L'ÉCRAN, TOUJOURS

Aucun plan ne montre deux véhicules. On ne connaît pas la taille exacte de la
flotte, et un parking de douze ensembles alignés serait le même mensonge que
le logo déformé. Un seul camion, bien filmé, est de toute façon plus fort —
c'est ce que fait toute la publicité automobile.

## CE QU'ILS TRANSPORTENT

« Tout », c'est-à-dire du fret général. Visuellement : **des palettes
banalisées**, filmées et sanglées, de hauteurs inégales. Pas de groupe
frigorifique, pas de fût, pas de bâche à logo, rien qui désigne un secteur.
Ce qui doit se voir, ce n'est pas la marchandise — c'est **le soin avec
lequel elle est tenue**.

## LES LOIS, INCHANGÉES

Elles viennent de la vitrine et rien ici ne les remet en cause.

  1. **Réversible, pas immobile.** Une porte qui s'ouvre, un hayon qui
     descend : ça se remonte. De la fumée, de la poussière, une gerbe d'eau :
     non. Le visiteur remonte le film aussi souvent qu'il le descend.
  2. **Aucun flou de bougé.** 1/1000 s partout. Une image extraite est
     regardée FIXE ; un filé qui passe inaperçu à trente images par seconde
     devient une bouillie quand on s'arrête dessus. Le mouvement se lit dans
     l'écart entre deux images, pas dans le flou de chacune.
  3. **Personne à l'écran.** Pas de chauffeur, pas de cariste, pas de main.
     Un visage date une image et impose une identification ; on vend un
     service, pas un employé.

## LE PASSAGE

Chaque plan reçoit son raccord par une **masse opaque qui remplit le cadre
une demi-seconde** — la porte arrière, le montant, le mur d'un quai. Elle est
toujours **au DÉBUT du plan qui reçoit**, jamais à la fin de celui qui donne :
la dernière image d'un plan sert à conditionner le suivant, elle doit donc
porter de l'information, pas du noir.

C'est ce qui permet de changer de lieu, d'heure et même de véhicule sans
qu'aucune coupe ne se voie.

## RÉGLAGES DE SORTIE

16:9 horizontal · 3840x2160 en 4K native · 30 i/s · 8 secondes · réglage de
qualité au maximum, **aucun agrandissement ultérieur**.

Vérifier le format à chaque plan : c'est le réglage qui se réinitialise le
plus souvent, et quatre plans de la vitrine étaient sortis en vertical à
cause de ça.

## LA BOUCLE

1. Générer le plan.
2. Extraire sa **dernière image**.
3. La joindre comme **image de départ** du plan suivant.
4. Recommencer.

---

# Plan 1 — L'aube

**Le camion ne bouge pas dans le cadre, c'est le paysage qui file.**

La caméra roule à la vitesse exacte du camion, à son niveau. C'est le plan le
plus simple à traiter proprement : le véhicule étant immobile dans l'image,
la surface qui portera le logo l'est aussi, et la composition ultérieure n'a
presque rien à suivre.

```
IMAGES JOINTES — deux rôles distincts, à ne pas confondre.

La première image jointe est L'IMAGE DE DÉPART de ce plan : elle donne le lieu, le cadrage, la hauteur de caméra et la lumière. Le plan commence exactement sur elle et poursuit le mouvement sans le moindre à-coup.

Les autres images jointes sont les RÉFÉRENCES DE LA LIVRÉE. Elles ne donnent ni le décor, ni le cadrage, ni la lumière : elles servent uniquement à reproduire fidèlement le marquage du véhicule — la marque circulaire, ses couleurs, sa typographie, sa position sur la caisse. Reproduis-la exactement telle qu'elle apparaît sur ces images, sans rien redessiner, sans rien styliser, sans rien réinterpréter.

Un seul plan continu de huit secondes, sans aucune coupe, qui accompagne un ensemble routier seul sur une autoroute, à l'aube.

MOUVEMENT. La caméra se déplace latéralement à la vitesse EXACTE du camion, à son niveau, sur un axe parallèle à la route : le camion reste donc rigoureusement immobile dans le cadre, tandis que le paysage, la glissière et le bitume défilent derrière lui de la droite vers la gauche, à vitesse rigoureusement constante. En plus de ce mouvement d'accompagnement, la caméra se rapproche très lentement et en ligne droite : à la première image on voit l'ensemble entier de trois quarts avant, à la dernière on est plus près, cadré sur la cabine et le début de la caisse. Aucune rotation, aucun panoramique, aucun zoom, aucun tremblement, aucune variation de vitesse. Les roues tournent, la route défile, rien d'autre ne bouge.

SUJET. Un ensemble routier moderne : tracteur à cabine haute avec couchette, attelé à une semi-remorque fourgon à parois lisses. La caisse porte la LIVRÉE décrite plus bas, conforme aux images de référence. Le reste de la carrosserie est blanc et lisse. Les emplacements de plaque d'immatriculation, devant comme derrière, sont LISSES, VIDES ET UNIS : pas de plaque, pas de support, aucun caractère. Vitres teintées, rétroviseurs noirs, jantes en acier claires, pneus propres. Phares allumés, blancs et constants. Feux de gabarit orange allumés le long du pavillon. AUCUNE PERSONNE, aucune silhouette dans la cabine, aucun autre véhicule sur la route.

DÉCOR. Une autoroute à deux voies, bitume sombre et régulier, marquage blanc net, glissière métallique. De part et d'autre, des collines douces et des champs, végétation d'automne. Ciel de fin de nuit : bleu profond au zénith, virant à l'orange pâle sur l'horizon. Aucun panneau, aucune sortie, aucun péage, aucun bâtiment, aucun texte lisible nulle part.

LIVRÉE. Le marquage de Trans Gold, exactement celui des images de référence jointes, sur une caisse blanche. Au centre du flanc, une grande marque circulaire : un globe terrestre bleu et blanc, encerclé par deux arcs épais — l'un bleu montant à gauche, l'autre rouge descendant à droite — prolongés à droite par trois traits obliques en fuite. Devant le globe, la silhouette blanche et grise d'un ensemble routier vu de trois quarts avant. Sous le globe, le mot TRANS GOLD en grandes capitales dorées à ombre portée ; en dessous, le mot MARCHANDISES en capitales grises fines encadrées de deux filets horizontaux ; en dessous encore, la ligne TRANSPORT DE MARCHANDISES & LOGISTIQUE en très petites capitales ; enfin, en bas, la mention DEPUIS 2017 sur deux lignes. L'orthographe est EXACTEMENT celle-ci, lettre pour lettre, sur toutes les images du plan sans exception : TRANS GOLD, MARCHANDISES, TRANSPORT DE MARCHANDISES & LOGISTIQUE, DEPUIS 2017. Aucune lettre ne change de forme, aucune ne disparaît, aucune ne s'ajoute d'une image à l'autre. Une version réduite de la même marque figure sur la portière de la cabine. Le reste de la carrosserie est blanc, lisse et uni.

CAMÉRA. Objectif 50 mm, f/5.6, ISO 400, sur véhicule travelling parfaitement stabilisé, axe strictement horizontal à deux mètres du sol, verticales parfaitement redressées. Nette de bout en bout, y compris sur le paysage qui défile. Obturateur très rapide, 1/1000 s : chaque image parfaitement nette, AUCUN FILÉ sur le décor, aucun flou de roue, aucun flou de bougé. Le mouvement doit se lire dans l'écart entre deux images, jamais dans le flou d'une seule.

LUMIÈRE. Heure bleue, juste avant le lever du soleil. Lumière douce et froide venant du ciel, sans source dure, sans ombre portée marquée. La carrosserie blanche prend les bleus du ciel sur ses parties hautes et les ocres de l'horizon sur ses parties basses. Phares et feux de gabarit constants, sans halo excessif. Exposition et balance des blancs VERROUILLÉES du début à la fin.

CADRE. Le sujet essentiel reste dans le TIERS CENTRAL de l'image, en largeur. Le site montre ce plan en entier sur ordinateur, mais sur téléphone il n'en garde qu'une bande verticale centrale : la cabine et le début de la caisse doivent y tenir. Les bords gauche et droit ne portent que du paysage.

RENDU. Prise de vue réelle, film publicitaire automobile haut de gamme, qualité commerciale. Colorimétrie neutre et fidèle, contraste doux, blancs de la carrosserie tenus et non brûlés, noirs des pneus lisibles. Grain photographique très fin. 30 images par seconde, 8 secondes, format 16:9 horizontal, résolution 3840x2160, 4K NATIVE (réglage de sortie au maximum, aucun agrandissement ultérieur), débit élevé, netteté jusque dans les textures fines : grain du bitume, rainures des pneus, arêtes de la caisse.

INTERDIT. Coupe, changement de plan, fondu, transition, rotation de caméra, panoramique, zoom, tremblement, accélération, ralentissement, flou de mouvement, filé sur le décor, flou de roue, caractère déformé, lettre inventée, lettre manquante, orthographe modifiée, marquage différent des images de référence, marque redessinée ou stylisée, plaque d'immatriculation, panneau, enseigne, filigrane, deuxième véhicule, voiture, camion, personne, silhouette, chauffeur, animal, fumée, vapeur d'échappement, projection d'eau, poussière, particules, pluie, brouillard, rendu 3D, image de synthèse, aspect jeu vidéo, couleurs saturées, HDR excessif.
```

---

# Plan 2 — Le flanc

**Le plan qui montrera la livrée, donc celui qui doit être le plus propre.**

C'est sur cette surface que le logo sera composé. Elle doit rester plane,
uniformément éclairée, et traverser le cadre à vitesse constante — trois
conditions qui rendent la composition ultérieure exacte plutôt
qu'approximative.

```
IMAGES JOINTES — deux rôles distincts.

La première est L'IMAGE DE DÉPART : le plan commence exactement sur elle et poursuit le mouvement sans le moindre à-coup.

Les autres sont les RÉFÉRENCES DE LA LIVRÉE, à rejoindre à CHAQUE plan sans exception. Elles ne donnent ni le décor, ni le cadrage, ni la lumière : elles servent uniquement à maintenir le marquage identique d'un plan au suivant — même marque, mêmes couleurs, même typographie, même orthographe. Sans elles, le marquage dérive un peu plus à chaque génération et le sixième plan ne ressemble plus au premier.

L'image jointe est la première image de ce plan. Reprends exactement le même camion, la même route, la même lumière, et poursuis le mouvement sans le moindre à-coup.

Un seul plan continu de huit secondes, sans aucune coupe, qui longe le flanc d'une semi-remorque en roulant.

MOUVEMENT. La caméra continue d'accompagner le camion à sa vitesse exacte, à son niveau : le camion reste immobile dans le cadre et le paysage défile derrière lui, de la droite vers la gauche, à vitesse rigoureusement constante. La caméra glisse en outre le long du véhicule, de l'avant vers l'arrière, en translation latérale pure et à vitesse rigoureusement constante : à la première image on est cadré sur la cabine, à la dernière on est parvenu à l'arrière de la remorque, dont les portes fermées occupent la droite du cadre et se rapprochent de l'objectif. Entre les deux, le flanc de la caisse traverse le cadre d'un bord à l'autre, entièrement visible, parfaitement plan et parfaitement net. Aucune rotation, aucun panoramique, aucun zoom, aucun tremblement, aucune variation de vitesse ni de distance.

SUJET. La semi-remorque fourgon du plan précédent, vue de profil, à parois lisses. La caisse porte la LIVRÉE décrite plus bas, conforme aux images de référence : la grande marque circulaire occupe le centre du flanc et le traverse avec lui. Les seuls reliefs sont ceux du véhicule : le bandeau de protection latéral, les trois essieux, les jantes claires, le passage de roue, la barre anti-encastrement. À l'arrière, deux portes battantes fermées, à cadre métallique et charnières apparentes, blanches et lisses elles aussi. Les emplacements de plaque sont LISSES, VIDES ET UNIS. AUCUNE PERSONNE, aucun autre véhicule.

DÉCOR. La même autoroute, le même paysage de collines, la même heure. La glissière défile en bas du cadre. Aucun panneau, aucun bâtiment, aucun texte lisible.

LIVRÉE. Le marquage de Trans Gold, exactement celui des images de référence jointes, sur une caisse blanche. Au centre du flanc, une grande marque circulaire : un globe terrestre bleu et blanc, encerclé par deux arcs épais — l'un bleu montant à gauche, l'autre rouge descendant à droite — prolongés à droite par trois traits obliques en fuite. Devant le globe, la silhouette blanche et grise d'un ensemble routier vu de trois quarts avant. Sous le globe, le mot TRANS GOLD en grandes capitales dorées à ombre portée ; en dessous, le mot MARCHANDISES en capitales grises fines encadrées de deux filets horizontaux ; en dessous encore, la ligne TRANSPORT DE MARCHANDISES & LOGISTIQUE en très petites capitales ; enfin, en bas, la mention DEPUIS 2017 sur deux lignes. L'orthographe est EXACTEMENT celle-ci, lettre pour lettre, sur toutes les images du plan sans exception : TRANS GOLD, MARCHANDISES, TRANSPORT DE MARCHANDISES & LOGISTIQUE, DEPUIS 2017. Aucune lettre ne change de forme, aucune ne disparaît, aucune ne s'ajoute d'une image à l'autre. Une version réduite de la même marque figure sur la portière de la cabine. Le reste de la carrosserie est blanc, lisse et uni.

CAMÉRA. Objectif 50 mm, f/5.6, ISO 400, sur véhicule travelling parfaitement stabilisé, axe strictement horizontal, PERPENDICULAIRE au flanc de la remorque, verticales parfaitement redressées. La distance au flanc ne varie pas d'un bout à l'autre du plan : la caisse conserve exactement la même taille dans le cadre. Nette de bout en bout. Obturateur 1/1000 s : chaque image parfaitement nette, AUCUN FILÉ sur le décor, aucun flou de roue.

LUMIÈRE. Même heure bleue, inchangée. Le flanc blanc est éclairé de façon RIGOUREUSEMENT UNIFORME sur toute sa longueur : pas de dégradé d'un bout à l'autre, pas de reflet mobile qui court sur la tôle, pas d'ombre portée qui traverse. Exposition et balance des blancs VERROUILLÉES du début à la fin.

CADRE. Le sujet essentiel reste dans le TIERS CENTRAL de l'image, en largeur. Sur téléphone, seule une bande verticale centrale du flanc reste visible : la caisse doit donc occuper toute la hauteur utile du cadre, et rien d'important ne doit se trouver aux extrémités gauche et droite.

RENDU. Prise de vue réelle, film publicitaire automobile haut de gamme, qualité commerciale. Colorimétrie neutre et fidèle, blancs tenus et non brûlés, contraste doux. Grain photographique très fin. 30 images par seconde, 8 secondes, format 16:9 horizontal, résolution 3840x2160, 4K NATIVE (réglage de sortie au maximum, aucun agrandissement ultérieur), débit élevé, netteté jusque dans les textures fines : rivets, joints de panneaux, rainures des pneus.

INTERDIT. Coupe, fondu, transition, rotation de caméra, panoramique, zoom, tremblement, variation de distance au flanc, variation de vitesse, flou de mouvement, filé sur le décor, flou de roue, reflet mobile sur la tôle, ombre portée qui traverse la caisse, dégradé de lumière le long du flanc, caractère déformé, lettre inventée, lettre manquante, orthographe modifiée, marquage différent des images de référence, marque redessinée ou stylisée, plaque d'immatriculation, panneau, filigrane, deuxième véhicule, personne, silhouette, animal, fumée, vapeur, projection, poussière, particules, rendu 3D, image de synthèse.
```

---

# Plan 3 — Ce qu'il y a dedans

**Le plan qui parle au directeur logistique.**

Ce n'est pas le camion qui décide d'un contrat de transport, c'est la façon
dont la marchandise est tenue. Sangles, filmage, palettes calées : voilà ce
qu'un donneur d'ordre cherche sur un site de transporteur, et qu'il n'y
trouve jamais.

Le passage se fait sur les portes arrière, et c'est lui qui autorise le
changement d'état : à la fin du plan 2 le camion roule, ici il est à l'arrêt
au quai. Sans cette masse opaque d'une demi-seconde, la transition serait un
saut.

```
L'image jointe est la première image de ce plan. Reprends exactement la même remorque et la même lumière, et poursuis le mouvement sans le moindre à-coup.

Un seul plan continu de huit secondes, sans aucune coupe, qui franchit les portes d'une semi-remorque et découvre son chargement.

MOUVEMENT. Le plan se déroule en trois temps enchaînés, à vitesse rigoureusement constante du début à la fin, sans jamais s'arrêter ni ralentir.

Premier temps, environ une seconde et demie : la caméra continue d'avancer vers les portes arrière fermées, qui se rapprochent et finissent par occuper TOUT le cadre. L'image est alors entièrement remplie par cette tôle blanche mate, dont on voit le grain et les charnières, sans détail net, sans trouée. Elle n'est pas noire : elle est blanche, claire et texturée.

Deuxième temps, environ une seconde : les deux portes s'ouvrent vers l'extérieur, lentement et symétriquement, à vitesse rigoureusement constante, en pivotant sur leurs charnières. Elles dégagent le cadre et découvrent l'intérieur de la remorque. Le camion est désormais à l'arrêt, reculé contre un quai.

Troisième temps, le reste du plan : la caméra pénètre dans la remorque et avance en ligne droite dans l'allée centrale, à hauteur de poitrine, entre les palettes rangées de part et d'autre. À la dernière image elle est parvenue au fond du chargement, face à la cloison avant de la caisse.

Aucune rotation, aucun panoramique, aucun zoom, aucun tremblement. Rien ne bouge en dehors des portes : aucune palette ne glisse, aucune sangle ne vibre.

SUJET. L'intérieur d'une semi-remorque fourgon, parois blanches nervurées, plancher en contreplaqué clair, rails d'arrimage le long des parois. De part et d'autre d'une allée centrale, des palettes de bois portant des charges de hauteurs inégales, entièrement enveloppées de film étirable transparent légèrement bleuté, et maintenues par des sangles à cliquet en tissu bleu tendues sur les rails. Les charges sont neutres et anonymes : aucune étiquette lisible, aucun carton de marque, aucun texte, aucun code, aucun pictogramme, aucune couleur d'entreprise. AUCUNE PERSONNE, aucun cariste, aucun transpalette, aucune main. La caisse est propre et vide de tout autre objet.

CAMÉRA. Objectif 24 mm, f/5.6, ISO 800, sur rail motorisé parfaitement stabilisé, axe strictement horizontal, verticales parfaitement redressées. Nette de bout en bout, des palettes proches à la cloison du fond. Obturateur très rapide, 1/1000 s : chaque image parfaitement nette, sans le moindre flou de bougé, y compris pendant l'ouverture des portes.

LUMIÈRE. Le jour s'est levé pendant le passage sur les portes, et à aucun autre moment. Avant les portes : l'heure bleue du plan précédent, inchangée. Après : la lumière franche d'un matin, entrant par les portes ouvertes derrière la caméra et éclairant le chargement de façon régulière ; le fond de la remorque reste lisible, jamais noir. Une fois à l'intérieur, l'exposition et la balance des blancs sont VERROUILLÉES et ne bougent plus. Aucun éclairage artificiel, aucune diode, aucune lampe.

CADRE. Le sujet essentiel reste dans le TIERS CENTRAL de l'image, en largeur. Sur téléphone, seule l'allée centrale et les premières palettes resteront visibles : c'est là que doit se trouver l'essentiel, et rien d'important ne doit se jouer aux extrémités du cadre.

RENDU. Prise de vue réelle, film industriel haut de gamme, qualité commerciale. Colorimétrie neutre et fidèle, blancs tenus, bois du plancher juste, bleu des sangles non saturé. Grain photographique très fin. 30 images par seconde, 8 secondes, format 16:9 horizontal, résolution 3840x2160, 4K NATIVE (réglage de sortie au maximum, aucun agrandissement ultérieur), débit élevé, netteté jusque dans les textures fines : trame du film étirable, tissage des sangles, veine du bois des palettes.

INTERDIT. Coupe, fondu, fondu au noir, transition ajoutée, rotation de caméra, panoramique, zoom, tremblement, variation de vitesse, arrêt, flou de mouvement, image entièrement noire, porte qui claque, palette qui glisse, sangle qui vibre, texte, chiffre, lettre, code-barres, étiquette lisible, pictogramme, logo, marque, filigrane, carton de marque, personne, cariste, main, transpalette, chariot, animal, poussière en suspension, particules, fumée, rendu 3D, image de synthèse.
```

---

# Plan 4 — L'Europe

**Dire « France et Europe » sans carte et sans drapeau.**

Le plan ressort de la remorque et le monde a changé : la nuit est tombée, le
quai n'est plus le même. C'est le passage qui porte la distance — on n'a
besoin ni d'un panneau, ni d'une frontière, ni d'une carte animée, tous
illisibles et tous des clichés.

```
IMAGES JOINTES — deux rôles distincts.

La première est L'IMAGE DE DÉPART : le plan commence exactement sur elle et poursuit le mouvement sans le moindre à-coup.

Les autres sont les RÉFÉRENCES DE LA LIVRÉE, à rejoindre à CHAQUE plan sans exception. Elles ne donnent ni le décor, ni le cadrage, ni la lumière : elles servent uniquement à maintenir le marquage identique d'un plan au suivant — même marque, mêmes couleurs, même typographie, même orthographe. Sans elles, le marquage dérive un peu plus à chaque génération et le sixième plan ne ressemble plus au premier.

L'image jointe est la première image de ce plan. Reprends exactement la même remorque et le même chargement, et poursuis le mouvement sans le moindre à-coup.

Un seul plan continu de huit secondes, sans aucune coupe, qui ressort d'une semi-remorque sur une plateforme logistique, de nuit.

MOUVEMENT. Le plan se déroule en trois temps enchaînés, à vitesse rigoureusement constante du début à la fin, sans jamais s'arrêter ni ralentir.

Premier temps, environ deux secondes : la caméra RECULE en ligne droite dans l'allée centrale du chargement, des palettes du fond vers les portes ouvertes, à vitesse rigoureusement constante.

Deuxième temps, environ une demi-seconde : le montant vertical d'une des portes ouvertes passe tout près de l'objectif et occupe TOUT le cadre. L'image est entièrement remplie par cette tôle blanche mate. Elle n'est pas noire : elle est claire et texturée.

Troisième temps, le reste du plan : le montant se dégage et découvre une plateforme logistique la nuit. La caméra poursuit son recul, s'éloigne du quai et découvre la façade du bâtiment, ses portes de quai alignées et fermées, et le vaste tablier de béton devant elles. À la dernière image, la caméra est au milieu de la plateforme, face au bâtiment, dont un large pilier de béton se dresse tout près de l'objectif sur la gauche du cadre.

Aucune rotation, aucun panoramique, aucun zoom, aucun tremblement.

SUJET. Une plateforme logistique moderne, la nuit. Bâtiment bas et long en bardage métallique clair, une rangée de portes de quai sectionnelles fermées, numérotées par des chiffres ILLISIBLES ET EFFACÉS — surfaces unies, sans caractère. Bourrelets d'étanchéité noirs au-dessus de chaque porte. Tablier de béton lisse et propre, marquages au sol effacés et unis. Éclairage par mâts en tête de parking, lumière blanche et régulière, halos doux. Au premier plan, l'arrière de la semi-remorque blanche, portes ouvertes, reculée contre un quai. AUCUN AUTRE VÉHICULE, aucune remorque, aucun tracteur, aucun chariot. AUCUNE PERSONNE. Aucune enseigne, aucun panneau, aucun texte, aucun chiffre, aucun logo nulle part.

LIVRÉE. Le marquage de Trans Gold, exactement celui des images de référence jointes, sur une caisse blanche. Au centre du flanc, une grande marque circulaire : un globe terrestre bleu et blanc, encerclé par deux arcs épais — l'un bleu montant à gauche, l'autre rouge descendant à droite — prolongés à droite par trois traits obliques en fuite. Devant le globe, la silhouette blanche et grise d'un ensemble routier vu de trois quarts avant. Sous le globe, le mot TRANS GOLD en grandes capitales dorées à ombre portée ; en dessous, le mot MARCHANDISES en capitales grises fines encadrées de deux filets horizontaux ; en dessous encore, la ligne TRANSPORT DE MARCHANDISES & LOGISTIQUE en très petites capitales ; enfin, en bas, la mention DEPUIS 2017 sur deux lignes. L'orthographe est EXACTEMENT celle-ci, lettre pour lettre, sur toutes les images du plan sans exception : TRANS GOLD, MARCHANDISES, TRANSPORT DE MARCHANDISES & LOGISTIQUE, DEPUIS 2017. Aucune lettre ne change de forme, aucune ne disparaît, aucune ne s'ajoute d'une image à l'autre. Une version réduite de la même marque figure sur la portière de la cabine. Le reste de la carrosserie est blanc, lisse et uni.

CAMÉRA. Objectif 24 mm, f/4, ISO 1600, sur rail motorisé parfaitement stabilisé, axe strictement horizontal, verticales parfaitement redressées. Nette de bout en bout. Obturateur très rapide, 1/1000 s : chaque image parfaitement nette, sans le moindre flou de bougé.

LUMIÈRE. La nuit est tombée PENDANT le passage sur le montant, et à aucun autre moment. Avant : le matin du plan précédent, inchangé. Après : nuit noire, ciel sans étoile, éclairage artificiel des mâts, blanc et rigoureusement constant. La carrosserie blanche prend cette lumière froide. Aucune source qui vacille, aucun gyrophare, aucun phare mobile. Une fois dehors, l'exposition et la balance des blancs sont VERROUILLÉES et ne bougent plus.

CADRE. Le sujet essentiel reste dans le TIERS CENTRAL de l'image, en largeur. Sur téléphone, seule la bande centrale reste visible : l'arrière de la remorque et la façade du quai doivent y tenir.

RENDU. Prise de vue réelle, film industriel haut de gamme, qualité commerciale. Colorimétrie neutre et fidèle, noirs profonds mais lisibles, blancs de la carrosserie tenus sous l'éclairage artificiel. Grain photographique très fin. 30 images par seconde, 8 secondes, format 16:9 horizontal, résolution 3840x2160, 4K NATIVE (réglage de sortie au maximum, aucun agrandissement ultérieur), débit élevé, netteté jusque dans les textures fines : nervures du bardage, grain du béton, joints du tablier.

INTERDIT. Coupe, fondu, fondu au noir, transition ajoutée, rotation de caméra, panoramique, zoom, tremblement, variation de vitesse, flou de mouvement, image entièrement noire, deuxième véhicule, remorque supplémentaire, tracteur, chariot élévateur, personne, silhouette, animal, texte, chiffre, numéro de quai lisible, enseigne, panneau, drapeau, carte, logo, marque, filigrane, gyrophare, phare mobile, source qui vacille, pluie, flaque, reflet mouvant, fumée, vapeur, particules, rendu 3D, image de synthèse.
```

---

# Plan 5 — Le dernier kilomètre

**Le second véhicule entre ici, et le récit devient concret.**

Le semi fait la distance, le porteur fait la porte. C'est la promesse qu'un
transporteur généraliste doit tenir, et la seule façon de la montrer est de
changer de camion — ce que le passage sur le pilier autorise sans coupe.

```
IMAGES JOINTES — deux rôles distincts.

La première est L'IMAGE DE DÉPART : le plan commence exactement sur elle et poursuit le mouvement sans le moindre à-coup.

Les autres sont les RÉFÉRENCES DE LA LIVRÉE, à rejoindre à CHAQUE plan sans exception. Elles ne donnent ni le décor, ni le cadrage, ni la lumière : elles servent uniquement à maintenir le marquage identique d'un plan au suivant — même marque, mêmes couleurs, même typographie, même orthographe. Sans elles, le marquage dérive un peu plus à chaque génération et le sixième plan ne ressemble plus au premier.

L'image jointe est la première image de ce plan. Reprends exactement la même nuit et la même lumière, et poursuis le mouvement sans le moindre à-coup.

Un seul plan continu de huit secondes, sans aucune coupe, qui longe un pilier de béton et découvre un camion porteur à l'arrêt devant un commerce.

MOUVEMENT. Le plan se déroule en trois temps enchaînés, à vitesse rigoureusement constante du début à la fin, sans jamais s'arrêter ni ralentir.

Premier temps, environ deux secondes : la caméra poursuit son mouvement en ligne droite vers le large pilier de béton qui se dresse sur la gauche du cadre, et le longe à quelques centimètres de l'objectif. Le béton envahit progressivement le cadre par la gauche.

Deuxième temps, environ une demi-seconde : le pilier occupe TOUT le cadre. L'image est entièrement remplie par ce béton gris clair et mat, dont on voit le grain et les joints de coffrage, sans détail net, sans trouée. Il n'est pas noir : il est clair et texturé.

Troisième temps, le reste du plan : le pilier se dégage par la droite et découvre une rue de ville au petit matin. La caméra avance et longe un camion porteur à caisse, garé le long du trottoir devant la vitrine d'un commerce. Elle progresse de la cabine vers l'arrière et s'immobilise en douceur face au hayon élévateur, replié en position haute contre les portes. À la dernière image, le hayon occupe le centre du cadre.

Aucune rotation, aucun panoramique, aucun zoom, aucun tremblement.

SUJET. Un camion porteur à caisse fourgon, de gabarit moyen, cabine courte. La caisse porte la LIVRÉE décrite plus bas, conforme aux images de référence, à l'échelle du porteur. Le reste de la carrosserie est blanc et lisse. Les emplacements de plaque sont LISSES, VIDES ET UNIS. À l'arrière, un hayon élévateur en aluminium brossé, replié verticalement contre les portes, et un marchepied. Vitres teintées, rétroviseurs noirs, jantes claires. Feux de position allumés, constants. AUCUNE PERSONNE dans la cabine ni sur le trottoir. AUCUN AUTRE VÉHICULE en circulation ou stationné.

DÉCOR. Une rue de ville européenne au petit matin, immeubles de pierre claire de trois ou quatre étages, trottoir large et propre, bordure en granit. La vitrine d'un commerce fermé, rideau métallique baissé, surface unie sans inscription. Quelques arbres d'alignement aux branches nues. Chaussée en enrobé sombre et propre. Aucune enseigne, aucun panneau, aucun texte, aucun chiffre, aucun logo, aucune affiche, aucune plaque de rue.

LIVRÉE. Le marquage de Trans Gold, exactement celui des images de référence jointes, sur une caisse blanche. Au centre du flanc, une grande marque circulaire : un globe terrestre bleu et blanc, encerclé par deux arcs épais — l'un bleu montant à gauche, l'autre rouge descendant à droite — prolongés à droite par trois traits obliques en fuite. Devant le globe, la silhouette blanche et grise d'un ensemble routier vu de trois quarts avant. Sous le globe, le mot TRANS GOLD en grandes capitales dorées à ombre portée ; en dessous, le mot MARCHANDISES en capitales grises fines encadrées de deux filets horizontaux ; en dessous encore, la ligne TRANSPORT DE MARCHANDISES & LOGISTIQUE en très petites capitales ; enfin, en bas, la mention DEPUIS 2017 sur deux lignes. L'orthographe est EXACTEMENT celle-ci, lettre pour lettre, sur toutes les images du plan sans exception : TRANS GOLD, MARCHANDISES, TRANSPORT DE MARCHANDISES & LOGISTIQUE, DEPUIS 2017. Aucune lettre ne change de forme, aucune ne disparaît, aucune ne s'ajoute d'une image à l'autre. Une version réduite de la même marque figure sur la portière de la cabine. Le reste de la carrosserie est blanc, lisse et uni.

CAMÉRA. Objectif 35 mm, f/5.6, ISO 800, sur rail motorisé parfaitement stabilisé, axe strictement horizontal à un mètre soixante du sol, verticales parfaitement redressées. Nette de bout en bout, y compris le grain du béton du pilier au moment où il frôle l'objectif. Obturateur très rapide, 1/1000 s : chaque image parfaitement nette, sans le moindre flou de bougé.

LUMIÈRE. Le jour s'est levé PENDANT le passage sur le pilier, et à aucun autre moment. Avant : la nuit du plan précédent, inchangée. Après : premier jour, lumière douce et froide, ciel clair sans soleil visible, ombres longues et légères. Aucun lampadaire allumé. Une fois dans la rue, l'exposition et la balance des blancs sont VERROUILLÉES et ne bougent plus.

CADRE. Le sujet essentiel reste dans le TIERS CENTRAL de l'image, en largeur. Sur téléphone, seule la bande centrale reste visible : le camion et le hayon doivent y tenir, la rue et les façades ne sont que du décor.

RENDU. Prise de vue réelle, film publicitaire automobile haut de gamme, qualité commerciale. Colorimétrie neutre et fidèle, blancs de la caisse tenus, pierre des façades juste. Grain photographique très fin. 30 images par seconde, 8 secondes, format 16:9 horizontal, résolution 3840x2160, 4K NATIVE (réglage de sortie au maximum, aucun agrandissement ultérieur), débit élevé, netteté jusque dans les textures fines : grain du béton, brossage du hayon, joints du trottoir.

INTERDIT. Coupe, fondu, fondu au noir, transition ajoutée, rotation de caméra, panoramique, zoom, tremblement, variation de vitesse, flou de mouvement, pilier qui s'écarte tout seul, image entièrement noire, deuxième véhicule, voiture, scooter, vélo, personne, silhouette, chauffeur, passant, animal, oiseau, caractère déformé, lettre inventée, orthographe modifiée, marquage différent des images de référence, plaque de rue, enseigne, affiche, panneau, vitrine éclairée, plaque d'immatriculation, filigrane, fumée, vapeur, poussière, particules, pluie, flaque, rendu 3D, image de synthèse.
```

---

# Plan 6 — La palette

**Ce que le client de Trans Gold achète, ce n'est pas un camion.**

C'est que sa marchandise arrive entière et à l'heure. Le film doit donc finir
sur elle, et non sur le véhicule — c'est la différence entre une publicité de
constructeur et la vitrine d'un transporteur.

Le hayon qui descend est réversible : il remonte quand on remonte. C'est le
dernier mouvement, et le seul du plan.

```
IMAGES JOINTES — deux rôles distincts.

La première est L'IMAGE DE DÉPART : le plan commence exactement sur elle et poursuit le mouvement sans le moindre à-coup.

Les autres sont les RÉFÉRENCES DE LA LIVRÉE, à rejoindre à CHAQUE plan sans exception. Elles ne donnent ni le décor, ni le cadrage, ni la lumière : elles servent uniquement à maintenir le marquage identique d'un plan au suivant — même marque, mêmes couleurs, même typographie, même orthographe. Sans elles, le marquage dérive un peu plus à chaque génération et le sixième plan ne ressemble plus au premier.

L'image jointe est la première image de ce plan. Reprends exactement le même camion, la même rue, la même lumière, et poursuis le mouvement sans le moindre à-coup.

Un seul plan continu de huit secondes, sans aucune coupe, où un hayon élévateur descend et dépose une palette sur le trottoir.

MOUVEMENT. Le plan se déroule en deux temps enchaînés, à vitesse rigoureusement constante du début à la fin, sans jamais s'arrêter ni ralentir.

Premier temps, environ deux secondes : le hayon, replié verticalement contre les portes, bascule vers l'extérieur jusqu'à l'horizontale, à vitesse rigoureusement constante. Une palette filmée s'y trouve DÉJÀ POSÉE, immobile, depuis la première image — elle n'apparaît pas, elle n'est pas chargée, elle est là. Rien ne la pousse, rien ne la retient.

Deuxième temps, environ six secondes : le hayon descend en translation verticale pure, à vitesse rigoureusement constante, du niveau du plancher de la caisse jusqu'au trottoir. Simultanément, la caméra avance très lentement en ligne droite vers la palette et descend en restant strictement horizontale, de sorte qu'à la dernière image elle est cadrée de près sur la palette, à hauteur de sa moitié, le hayon reposant au sol derrière elle. La palette reste rigoureusement immobile sur le plateau pendant toute la descente : elle ne glisse pas, ne bascule pas, ne vibre pas.

Aucune rotation, aucun panoramique, aucun zoom, aucun tremblement.

SUJET. Une palette de bois clair portant une charge d'environ un mètre de haut, entièrement enveloppée de film étirable transparent légèrement bleuté dont on distingue les tours superposés et les plis. La charge est neutre et anonyme : cartons bruns sans impression, aucune étiquette, aucun code, aucun texte, aucun pictogramme, aucune couleur d'entreprise. Sous elle, un hayon élévateur en aluminium brossé, plateau nervuré, bords rabattables. Derrière, l'arrière du camion porteur, caisse blanche portant la LIVRÉE décrite plus bas sur ses portes fermées, conforme aux images de référence, emplacement de plaque LISSE ET VIDE. AUCUNE PERSONNE, aucune main, aucun cariste, aucun transpalette.

DÉCOR. Le trottoir et la rue du plan précédent, inchangés. Bordure en granit, enrobé sombre, façades de pierre claire à l'arrière-plan, hors de mise au point. Aucune enseigne, aucun texte, aucun passant.

LIVRÉE. Le marquage de Trans Gold, exactement celui des images de référence jointes, sur une caisse blanche. Au centre du flanc, une grande marque circulaire : un globe terrestre bleu et blanc, encerclé par deux arcs épais — l'un bleu montant à gauche, l'autre rouge descendant à droite — prolongés à droite par trois traits obliques en fuite. Devant le globe, la silhouette blanche et grise d'un ensemble routier vu de trois quarts avant. Sous le globe, le mot TRANS GOLD en grandes capitales dorées à ombre portée ; en dessous, le mot MARCHANDISES en capitales grises fines encadrées de deux filets horizontaux ; en dessous encore, la ligne TRANSPORT DE MARCHANDISES & LOGISTIQUE en très petites capitales ; enfin, en bas, la mention DEPUIS 2017 sur deux lignes. L'orthographe est EXACTEMENT celle-ci, lettre pour lettre, sur toutes les images du plan sans exception : TRANS GOLD, MARCHANDISES, TRANSPORT DE MARCHANDISES & LOGISTIQUE, DEPUIS 2017. Aucune lettre ne change de forme, aucune ne disparaît, aucune ne s'ajoute d'une image à l'autre. Une version réduite de la même marque figure sur la portière de la cabine. Le reste de la carrosserie est blanc, lisse et uni.

CAMÉRA. Objectif 50 mm, f/4, ISO 800, sur rail motorisé parfaitement stabilisé, axe strictement horizontal du début à la fin, verticales parfaitement redressées. Nette sur la palette de bout en bout. Obturateur très rapide, 1/1000 s : chaque image parfaitement nette, y compris pendant la descente du hayon, sans le moindre flou de bougé.

LUMIÈRE. Exactement celle du plan précédent, inchangée : premier jour, lumière douce et froide, ombres longues et légères. Le film étirable accroche cette lumière en reflets doux et FIXES : aucun reflet ne court sur la surface pendant la descente. Exposition et balance des blancs VERROUILLÉES du début à la fin.

CADRE. Le sujet essentiel reste dans le TIERS CENTRAL de l'image, en largeur. Sur téléphone, seule la bande centrale reste visible : la palette doit y tenir entièrement à la dernière image.

RENDU. Prise de vue réelle, film industriel haut de gamme, qualité commerciale. Colorimétrie neutre et fidèle, brun des cartons juste et non saturé, blancs de la caisse tenus. Grain photographique très fin. 30 images par seconde, 8 secondes, format 16:9 horizontal, résolution 3840x2160, 4K NATIVE (réglage de sortie au maximum, aucun agrandissement ultérieur), débit élevé, netteté jusque dans les textures fines : trame et plis du film étirable, cannelure des cartons, veine du bois de la palette, nervures du plateau.

INTERDIT. Coupe, fondu, transition ajoutée, rotation de caméra, panoramique, zoom, tremblement, variation de vitesse, arrêt, flou de mouvement, palette qui apparaît, qui est chargée ou qui entre dans le champ, palette qui glisse, bascule ou vibre, hayon qui claque, reflet qui court sur le film étirable, variation d'exposition, personne, main, cariste, transpalette, chariot, animal, caractère déformé, lettre inventée, orthographe modifiée, marquage différent des images de référence, code-barres, étiquette, pictogramme, impression sur carton, filigrane, fumée, vapeur, poussière, particules, rendu 3D, image de synthèse.
```

---

# Après la génération

**Extraction.** `film_video.py` découpe les six plans en 1 440 images, format
16:9, 4K native. Aucun agrandisseur dans la chaîne.

**Composition du logo.** Les surfaces qui le portent sont planes et se
déplacent à vitesse constante — le flanc au plan 2, les portes au plan 3, la
caisse au plan 5. Le logo vectoriel y est posé par transformation
géométrique, image par image. C'est cette étape qui rend le nom du client
net et correctement orthographié, ce qu'aucun modèle ne garantira.

**Le contact, déjà connu :** +33 6 60 92 66 46. Il vit dans le HTML du site,
en lien `tel:` cliquable, et **jamais dans une image générée** — un numéro
dessiné par un modèle serait faux, et un numéro faux sur un site de
transporteur coûte des appels perdus.

**Ce qu'il faut obtenir du client avant cette étape :**

  1. le logo en **vectoriel** — `.svg`, `.ai`, `.eps` ou `.pdf` ;
  2. la **licence de transport**, le SIRET, les assurances, les
     certifications éventuelles ;
  3. la **zone réellement couverte** — « Europe » est vague, et un donneur
     d'ordre veut lire des pays ;
  4. la **taille de la flotte**, si un jour on veut l'écrire. Le film, lui,
     ne montre jamais qu'un camion à la fois : rien à ajuster de ce côté.
